"""文件素材相关的 Pydantic Schemas。"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

class FileTypeEnum(str, Enum):
    image = "image"
    video = "video"


class FileBase(BaseModel):
    id: str = Field(..., description="文件 ID")
    type: FileTypeEnum = Field(..., description="文件类型")
    name: str = Field(..., description="文件名/标题")
    thumbnail: str = Field("", description="缩略图 URL/路径")
    tags: list[str] = Field(default_factory=list, description="标签")


class FileCreate(BaseModel):
    type: FileTypeEnum
    name: str
    thumbnail: str = ""
    tags: list[str] = Field(default_factory=list)


class FileUpdate(BaseModel):
    name: str | None = None
    thumbnail: str | None = None
    tags: list[str] | None = None


class FileRead(FileBase):
    class Config:
        from_attributes = True

