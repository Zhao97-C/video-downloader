import os
import asyncio
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse, FileResponse, StreamingResponse
from yt_dlp import YoutubeDL

from app.schemas.video import ParseRequest, ParseResponse
from app.services.download import parse_video, download_video, get_task, _resolve_ffmpeg_location
from app.core.config import settings

router = APIRouter()


@router.post("/parse", response_model=ParseResponse)
async def parse_url(req: ParseRequest):
    try:
        result = await parse_video(req.url, req.mode)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse URL: {str(e)}")


@router.get("/download/{task_id}")
async def download(task_id: str, format_id: str = Query(...)):
    try:
        result = await download_video(task_id, format_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")

    if result["mode"] == "redirect":
        return RedirectResponse(url=result["url"], status_code=302)

    elif result["mode"] == "proxy":
        file_path = result["file_path"]
        filename = result["filename"]
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type="application/octet-stream",
        )

    elif result["mode"] == "stream":
        raise HTTPException(
            status_code=501,
            detail="Large file streaming is not supported for this format. Try a lower quality.",
        )
