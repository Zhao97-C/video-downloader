import json

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.core.security import get_current_user
from app.schemas.subtitle import SubtitlesResponse
from app.services.ai import (
    CHAT_MAX_QUESTIONS_PER_TASK,
    _strip_markdown_fences,
    chat_video_stream,
    count_user_questions,
    mindmap_markdown_stream,
    summarize_video_stream,
    translate_subtitle,
    trim_chat_history,
)
from app.services.download import get_task
from app.services.subtitle import (
    fetch_subtitles_for_task,
    get_or_extract_subtitles,
    text_for_ai,
)

router = APIRouter()


class SummarizeRequest(BaseModel):
    task_id: str
    output_language: str = "Chinese"


class SubtitlesRequest(BaseModel):
    task_id: str


class TranslateRequest(BaseModel):
    task_id: str
    target_language: str = "Chinese"


class MindmapRequest(BaseModel):
    task_id: str
    output_language: str = "Chinese"


class ChatRequest(BaseModel):
    task_id: str
    message: str
    output_language: str = "Chinese"


class AIResponse(BaseModel):
    result: str


@router.post("/subtitles", response_model=SubtitlesResponse)
async def get_subtitles(req: SubtitlesRequest, current_user: dict = Depends(get_current_user)):
    del current_user  # login required; whitelist PRO handled in JWT for AI routes only
    try:
        return await fetch_subtitles_for_task(req.task_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


async def _summarize_sse(
    title: str,
    subtitles: str,
    *,
    output_language: str,
    from_metadata_only: bool,
):
    try:
        async for piece in summarize_video_stream(
            title,
            subtitles,
            output_language=output_language,
            from_metadata_only=from_metadata_only,
        ):
            yield f"data: {json.dumps({'content': piece}, ensure_ascii=False)}\n\n"
        yield f"data: {json.dumps({'done': True})}\n\n"
    except Exception as e:
        yield f"event: error\ndata: {json.dumps({'detail': str(e)}, ensure_ascii=False)}\n\n"


@router.post("/summarize")
async def summarize(req: SummarizeRequest, current_user: dict = Depends(get_current_user)):
    if not current_user.get("is_pro"):
        raise HTTPException(status_code=403, detail="PRO subscription required")

    task = get_task(req.task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found or expired")

    try:
        bundle = await get_or_extract_subtitles(req.task_id, task, refresh_if_empty=True)
        info = task.get("info", {})
        subtitles = text_for_ai(bundle, info)
        if not subtitles.strip():
            raise HTTPException(status_code=404, detail="No subtitles or transcript available for this video")
        title = info.get("title", "Video")
        from_metadata = bundle.source == "none"
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

    return StreamingResponse(
        _summarize_sse(
            title,
            subtitles,
            output_language=req.output_language,
            from_metadata_only=from_metadata,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


def _get_mindmap_cache(task: dict, output_language: str) -> dict | None:
    cache = task.get("mindmap_cache")
    if not cache:
        return None
    if cache.get("output_language") != output_language:
        return None
    markdown = (cache.get("markdown") or "").strip()
    if not markdown:
        return None
    return cache


async def _mindmap_sse(
    task: dict,
    title: str,
    subtitles: str,
    *,
    output_language: str,
    from_metadata_only: bool,
):
    accumulated: list[str] = []
    try:
        async for piece in mindmap_markdown_stream(
            title,
            subtitles,
            output_language=output_language,
            from_metadata_only=from_metadata_only,
        ):
            accumulated.append(piece)
            yield f"data: {json.dumps({'content': piece}, ensure_ascii=False)}\n\n"
        markdown = _strip_markdown_fences("".join(accumulated))
        task["mindmap_cache"] = {
            "output_language": output_language,
            "markdown": markdown,
            "from_metadata_only": from_metadata_only,
        }
        yield f"data: {json.dumps({'done': True, 'from_metadata_only': from_metadata_only, 'cached': False}, ensure_ascii=False)}\n\n"
    except Exception as e:
        yield f"event: error\ndata: {json.dumps({'detail': str(e)}, ensure_ascii=False)}\n\n"


async def _mindmap_cached_sse(cache: dict):
    yield f"data: {json.dumps({'content': cache['markdown'], 'cached': True}, ensure_ascii=False)}\n\n"
    yield f"data: {json.dumps({'done': True, 'from_metadata_only': cache.get('from_metadata_only', False), 'cached': True}, ensure_ascii=False)}\n\n"


@router.post("/mindmap")
async def mindmap(req: MindmapRequest, current_user: dict = Depends(get_current_user)):
    if not current_user.get("is_pro"):
        raise HTTPException(status_code=403, detail="PRO subscription required")

    task = get_task(req.task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found or expired")

    cached = _get_mindmap_cache(task, req.output_language)
    if cached:
        return StreamingResponse(
            _mindmap_cached_sse(cached),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    try:
        bundle = await get_or_extract_subtitles(req.task_id, task, refresh_if_empty=True)
        info = task.get("info", {})
        subtitles = text_for_ai(bundle, info)
        if not subtitles.strip():
            raise HTTPException(
                status_code=404,
                detail="No subtitles or transcript available for this video",
            )
        title = info.get("title", "Video")
        from_metadata = bundle.source == "none"
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

    return StreamingResponse(
        _mindmap_sse(
            task,
            title,
            subtitles,
            output_language=req.output_language,
            from_metadata_only=from_metadata,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


async def _chat_sse(
    task: dict,
    title: str,
    subtitles: str,
    history: list[dict[str, str]],
    *,
    output_language: str,
    from_metadata_only: bool,
):
    accumulated: list[str] = []
    try:
        async for piece in chat_video_stream(
            title,
            subtitles,
            history,
            output_language=output_language,
            from_metadata_only=from_metadata_only,
        ):
            accumulated.append(piece)
            yield f"data: {json.dumps({'content': piece}, ensure_ascii=False)}\n\n"
        history.append({"role": "assistant", "content": "".join(accumulated)})
        trim_chat_history(history)
        yield f"data: {json.dumps({'done': True, 'from_metadata_only': from_metadata_only, 'questions_used': count_user_questions(history)}, ensure_ascii=False)}\n\n"
    except Exception as e:
        if history and history[-1].get("role") == "user":
            history.pop()
        yield f"event: error\ndata: {json.dumps({'detail': str(e)}, ensure_ascii=False)}\n\n"


@router.post("/chat")
async def chat(req: ChatRequest, current_user: dict = Depends(get_current_user)):
    if not current_user.get("is_pro"):
        raise HTTPException(status_code=403, detail="PRO subscription required")

    message = req.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    if len(message) > 2000:
        raise HTTPException(status_code=400, detail="Message too long (max 2000 characters)")

    task = get_task(req.task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found or expired")

    history: list[dict[str, str]] = task.setdefault("chat_history", [])
    if count_user_questions(history) >= CHAT_MAX_QUESTIONS_PER_TASK:
        raise HTTPException(
            status_code=429,
            detail=f"Question limit reached ({CHAT_MAX_QUESTIONS_PER_TASK} per video). Re-parse the link for a new session.",
        )

    try:
        bundle = await get_or_extract_subtitles(req.task_id, task, refresh_if_empty=True)
        info = task.get("info", {})
        subtitles = text_for_ai(bundle, info)
        if not subtitles.strip():
            raise HTTPException(
                status_code=404,
                detail="No subtitles or transcript available for this video",
            )
        title = info.get("title", "Video")
        from_metadata = bundle.source == "none"
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

    history.append({"role": "user", "content": message})
    trim_chat_history(history)

    return StreamingResponse(
        _chat_sse(
            task,
            title,
            subtitles,
            history,
            output_language=req.output_language,
            from_metadata_only=from_metadata,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/translate-subtitle", response_model=AIResponse)
async def translate(req: TranslateRequest, current_user: dict = Depends(get_current_user)):
    if not current_user.get("is_pro"):
        raise HTTPException(status_code=403, detail="PRO subscription required")

    task = get_task(req.task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found or expired")

    try:
        bundle = await get_or_extract_subtitles(req.task_id, task, refresh_if_empty=True)
        text = text_for_ai(bundle, task.get("info", {}))
        if not text.strip():
            raise HTTPException(
                status_code=404,
                detail="No subtitles or transcript available for this video",
            )
        result = await translate_subtitle(
            text,
            req.target_language,
            from_description=not bundle.segments and bundle.source == "none",
        )
        return AIResponse(result=result)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
