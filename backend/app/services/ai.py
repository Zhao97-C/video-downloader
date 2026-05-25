from openai import AsyncOpenAI

from app.core.config import settings
from app.services.subtitle import get_or_extract_subtitles, text_for_ai

client = AsyncOpenAI(
    api_key=settings.DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com",
) if settings.DEEPSEEK_API_KEY else None


async def extract_subtitles_for_ai(task_id: str, task_info: dict) -> str:
    bundle = await get_or_extract_subtitles(task_id, task_info, refresh_if_empty=True)
    return text_for_ai(bundle, task_info.get("info", {}))


def _normalize_output_language(language: str) -> str:
    if language.lower() in ("chinese", "zh", "zh-cn", "简体中文"):
        return "Simplified Chinese"
    return language


async def summarize_video(
    title: str,
    subtitles: str,
    *,
    output_language: str = "Chinese",
    from_metadata_only: bool = False,
) -> str:
    if not client:
        raise RuntimeError("DeepSeek API key not configured")

    lang = _normalize_output_language(output_language)
    meta_hint = ""
    if from_metadata_only:
        meta_hint = (
            " Timed subtitles are not available; summarize from the title/description/metadata only. "
            "State that the summary is based on limited metadata if appropriate."
        )

    response = await client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a helpful assistant that summarizes video content. "
                    "Provide a concise, well-structured summary with key points. "
                    "Use bullet points for clarity. "
                    f"You MUST write the entire summary in {lang} only. "
                    "Do not respond in any other language."
                    + meta_hint
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Video title: {title}\n\n"
                    f"Subtitles/Transcript/Metadata:\n{subtitles}\n\n"
                    f"Please provide a summary of this video in {lang}."
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
