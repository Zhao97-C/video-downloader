import asyncio
import hashlib
import os
import re
import shutil
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor

import httpx
from yt_dlp import YoutubeDL

from app.core.config import settings
from app.schemas.video import FormatInfo, ParseResponse

_executor = ThreadPoolExecutor(max_workers=settings.MAX_CONCURRENT_DOWNLOADS)
_semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_DOWNLOADS)

# In-memory task store (replace with Redis in production)
_tasks: dict[str, dict] = {}


def _generate_task_id(url: str) -> str:
    return hashlib.md5(f"{url}{time.time()}".encode()).hexdigest()[:12]


def _format_priority(f: dict) -> int:
    """Prefer muxed (video+audio) over video-only / audio-only."""
    v = f.get("vcodec") or "none"
    a = f.get("acodec") or "none"
    if v != "none" and a != "none":
        return 3
    if v != "none":
        return 2
    if a != "none":
        return 1
    return 0


def _needs_audio_merge(fmt: dict) -> bool:
    vcodec = fmt.get("vcodec") or "none"
    acodec = fmt.get("acodec") or "none"
    return vcodec != "none" and acodec == "none"


def _ydlp_format_selector(format_id: str, fmt: dict) -> str:
    """Bilibili/YouTube often split video & audio; merge when needed."""
    if _needs_audio_merge(fmt):
        height = fmt.get("height") or 0
        if height > 0:
            return (
                f"bestvideo[height<={height}][ext=mp4]+bestaudio[ext=m4a]/"
                f"bestvideo[height<={height}]+bestaudio/best"
            )
        return f"{format_id}+bestaudio/best"
    return format_id


def _file_has_audio(path: str) -> bool:
    ffmpeg = _resolve_ffmpeg_location()
    if not ffmpeg:
        return True
    try:
        result = subprocess.run(
            [ffmpeg, "-hide_banner", "-i", path],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
            check=False,
        )
        return "Audio:" in (result.stderr or "")
    except Exception:
        return True


def _resolve_ffmpeg_location() -> str | None:
    """Return path to ffmpeg binary (yt-dlp needs the executable, not a directory)."""
    if path := shutil.which("ffmpeg"):
        return path
    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


def _ensure_ffmpeg_for_merge(fmt: dict) -> None:
    if not _needs_audio_merge(fmt):
        return
    if _resolve_ffmpeg_location():
        return
    raise ValueError(
        "需要 FFmpeg 合并视频与音频。请运行: pip install -r requirements.txt 后重启后端，"
        "或安装系统 FFmpeg 并加入 PATH。"
    )


def _base_ydl_opts() -> dict:
    opts: dict = {"quiet": True, "no_warnings": True}
    if ffmpeg := _resolve_ffmpeg_location():
        opts["ffmpeg_location"] = ffmpeg
    return opts


def _extract_info_sync(url: str) -> dict:
    ydl_opts = {**_base_ydl_opts(), "extract_flat": False}
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return ydl.sanitize_info(info)


async def extract_video_info(url: str) -> dict:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_executor, _extract_info_sync, url)


def _build_formats(info: dict, max_resolution: int = 9999) -> list[FormatInfo]:
    formats = []
    best_by_key: dict[str, dict] = {}
    raw_formats = info.get("formats") or []

    for f in raw_formats:
        height = f.get("height") or 0
        ext = f.get("ext", "mp4")
        vcodec = f.get("vcodec", "none")
        acodec = f.get("acodec", "none")

        if vcodec == "none" and acodec == "none":
            continue

        if vcodec != "none" and height > 0:
            label = f"{height}p"
        elif acodec != "none" and vcodec == "none":
            label = "audio"
        else:
            label = ext

        key = f"{label}_{ext}"
        prev = best_by_key.get(key)
        if prev is None or _format_priority(f) > _format_priority(prev):
            best_by_key[key] = f

    for f in best_by_key.values():
        height = f.get("height") or 0
        ext = f.get("ext", "mp4")
        vcodec = f.get("vcodec", "none")
        acodec = f.get("acodec", "none")

        if vcodec != "none" and height > 0:
            label = f"{height}p"
        elif acodec != "none" and vcodec == "none":
            label = "audio"
        else:
            label = ext

        is_pro = height > settings.FREE_MAX_RESOLUTION
        resolution = f"{height}p" if height > 0 else None

        formats.append(FormatInfo(
            format_id=f.get("format_id", ""),
            ext=ext,
            resolution=resolution,
            filesize=f.get("filesize") or f.get("filesize_approx"),
            vcodec=vcodec if vcodec != "none" else None,
            acodec=acodec if acodec != "none" else None,
            quality_label=label,
            is_pro=is_pro,
        ))

    formats.sort(key=lambda x: int(x.resolution.replace("p", "")) if x.resolution else 0, reverse=True)
    return formats


async def parse_video(url: str, mode: str = "auto") -> ParseResponse:
    info = await extract_video_info(url)

    task_id = _generate_task_id(url)
    _tasks[task_id] = {"info": info, "url": url, "created_at": time.time()}

    formats = _build_formats(info)

    if mode == "audio":
        formats = [f for f in formats if f.quality_label == "audio"]

    raw_duration = info.get("duration")
    duration = int(raw_duration) if raw_duration is not None else None

    return ParseResponse(
        title=info.get("title", "Unknown"),
        thumbnail=info.get("thumbnail"),
        duration=duration,
        platform=info.get("extractor", "").split(":")[0] if info.get("extractor") else None,
        formats=formats,
        task_id=task_id,
    )


async def check_direct_link(url: str) -> bool:
    """Check if a direct URL is accessible without referer/cookies."""
    try:
        async with httpx.AsyncClient(follow_redirects=False, timeout=10) as client:
            resp = await client.head(url)
            return resp.status_code in (200, 206)
    except Exception:
        return False


def _cleanup_partial_downloads(task_id: str) -> None:
    if not os.path.isdir(settings.DOWNLOAD_DIR):
        return
    partial = re.compile(rf"^{re.escape(task_id)}.*\.f\d+\.")
    for name in os.listdir(settings.DOWNLOAD_DIR):
        if partial.match(name):
            try:
                os.remove(os.path.join(settings.DOWNLOAD_DIR, name))
            except OSError:
                pass


def _download_file_sync(url: str, ydl_format: str, task_id: str, require_audio: bool) -> str:
    os.makedirs(settings.DOWNLOAD_DIR, exist_ok=True)
    _cleanup_partial_downloads(task_id)
    outtmpl = os.path.join(settings.DOWNLOAD_DIR, f"{task_id}.%(ext)s")
    ydl_opts = {
        **_base_ydl_opts(),
        "format": ydl_format,
        "merge_output_format": "mp4",
        "outtmpl": outtmpl,
    }
    if not ydl_opts.get("ffmpeg_location") and "+" in ydl_format:
        raise RuntimeError(
            "FFmpeg not found. Run: pip install -r requirements.txt then restart the backend."
        )

    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    expected = os.path.join(settings.DOWNLOAD_DIR, f"{task_id}.mp4")
    if os.path.isfile(expected):
        output = expected
    else:
        output = None
        for name in os.listdir(settings.DOWNLOAD_DIR):
            if not name.startswith(task_id + "."):
                continue
            if ".f" in name.split(task_id + ".", 1)[-1]:
                continue
            path = os.path.join(settings.DOWNLOAD_DIR, name)
            if os.path.isfile(path):
                output = path
                break
        if not output:
            _cleanup_partial_downloads(task_id)
            raise FileNotFoundError("Download finished but merged output file was not found")

    if require_audio and not _file_has_audio(output):
        try:
            os.remove(output)
        except OSError:
            pass
        _cleanup_partial_downloads(task_id)
        raise RuntimeError(
            "Downloaded file has no audio track. Ensure FFmpeg is available and try parsing the URL again."
        )

    return output


async def download_video(task_id: str, format_id: str) -> dict:
    """Returns download strategy info."""
    task = _tasks.get(task_id)
    if not task:
        raise ValueError("Task not found or expired")

    info = task["info"]
    url = task["url"]

    target_format = None
    for f in info.get("formats", []):
        if f.get("format_id") == format_id:
            target_format = f
            break

    if not target_format:
        raise ValueError("Format not found")

    _ensure_ffmpeg_for_merge(target_format)

    filesize = target_format.get("filesize") or target_format.get("filesize_approx") or 0
    ydl_format = _ydlp_format_selector(format_id, target_format)
    needs_merge = _needs_audio_merge(target_format)

    # Never redirect: CDN URLs are often video-only even when metadata lists an audio codec.
    if filesize > settings.LARGE_FILE_THRESHOLD and not needs_merge:
        return {"mode": "stream", "url": url, "ydl_format": ydl_format}

    ext = "mp4" if needs_merge else target_format.get("ext", "mp4")

    async with _semaphore:
        loop = asyncio.get_event_loop()
        output_path = await loop.run_in_executor(
            _executor,
            _download_file_sync,
            url,
            ydl_format,
            task_id,
            needs_merge,
        )

    return {"mode": "proxy", "file_path": output_path, "filename": f"{info.get('title', 'video')}.{ext}"}


def get_task(task_id: str) -> dict | None:
    return _tasks.get(task_id)


def cleanup_expired_tasks():
    """Remove expired tasks and temp files."""
    now = time.time()
    expired = [k for k, v in _tasks.items() if now - v["created_at"] > settings.TEMP_FILE_EXPIRY_MINUTES * 60]
    for k in expired:
        task = _tasks.pop(k, None)
        if task:
            for ext in ("mp4", "webm", "mkv", "m4a", "mp3"):
                path = os.path.join(settings.DOWNLOAD_DIR, f"{k}.{ext}")
                if os.path.exists(path):
                    os.remove(path)
