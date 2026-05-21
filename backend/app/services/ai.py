from openai import AsyncOpenAI
from app.core.config import settings

client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None


async def summarize_video(title: str, subtitles: str) -> str:
    if not client:
        raise RuntimeError("OpenAI API key not configured")

    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that summarizes video content. Provide a concise, well-structured summary."},
            {"role": "user", "content": f"Video title: {title}\n\nSubtitles/Transcript:\n{subtitles[:8000]}\n\nPlease provide a summary of this video."},
        ],
        max_tokens=1000,
    )
    return response.choices[0].message.content


async def translate_subtitle(text: str, target_language: str) -> str:
    if not client:
        raise RuntimeError("OpenAI API key not configured")

    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": f"Translate the following subtitle text to {target_language}. Keep the timing markers if present. Only output the translation."},
            {"role": "user", "content": text[:10000]},
        ],
        max_tokens=4000,
    )
    return response.choices[0].message.content
