from fastapi import APIRouter, HTTPException, Depends

from app.core.security import get_current_user
from app.services.ai import summarize_video, translate_subtitle, extract_subtitles
from app.services.download import get_task

router = APIRouter()


from pydantic import BaseModel


class SummarizeRequest(BaseModel):
    task_id: str


class TranslateRequest(BaseModel):
    text: str
    target_language: str = "Chinese"


class AIResponse(BaseModel):
    result: str


@router.post("/summarize", response_model=AIResponse)
async def summarize(req: SummarizeRequest, current_user: dict = Depends(get_current_user)):
    if not current_user.get("is_pro"):
        raise HTTPException(status_code=403, detail="PRO subscription required")

    task = get_task(req.task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found or expired")

    try:
        subtitles = await extract_subtitles(req.task_id, task)
        title = task.get("info", {}).get("title", "Video")
        result = await summarize_video(title, subtitles)
        return AIResponse(result=result)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.post("/translate-subtitle", response_model=AIResponse)
async def translate(req: TranslateRequest, current_user: dict = Depends(get_current_user)):
    if not current_user.get("is_pro"):
        raise HTTPException(status_code=403, detail="PRO subscription required")
    try:
        result = await translate_subtitle(req.text, req.target_language)
        return AIResponse(result=result)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
