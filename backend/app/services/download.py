import asyncio
import hashlib
import os
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


def _extract_info_sync(url: str) -> dict:
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
    }
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return ydl.sanitize_info(info)


async def extract_video_info(url: str) -> dict:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_executor, _extract_info_sync, url)


def _build_formats(info: dict, max_resolution: int = 9999) -> list[FormatInfo]:
    formats = []
    seen = set()
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
        if key in seen:
            continue
        seen.add(key)

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

    return ParseResponse(
        title=info.get("title", "Unknown"),
        thumbnail=info.get("thumbnail"),
        duration=info.get("duration"),
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


def _download_file_sync(url: str, format_id: str, output_path: str) -> str:
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "format": format_id,
        "outtmpl": output_path,
    }
    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    return output_path


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

    direct_url = target_format.get("url")
    filesize = target_format.get("filesize") or target_format.get("filesize_approx") or 0

    if direct_url:
        is_accessible = await check_direct_link(direct_url)
        if is_accessible:
            return {"mode": "redirect", "url": direct_url}

    if filesize > settings.LARGE_FILE_THRESHOLD:
        return {"mode": "stream", "url": url, "format_id": format_id}

    os.makedirs(settings.DOWNLOAD_DIR, exist_ok=True)
    ext = target_format.get("ext", "mp4")
    output_path = os.path.join(settings.DOWNLOAD_DIR, f"{task_id}.{ext}")

    async with _semaphore:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(_executor, _download_file_sync, url, format_id, output_path)

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
