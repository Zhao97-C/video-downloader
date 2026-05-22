from typing import Literal

from pydantic import BaseModel

SubtitleSource = Literal["auto_subtitle", "manual_subtitle", "description", "none"]


class SubtitleSegment(BaseModel):
    start: float
    end: float
    text: str


class SubtitlesResponse(BaseModel):
    source: SubtitleSource
    language: str | None = None
    segments: list[SubtitleSegment] = []
    plain_text: str = ""
    char_count: int = 0
    truncated: bool = False
    has_timestamps: bool = True
    extraction_method: str | None = None  # platform_api | ytdlp
