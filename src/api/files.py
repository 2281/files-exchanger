"""
API endpoints for file operations
"""

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask
from src.models.auth_model import User
from src.models.file_model import (
    FileModel, FileListResponse, FolderContentResponse, CreateFolderModel, UpdateFileModel
)
from src.services.file_service import FileService, validate_name
from src.storage.file_storage import FileStorage
from src.config.settings import MAX_FILE_SIZE
from src.api.deps import get_current_user
import os

router = APIRouter()

# Инициализация сервиса файлов
file_service = FileService()
file_storage = FileStorage()

def get_accessible_file(file_id: str, user: User, folder: bool = False, owned: bool = False) -> FileModel:
    """Получить файл или папку, доступные пользователю.

    Недоступные объекты не отличаются от несуществующих (404).
    owned=True — требуются права владельца (403 для чужих общих объектов).
    """
    file = file_service.get_file(file_id, user.id)
    if not file or not file_service.can_read(file, user.id) or (folder and file.type != 'folder'):
        raise HTTPException(status_code=404, detail="Папка не найдена" if folder else "Файл не найден")
    if owned and not file.is_owner:
        raise HTTPException(status_code=403, detail="Изменять можно только свои файлы и папки")
    return file

def file_response(file: FileModel) -> FileResponse:
    """Отдать файл или ZIP архив папки (архив удаляется после отправки)"""
    if not os.path.exists(file.path):
        raise HTTPException(status_code=404, detail="Файл не найден")

    if file.type == 'folder':
        archive_path = file_storage.create_zip_archive(file.path)
        return FileResponse(
            archive_path,
            media_type='application/zip',
            filename=f"{file.name}.zip",
            background=BackgroundTask(os.remove, archive_path)
        )

    return FileResponse(file.path, media_type='application/octet-stream', filename=file.name)

async def _save_upload(file: UploadFile, user: User, folder: FileModel = None) -> FileModel:
    """Проверить и сохранить загруженный файл, создать запись о нем"""
    try:
        filename = validate_name(file.filename)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"Размер файла превышает допустимый предел ({MAX_FILE_SIZE // (1024 * 1024)}MB)"
        )

    directory = folder.path if folder else file_service.user_root(user.id)
    try:
        saved_path = file_storage.save_file(content, filename, directory)
    except FileExistsError as e:
        raise HTTPException(status_code=409, detail=str(e))

    return file_service.create_file_info(
        filename, saved_path, len(content), 'file', user.id, folder.id if folder else None
    )

@router.get("/", response_model=FileListResponse)
async def list_files(user: User = Depends(get_current_user)):
    """Свои файлы и папки верхнего уровня и общие файлы других пользователей"""
    return FileListResponse(files=file_service.list_root(user.id))

@router.post("/upload")
async def upload_file(file: UploadFile = File(...), user: User = Depends(get_current_user)):
    """Загрузка файла в свой корень"""
    file_info = await _save_upload(file, user)
    return {"message": "Файл успешно загружен", "file": file_info}

@router.post("/folder")
async def create_folder(folder: CreateFolderModel, user: User = Depends(get_current_user)):
    """Создать папку (в своем корне или внутри своей папки parent_id)"""
    parent = get_accessible_file(folder.parent_id, user, folder=True, owned=True) if folder.parent_id else None
    try:
        folder_result = file_service.create_folder(folder.name, user.id, parent)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileExistsError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return {"message": "Папка успешно создана", "folder": folder_result}

@router.get("/folder/{folder_id}/list", response_model=FolderContentResponse)
async def list_folder_content(folder_id: str, user: User = Depends(get_current_user)):
    """Получить папку и ее прямое содержимое"""
    folder = get_accessible_file(folder_id, user, folder=True)
    return FolderContentResponse(
        folder=folder,
        files=file_service.list_children(folder, user.id),
        up_id=file_service.readable_parent_id(folder, user.id)
    )

@router.post("/folder/{folder_id}/upload")
async def upload_file_to_folder(folder_id: str, file: UploadFile = File(...),
                                user: User = Depends(get_current_user)):
    """Загрузить файл в свою папку"""
    folder = get_accessible_file(folder_id, user, folder=True, owned=True)
    file_info = await _save_upload(file, user, folder)
    return {"message": "Файл успешно загружен в папку", "file": file_info}

@router.patch("/{file_id}", response_model=FileModel)
async def update_file(file_id: str, data: UpdateFileModel, user: User = Depends(get_current_user)):
    """Пометить свой файл или папку как «видна всем» или личные"""
    file = get_accessible_file(file_id, user, owned=True)
    return file_service.set_public(file, data.is_public)

@router.delete("/{file_id}")
async def delete_file(file_id: str, user: User = Depends(get_current_user)):
    """Удаление своего файла или папки"""
    file_service.delete_file(get_accessible_file(file_id, user, owned=True))
    return {"message": "Файл успешно удален"}

@router.get("/download/{file_id}")
async def download_file(file_id: str, user: User = Depends(get_current_user)):
    """Скачивание файла или архива папки"""
    return file_response(get_accessible_file(file_id, user))
