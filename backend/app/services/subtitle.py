"""Subtitle extraction: platform CDN/API URLs first, yt-dlp download fallback."""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import re
import tempfile
import time
from urllib.parse import urlencode
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
from html import unescape
from urllib.parse import urlparse

_BVID_RE = re.compile(r"BV[\w]+", re.I)

import httpx
from yt_dlp import YoutubeDL

from app.core.config import settings
from app.schemas.subtitle import SubtitleSegment, SubtitleSource, SubtitlesResponse

_executor = ThreadPoolExecutor(max_workers=3)

LANG_PRIORITY = ["zh-Hans", "zh-CN", "zh-Hant", "zh", "en", "ja", "ko", "auto"]
EXT_PRIORITY = ["vtt", "srv3", "srv2", "srv1", "json3", "ttml", "srt"]
DISPLAY_MAX_CHARS = 20_000
AI_MAX_CHARS = 8_000

_TAG_RE = re.compile(r"<[^>]+>")
_VTT_TS = re.compile(
    r"(?P<start>\d{1,2}:)?\d{1,2}:\d{2}[.,]\d{3}\s*-->\s*"
    r"(?:(?P<end_h>\d{1,2}):)?(?P<end_m>\d{1,2}):(?P<end_s>\d{2})[.,](?P<end_ms>\d{3})"
)


@dataclass
class SubtitleBundle:
    source: SubtitleSource
    language: str | None = None
    segments: list[SubtitleSegment] = field(default_factory=list)
    plain_text: str = ""
    char_count: int = 0
    truncated: bool = False
    has_timestamps: bool = True
    extraction_method: str | None = None
    hint: str | None = None

    def to_response(self) -> SubtitlesResponse:
        return SubtitlesResponse(
            source=self.source,
            language=self.language,
            segments=self.segments,
            plain_text=self.plain_text,
            char_count=self.char_count,
            truncated=self.truncated,
            has_timestamps=self.has_timestamps,
            extraction_method=self.extraction_method,
            hint=self.hint,
        )

    def to_cache(self) -> dict:
        return asdict(self)


def _bundle_from_cache(data: dict) -> SubtitleBundle:
    segs = [SubtitleSegment(**s) for s in data.get("segments", [])]
    return SubtitleBundle(
        source=data["source"],
        language=data.get("language"),
        segments=segs,
        plain_text=data.get("plain_text", ""),
        char_count=data.get("char_count", 0),
        truncated=data.get("truncated", False),
        has_timestamps=data.get("has_timestamps", True),
        extraction_method=data.get("extraction_method"),
        hint=data.get("hint"),
    )


def _extract_bvid(url_or_id: str) -> str | None:
    if not url_or_id:
        return None
    m = _BVID_RE.search(url_or_id)
    return m.group(0) if m else None


def _is_bilibili(info: dict, url: str) -> bool:
    extractor = (info.get("extractor") or info.get("extractor_key") or "").lower()
    host = urlparse(info.get("webpage_url") or url).netloc.lower()
    return "bilibili" in extractor or "bilibili" in host


_WBI_MIXIN_TAB = [
    46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35, 27, 43, 5, 49,
    33, 9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13, 37, 48, 7, 16, 24, 55, 40,
    61, 26, 17, 0, 1, 60, 51, 30, 4, 22, 25, 54, 21, 56, 59, 6, 63, 57, 62, 11,
    36, 20, 34, 44, 52,
]


def _bilibili_api_headers() -> dict[str, str]:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Referer": "https://www.bilibili.com/",
        "Origin": "https://www.bilibili.com",
    }
    if settings.BILIBILI_SESSDATA:
        headers["Cookie"] = f"SESSDATA={settings.BILIBILI_SESSDATA}"
    return headers


def _get_wbi_mixin_key(client: httpx.Client) -> str | None:
    try:
        resp = client.get(
            "https://api.bilibili.com/x/web-interface/nav",
            headers=_bilibili_api_headers(),
        )
        resp.raise_for_status()
        wbi = (resp.json().get("data") or {}).get("wbi_img") or {}
        img_key = (wbi.get("img_url") or "").rsplit("/", 1)[-1].split(".")[0]
        sub_key = (wbi.get("sub_url") or "").rsplit("/", 1)[-1].split(".")[0]
        lookup = img_key + sub_key
        if len(lookup) < 64:
            return None
        return "".join(lookup[i] for i in _WBI_MIXIN_TAB)[:32]
    except Exception:
        return None


def _sign_wbi_params(params: dict, mixin_key: str) -> dict:
    signed = dict(params)
    signed["wts"] = round(time.time())
    filtered = {
        k: "".join(c for c in str(v) if c not in "!'()*")
        for k, v in sorted(signed.items())
    }
    query = urlencode(filtered)
    filtered["w_rid"] = hashlib.md5(f"{query}{mixin_key}".encode()).hexdigest()
    return filtered


def _bilibili_player_subtitles(bvid: str) -> tuple[list[dict], str | None, bool]:
    """Query Bilibili wbi player API. Returns (tracks, cid, need_login_subtitle)."""
    headers = _bilibili_api_headers()
    try:
        with httpx.Client(timeout=20, follow_redirects=True) as client:
            view = client.get(
                "https://api.bilibili.com/x/web-interface/view",
                params={"bvid": bvid},
                headers=headers,
            )
            view.raise_for_status()
            data = view.json().get("data") or {}
            pages = data.get("pages") or []
            if not pages:
                return [], None, False
            cid = pages[0].get("cid")
            aid = data.get("aid")
            if not cid:
                return [], None, False

            params: dict = {"bvid": bvid, "cid": cid}
            if aid:
                params["aid"] = aid
            mixin_key = _get_wbi_mixin_key(client)
            if mixin_key:
                params = _sign_wbi_params(params, mixin_key)

            player = client.get(
                "https://api.bilibili.com/x/player/wbi/v2",
                params=params,
                headers=headers,
            )
            player.raise_for_status()
            pdata = player.json().get("data") or {}
            subtitle = pdata.get("subtitle") or {}
            need_login = bool(pdata.get("need_login_subtitle"))
            return subtitle.get("subtitles") or [], str(cid), need_login
    except Exception:
        return [], None, False


def _pick_bilibili_track(tracks: list[dict]) -> dict | None:
    if not tracks:
        return None
    priority = [
        "ai-zh", "中文", "简体", "zh", "zh-cn", "zh-hans",
        "中文（自动生成）", "中文（简体）", "英文", "en",
    ]
    for pref in priority:
        pl = pref.lower()
        for track in tracks:
            doc = (track.get("lan_doc") or "").lower()
            code = (track.get("lan") or "").lower()
            if pl in doc or pl in code or doc.startswith(pl):
                return track
    return tracks[0]


def _parse_bilibili_json(content: str) -> list[SubtitleSegment]:
    data = json.loads(content)
    segments: list[SubtitleSegment] = []
    for item in data.get("body") or []:
        text = _clean_text(str(item.get("content", "")))
        if not text:
            continue
        start = float(item.get("from", 0))
        end = float(item.get("to", start + 1))
        segments.append(SubtitleSegment(start=start, end=end, text=text))
    return segments


def _fetch_bilibili_platform_subtitles(info: dict, page_url: str) -> SubtitleBundle | None:
    """Bilibili: player v2 API + subtitle JSON URL (before yt-dlp)."""
    bvid = _extract_bvid(info.get("id") or "") or _extract_bvid(page_url)
    if not bvid:
        return None

    tracks, _cid, need_login = _bilibili_player_subtitles(bvid)
    track = _pick_bilibili_track(tracks)
    if not track:
        return None

    sub_url = track.get("subtitle_url_v2") or track.get("subtitle_url") or ""
    if sub_url.startswith("//"):
        sub_url = "https:" + sub_url
    if not sub_url:
        return None

    language = track.get("lan_doc") or track.get("lan")
    headers = _bilibili_api_headers()
    try:
        with httpx.Client(timeout=30, follow_redirects=True) as client:
            resp = client.get(sub_url, headers=headers)
            resp.raise_for_status()
            segments = _parse_bilibili_json(resp.text)
    except Exception:
        return None

    if not segments:
        return None
    return _build_bundle(segments, "auto_subtitle", language, "bilibili_api")


def subtitle_meta_from_info(info: dict, url: str = "") -> tuple[bool, list[str] | None]:
    manual = info.get("subtitles") or {}
    auto = info.get("automatic_captions") or {}
    langs: list[str] = []
    seen: set[str] = set()
    for pool in (manual, auto):
        for lang in pool:
            if lang not in seen:
                seen.add(lang)
                langs.append(lang)
    if langs:
        return True, langs[:5]

    if _is_bilibili(info, url):
        bvid = _extract_bvid(info.get("id") or "") or _extract_bvid(url)
        if bvid:
            tracks, _, _ = _bilibili_player_subtitles(bvid)
            if tracks:
                api_langs = []
                for t in tracks[:5]:
                    label = t.get("lan_doc") or t.get("lan")
                    if label and label not in api_langs:
                        api_langs.append(label)
                return True, api_langs or None

    return False, None


def _clean_text(text: str) -> str:
    text = unescape(_TAG_RE.sub("", text))
    return re.sub(r"\s+", " ", text).strip()


def _parse_timestamp(ts: str) -> float:
    ts = ts.strip().replace(",", ".")
    parts = ts.split(":")
    if len(parts) == 3:
        h, m, s = parts
        return int(h) * 3600 + int(m) * 60 + float(s)
    if len(parts) == 2:
        m, s = parts
        return int(m) * 60 + float(s)
    return float(ts)


def _parse_vtt(content: str) -> list[SubtitleSegment]:
    segments: list[SubtitleSegment] = []
    blocks = re.split(r"\n\s*\n", content.replace("\r\n", "\n"))
    for block in blocks:
        lines = [ln.strip() for ln in block.split("\n") if ln.strip()]
        if not lines:
            continue
        ts_line = next((ln for ln in lines if "-->" in ln), None)
        if not ts_line:
            continue
        m = _VTT_TS.search(ts_line)
        if not m:
            continue
        start_part, _, end_part = ts_line.partition("-->")
        start = _parse_timestamp(start_part.strip())
        end = _parse_timestamp(end_part.strip())
        text_lines = [ln for ln in lines if "-->" not in ln and not ln.isdigit() and not ln.startswith("WEBVTT")]
        text = _clean_text(" ".join(text_lines))
        if text:
            segments.append(SubtitleSegment(start=start, end=end, text=text))
    return segments


def _parse_srt(content: str) -> list[SubtitleSegment]:
    content = content.replace("\r\n", "\n")
    pattern = re.compile(
        r"\d+\s*\n"
        r"(\d{1,2}:\d{2}:\d{2}[,.]\d{3})\s*-->\s*(\d{1,2}:\d{2}:\d{2}[,.]\d{3})\s*\n"
        r"((?:.+\n?)+?)(?=\n\d+\s*\n|\Z)",
        re.MULTILINE,
    )
    segments: list[SubtitleSegment] = []
    for m in pattern.finditer(content + "\n"):
        text = _clean_text(m.group(3).replace("\n", " "))
        if text:
            segments.append(
                SubtitleSegment(
                    start=_parse_timestamp(m.group(1)),
                    end=_parse_timestamp(m.group(2)),
                    text=text,
                )
            )
    return segments


def _parse_json3(content: str) -> list[SubtitleSegment]:
    data = json.loads(content)
    segments: list[SubtitleSegment] = []
    for ev in data.get("events", []):
        if "segs" not in ev:
            continue
        text = _clean_text("".join(seg.get("utf8", "") for seg in ev["segs"]))
        if not text or text == "\n":
            continue
        start_ms = ev.get("tStartMs", 0)
        dur_ms = ev.get("dDurationMs", 0)
        segments.append(
            SubtitleSegment(
                start=start_ms / 1000.0,
                end=(start_ms + dur_ms) / 1000.0,
                text=text,
            )
        )
    return segments


def _parse_subtitle_content(content: str, ext: str) -> list[SubtitleSegment]:
    ext = (ext or "").lower()
    if ext == "json3" or content.lstrip().startswith("{"):
        try:
            return _parse_json3(content)
        except (json.JSONDecodeError, KeyError):
            pass
    if ext == "srt" or re.search(r"\d+\s*\n\d{1,2}:\d{2}:\d{2}", content[:500]):
        segs = _parse_srt(content)
        if segs:
            return segs
    return _parse_vtt(content)


def _match_language(available: list[str]) -> str | None:
    if not available:
        return None
    lower_index = {k.lower(): k for k in available}
    for pref in LANG_PRIORITY:
        pl = pref.lower()
        for key in available:
            kl = key.lower()
            if kl == pl or kl.startswith(pl) or pl.startswith(kl):
                return key
    return available[0]


def _pick_format_entry(entries: list[dict]) -> dict | None:
    if not entries:
        return None
    by_ext: dict[str, dict] = {}
    for e in entries:
        ext = (e.get("ext") or "").lower()
        if ext:
            by_ext[ext] = e
    for ext in EXT_PRIORITY:
        if ext in by_ext:
            return by_ext[ext]
    return entries[0]


def _pick_subtitle_url(info: dict) -> tuple[str, str, str, bool] | None:
    """Return (url, language, ext, is_manual) from extract_info metadata."""
    manual: dict = info.get("subtitles") or {}
    auto: dict = info.get("automatic_captions") or {}

    for pool, is_manual in ((manual, True), (auto, False)):
        if not pool:
            continue
        lang = _match_language(list(pool.keys()))
        if not lang:
            continue
        entry = _pick_format_entry(pool[lang])
        if entry and entry.get("url"):
            return entry["url"], lang, entry.get("ext", "vtt"), is_manual
    return None


def _request_headers(info: dict, url: str) -> dict[str, str]:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
    }
    extractor = (info.get("extractor") or info.get("extractor_key") or "").lower()
    page_url = info.get("webpage_url") or url
    host = urlparse(page_url).netloc.lower()

    if "bilibili" in extractor or "bilibili" in host:
        headers["Referer"] = "https://www.bilibili.com/"
    elif "youtube" in extractor or "youtu" in host:
        headers["Referer"] = "https://www.youtube.com/"
    return headers


def _fetch_platform_subtitles(info: dict, page_url: str) -> SubtitleBundle | None:
    """Fetch subtitle via platform CDN URLs from extract_info (no yt-dlp re-extract)."""
    picked = _pick_subtitle_url(info)
    if not picked:
        return None

    sub_url, language, ext, is_manual = picked
    headers = _request_headers(info, page_url)

    try:
        with httpx.Client(follow_redirects=True, timeout=30) as client:
            resp = client.get(sub_url, headers=headers)
            resp.raise_for_status()
            content = resp.text
    except Exception:
        return None

    segments = _parse_subtitle_content(content, ext)
    if not segments:
        return None

    source: SubtitleSource = "manual_subtitle" if is_manual else "auto_subtitle"
    return _build_bundle(segments, source, language, "platform_api")


def _fetch_via_ytdlp(url: str, info: dict) -> SubtitleBundle | None:
    from app.services.download import _base_ydl_opts

    subs_dir = tempfile.mkdtemp(prefix="saveany-subs-")
    ydl_opts = {
        **_base_ydl_opts(),
        "writesubtitles": True,
        "writeautomaticsub": True,
        "writeautosub": True,
        "subtitleslangs": LANG_PRIORITY,
        "subtitlesformat": "vtt/srt/best",
        "outtmpl": os.path.join(subs_dir, "%(id)s.%(ext)s"),
        "skip_download": True,
    }
    if settings.BILIBILI_SESSDATA and _is_bilibili(info, url):
        ydl_opts.setdefault("http_headers", {})
        cookie = f"SESSDATA={settings.BILIBILI_SESSDATA}"
        ydl_opts["http_headers"]["Cookie"] = (
            f"{ydl_opts['http_headers'].get('Cookie', '')}; {cookie}".strip("; ")
        )

    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.extract_info(url, download=False)

        best_path = None
        best_lang = None
        for root, _, files in os.walk(subs_dir):
            for fname in sorted(files):
                if not fname.endswith((".vtt", ".srt")):
                    continue
                fpath = os.path.join(root, fname)
                for pref in LANG_PRIORITY:
                    if pref.lower() in fname.lower():
                        best_path = fpath
                        best_lang = pref
                        break
                if best_path is None:
                    best_path = fpath
                    best_lang = "unknown"

        if not best_path:
            return None

        with open(best_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        ext = os.path.splitext(best_path)[1].lstrip(".")
        segments = _parse_subtitle_content(content, ext)
        if not segments:
            return None

        is_manual = ".sub" in os.path.basename(best_path) or "manual" in best_path.lower()
        source: SubtitleSource = "manual_subtitle" if is_manual else "auto_subtitle"
        return _build_bundle(segments, source, best_lang, "ytdlp")
    except Exception:
        return None
    finally:
        for root, _, files in os.walk(subs_dir):
            for fname in files:
                try:
                    os.remove(os.path.join(root, fname))
                except OSError:
                    pass
        try:
            os.rmdir(subs_dir)
        except OSError:
            pass


def _build_bundle(
    segments: list[SubtitleSegment],
    source: SubtitleSource,
    language: str | None,
    method: str,
) -> SubtitleBundle:
    lines: list[str] = []
    kept: list[SubtitleSegment] = []
    truncated = False
    total = 0
    for seg in segments:
        line = f"{_format_time(seg.start)}  {seg.text}"
        if total + len(line) + 1 > DISPLAY_MAX_CHARS:
            truncated = True
            break
        lines.append(line)
        kept.append(seg)
        total += len(line) + 1

    plain_text = "\n".join(lines)
    return SubtitleBundle(
        source=source,
        language=language,
        segments=kept,
        plain_text=plain_text,
        char_count=len(plain_text),
        truncated=truncated,
        has_timestamps=True,
        extraction_method=method,
    )


def _format_time(seconds: float) -> str:
    total = int(seconds)
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def _empty_bundle(info: dict, url: str) -> SubtitleBundle:
    hint = None
    if _is_bilibili(info, url):
        _, _, need_login = _bilibili_player_subtitles(
            _extract_bvid(info.get("id") or "") or _extract_bvid(url) or "",
        )
        if need_login and not settings.BILIBILI_SESSDATA:
            hint = (
                "Bilibili timed subtitles require login. "
                "Set BILIBILI_SESSDATA in backend .env (browser cookie after login)."
            )
        elif need_login:
            hint = "Bilibili subtitles need a valid BILIBILI_SESSDATA cookie. Please refresh it."
    return SubtitleBundle(source="none", has_timestamps=False, extraction_method=None, hint=hint)


def _extract_subtitles_sync(task_info: dict) -> SubtitleBundle:
    url = task_info["url"]
    info = task_info.get("info", {})

    if _is_bilibili(info, url):
        bundle = _fetch_bilibili_platform_subtitles(info, url)
        if bundle and bundle.segments:
            return bundle

    bundle = _fetch_platform_subtitles(info, url)
    if bundle and bundle.segments:
        return bundle

    bundle = _fetch_via_ytdlp(url, info)
    if bundle and bundle.segments:
        return bundle

    return _empty_bundle(info, url)


def flatten_for_ai(bundle: SubtitleBundle) -> str:
    if bundle.source == "none" or bundle.source == "description":
        return ""
    if bundle.segments:
        text = " ".join(s.text for s in bundle.segments)
    else:
        text = bundle.plain_text.replace("\n", " ")
    return text[:AI_MAX_CHARS]


def metadata_fallback_for_ai(info: dict) -> str:
    """When no timed subtitles exist, use title/description for AI (legacy behavior)."""
    parts: list[str] = []
    title = (info.get("title") or "").strip()
    if title:
        parts.append(f"Title: {title}")
    desc = (info.get("description") or "").strip()
    if desc and desc != "-":
        parts.append(f"Description:\n{desc[:6000]}")
    channel = info.get("channel") or info.get("uploader")
    if channel:
        parts.append(f"Channel: {channel}")
    tags = info.get("tags")
    if tags and isinstance(tags, list):
        parts.append("Tags: " + ", ".join(str(t) for t in tags[:20]))
    return "\n\n".join(parts)[:AI_MAX_CHARS]


def text_for_ai(bundle: SubtitleBundle, info: dict) -> str:
    text = flatten_for_ai(bundle)
    if text.strip():
        return text
    return metadata_fallback_for_ai(info)


async def get_or_extract_subtitles(
    task_id: str,
    task_info: dict,
    *,
    refresh_if_empty: bool = False,
) -> SubtitleBundle:
    cached = task_info.get("subtitles_bundle")
    if cached:
        bundle = _bundle_from_cache(cached)
        if not refresh_if_empty or bundle.source not in ("none", "description"):
            return bundle
        task_info.pop("subtitles_bundle", None)

    loop = asyncio.get_event_loop()
    bundle = await loop.run_in_executor(_executor, _extract_subtitles_sync, task_info)
    # Do not cache empty results so AI / retry can run extraction again.
    if bundle.source not in ("none", "description"):
        task_info["subtitles_bundle"] = bundle.to_cache()
    return bundle


async def fetch_subtitles_for_task(task_id: str) -> SubtitlesResponse:
    from app.services.download import get_task

    task = get_task(task_id)
    if not task:
        raise ValueError("Task not found or expired")
    bundle = await get_or_extract_subtitles(task_id, task)
    return bundle.to_response()
