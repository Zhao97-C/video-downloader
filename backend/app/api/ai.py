from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from app.core.security import get_current_user
from app.services.ai import summarize_video, translate_subtitle

router = APIRouter()


class SummarizeRequest(BaseModel):
    title: str
    subtitles: str


class TranslateRequest(BaseModel):
    text: str
    target_language: str = "Chinese"


class AIResponse(BaseModel):
    result: str


@router.post("/summarize", response_model=AIResponse)
async def summarize(req: SummarizeRequest, current_user: dict = Depends(get_current_user)):
    if not current_user.get("is_pro"):
        raise HTTPException(status_code=403, detail="PRO subscription required")
    try:
        result = await summarize_video(req.title, req.subtitles)
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
