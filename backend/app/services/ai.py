import asyncio
import os
import tempfile
from concurrent.futures import ThreadPoolExecutor

from openai import AsyncOpenAI
from yt_dlp import YoutubeDL

from app.core.config import settings

_executor = ThreadPoolExecutor(max_workers=3)

client = AsyncOpenAI(
    api_key=settings.DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com",
) if settings.DEEPSEEK_API_KEY else None


def _extract_subtitles_sync(task_info: dict) -> str:
    """Extract subtitles/transcript from a parsed video using yt-dlp."""
    url = task_info["url"]
    info = task_info.get("info", {})

    subs_dir = tempfile.mkdtemp(prefix="saveany-subs-")
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "writesubtitles": True,
        "writeautosub": True,
        "subtitleslangs": ["en", "zh-Hans", "zh-CN", "zh", "ja", "ko", "auto"],
        "subtitlesformat": "vtt",
        "outtmpl": os.path.join(subs_dir, "%(id)s.%(ext)s"),
        "skip_download": True,
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.extract_info(url, download=False)

        # Collect subtitle content from downloaded files
        subtitle_text = ""
        for root, _, files in os.walk(subs_dir):
            for fname in sorted(files):
                if fname.endswith((".vtt", ".srt")):
                    fpath = os.path.join(root, fname)
                    try:
                        with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                            content = f.read()
                            subtitle_text += f"\n--- {fname} ---\n{content}"
                    except Exception:
                        pass

        # Clean up temp files
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

        if subtitle_text.strip():
            # Strip VTT/SRT formatting cues for cleaner input
            cleaned = []
            for line in subtitle_text.split("\n"):
                line = line.strip()
                # Skip VTT headers, timestamps, cue numbers
                if (
                    not line
                    or line.startswith("WEBVTT")
                    or line.startswith("NOTE")
                    or line == "kind:"
                    or "-->" in line
                    or line.isdigit()
                ):
                    continue
                cleaned.append(line)
            subtitle_text = " ".join(cleaned)

        if subtitle_text.strip():
            return subtitle_text[:8000]

        # Fallback: use video description
        return (info.get("description") or "")[:8000]

    except Exception:
        return (info.get("description") or "")[:8000]


async def extract_subtitles(task_id: str, task_info: dict) -> str:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_executor, _extract_subtitles_sync, task_info)


async def summarize_video(title: str, subtitles: str) -> str:
    if not client:
        raise RuntimeError("DeepSeek API key not configured")

    response = await client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a helpful assistant that summarizes video content. "
                    "Provide a concise, well-structured summary with key points. "
                    "Use bullet points for clarity."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Video title: {title}\n\n"
                    f"Subtitles/Transcript:\n{subtitles[:8000]}\n\n"
                    f"Please provide a summary of this video."
                ),
            },
        ],
        max_tokens=1000,
    )
    return response.choices[0].message.content


async def translate_subtitle(text: str, target_language: str) -> str:
    if not client:
        raise RuntimeError("DeepSeek API key not configured")

    response = await client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {
                "role": "system",
                "content": (
                    f"Translate the following subtitle text to {target_language}. "
                    "Keep the timing markers if present. Only output the translation."
                ),
            },
            {"role": "user", "content": text[:10000]},
        ],
        max_tokens=4000,
    )
    return response.choices[0].message.content
