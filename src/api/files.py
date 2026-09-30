"""
API endpoints for file operations
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, status, BackgroundTasks
from fastapi.responses import FileResponse
from src.models.file_model import FileModel, FileListResponse
from src.services.file_service import FileService
from src.storage.file_storage import FileStorage
import os

router = APIRouter()

# Инициализация сервиса файлов
file_service = FileService()
file_storage = FileStorage()

@router.get("/")
async def list_files():
    """Получить список всех файлов"""
    try:
        files = file_service.list_files()
        return {"files": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения списка файлов: {str(e)}")

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Загрузка файла"""
    try:
        # Проверяем тип файла
        if not file.filename:
            raise HTTPException(status_code=400, detail="Не указано имя файла")
        
        # Читаем содержимое файла
        content = await file.read()
        
        # Проверяем размер файла (ограничение 100MB)
        max_file_size = 100 * 1024 * 1024  # 100MB
        if len(content) > max_file_size:
            raise HTTPException(status_code=400, detail="Размер файла превышает допустимый предел (100MB)")
        
        # Сохраняем файл через FileStorage
        saved_path = file_storage.save_file(content, file.filename)
        
        # Создаем информацию о файле
        file_info = file_service.create_file_info({
            'name': file.filename,
            'path': saved_path,
            'size': len(content),
            'type': 'file'
        })
        
        return {"message": "Файл успешно загружен", "file": file_info}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка загрузки файла: {str(e)}")

@router.delete("/{file_id}")
async def delete_file(file_id: str):
    """Удаление файла"""
    try:
        result = file_service.delete_file(file_id)
        if not result:
            raise HTTPException(status_code=404, detail="Файл не найден")
        return {"message": "Файл успешно удален"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка удаления файла: {str(e)}")

@router.get("/download/{file_id}")
async def download_file(file_id: str):
    """Скачивание файла или архива папки"""
    try:
        # Получаем информацию о файле
        file_model = file_service.get_file_by_id(file_id)
        if not file_model:
            raise HTTPException(status_code=404, detail="Файл не найден")
            
        file_path = file_model.path
        
        # Если это папка, создаем ZIP архив
        if file_model.type == 'folder':
            archive_path = file_storage.create_zip_archive(file_path)
            if not archive_path:
                raise HTTPException(status_code=500, detail="Ошибка создания ZIP архива")
            return FileResponse(archive_path, media_type='application/zip', filename=f"{file_model.name}.zip")
        else:
            # Для обычного файла возвращаем его напрямую
            if not os.path.exists(file_path):
                raise HTTPException(status_code=404, detail="Файл не найден")
            return FileResponse(file_path, media_type='application/octet-stream', filename=file_model.name)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка скачивания файла: {str(e)}")