from pydantic import BaseModel


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
