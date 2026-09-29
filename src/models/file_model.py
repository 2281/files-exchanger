"""
Модели данных для файлообменника
"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class FileModel(BaseModel):
    """Модель файла"""
    id: str
    name: str
    path: str
    size: int
    type: str  # 'file' или 'folder'
    created_at: datetime
    updated_at: Optional[datetime] = None

class CreateFileModel(BaseModel):
    """Модель для создания файла"""
    name: str
    path: str
    size: int
    type: str

class FileListResponse(BaseModel):
    """Ответ с списком файлов"""
    files: list[FileModel]

class LinkResponse(BaseModel):
    """Ответ с прямой ссылкой"""
    url: str