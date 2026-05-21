from pydantic import BaseModel, field_validator


class ParseRequest(BaseModel):
    url: str
    mode: str = "auto"


class FormatInfo(BaseModel):
    format_id: str
    ext: str
    resolution: str | None = None
    filesize: int | None = None
    vcodec: str | None = None
    acodec: str | None = None
    quality_label: str | None = None
    is_pro: bool = False


class ParseResponse(BaseModel):
    title: str
    thumbnail: str | None = None
    duration: int | None = None
    platform: str | None = None
    formats: list[FormatInfo]
    task_id: str

    @field_validator("duration", mode="before")
    @classmethod
    def duration_to_int(cls, v):
        if v is None:
            return None
        try:
            return int(float(v))
        except (TypeError, ValueError):
            return None
