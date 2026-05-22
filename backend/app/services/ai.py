from openai import AsyncOpenAI

from app.core.config import settings
from app.services.subtitle import flatten_for_ai, get_or_extract_subtitles

client = AsyncOpenAI(
    api_key=settings.DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com",
) if settings.DEEPSEEK_API_KEY else None


async def extract_subtitles_for_ai(task_id: str, task_info: dict) -> str:
    bundle = await get_or_extract_subtitles(task_id, task_info)
    return flatten_for_ai(bundle)


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
                    f"Subtitles/Transcript:\n{subtitles}\n\n"
                    f"Please provide a summary of this video."
                ),
            },
        ],
        max_tokens=1000,
    )
    return response.choices[0].message.content


async def translate_subtitle(text: str, target_language: str, *, from_description: bool = False) -> str:
    if not client:
        raise RuntimeError("DeepSeek API key not configured")

    hint = ""
    if from_description:
        hint = " Note: source is video description, not timed subtitles. "

    response = await client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {
                "role": "system",
                "content": (
                    f"Translate the following subtitle/transcript text to {target_language}.{hint}"
                    "Preserve paragraph breaks. If lines include timestamps, keep them. "
                    "Only output the translation."
                ),
            },
            {"role": "user", "content": text[:10000]},
        ],
        max_tokens=4000,
    )
    return response.choices[0].message.content
