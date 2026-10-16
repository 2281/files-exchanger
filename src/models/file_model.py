"""
Модели данных для файлообменника
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from src.config.settings import LINK_MAX_DAYS

class FileModel(BaseModel):
    """Модель файла или папки"""
    id: str
    name: str
    path: str = Field(exclude=True)      # путь на диске, клиенту не отдается
    owner_id: str = Field(exclude=True)
    owner_email: str
    parent_id: Optional[str] = None
    size: int
    type: str  # 'file' или 'folder'
    is_public: bool = False
    is_owner: bool = False  # принадлежит ли текущему пользователю
    created_at: datetime
    updated_at: Optional[datetime] = None

class CreateFolderModel(BaseModel):
    """Модель для создания папки"""
    name: str
    parent_id: Optional[str] = None  # None — папка создается в корне

class UpdateFileModel(BaseModel):
    """Изменение свойств файла или папки"""
    is_public: bool

class FileListResponse(BaseModel):
    """Ответ со списком файлов"""
    files: list[FileModel]

class FolderContentResponse(BaseModel):
    """Ответ с содержимым папки"""
    folder: FileModel
    files: list[FileModel]
    up_id: Optional[str] = None  # родительская папка, если она доступна пользователю

class CreateLinkModel(BaseModel):
    """Параметры временной ссылки"""
    expires_in_hours: int = Field(default=24 * 7, gt=0, le=LINK_MAX_DAYS * 24)

class LinkModel(BaseModel):
    """Временная ссылка (без токена — он показывается только при создании)"""
    id: str
    file_id: str
    file_name: str
    file_type: str
    created_at: datetime
    expires_at: datetime

class LinkResponse(BaseModel):
    """Ответ с созданной временной ссылкой"""
    url: str
    link: LinkModel
