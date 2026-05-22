from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from app.core.security import get_current_user
from app.schemas.subtitle import SubtitlesResponse
from app.services.ai import (
    summarize_video,
    translate_subtitle,
    extract_subtitles_for_ai,
)
from app.services.download import get_task
from app.services.subtitle import fetch_subtitles_for_task, flatten_for_ai, get_or_extract_subtitles

router = APIRouter()


class SummarizeRequest(BaseModel):
    task_id: str


class SubtitlesRequest(BaseModel):
    task_id: str


class TranslateRequest(BaseModel):
    task_id: str
    target_language: str = "Chinese"


class AIResponse(BaseModel):
    result: str


@router.post("/subtitles", response_model=SubtitlesResponse)
async def get_subtitles(req: SubtitlesRequest, current_user: dict = Depends(get_current_user)):
    del current_user  # login required; whitelist PRO handled in JWT for AI routes only
    try:
        return await fetch_subtitles_for_task(req.task_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/summarize", response_model=AIResponse)
async def summarize(req: SummarizeRequest, current_user: dict = Depends(get_current_user)):
    if not current_user.get("is_pro"):
        raise HTTPException(status_code=403, detail="PRO subscription required")

    task = get_task(req.task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found or expired")

    try:
        subtitles = await extract_subtitles_for_ai(req.task_id, task)
        if not subtitles.strip():
            raise HTTPException(status_code=404, detail="No subtitles or transcript available for this video")
        title = task.get("info", {}).get("title", "Video")
        result = await summarize_video(title, subtitles)
        return AIResponse(result=result)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.post("/translate-subtitle", response_model=AIResponse)
async def translate(req: TranslateRequest, current_user: dict = Depends(get_current_user)):
    if not current_user.get("is_pro"):
        raise HTTPException(status_code=403, detail="PRO subscription required")

    task = get_task(req.task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found or expired")

    try:
        bundle = await get_or_extract_subtitles(req.task_id, task)
        text = bundle.plain_text or flatten_for_ai(bundle)
        if not text.strip():
            raise HTTPException(status_code=404, detail="No subtitles or transcript available for this video")
        result = await translate_subtitle(
            text,
            req.target_language,
            from_description=bundle.source == "description",
        )
        return AIResponse(result=result)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
