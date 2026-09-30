"""
API endpoints for file operations
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, status
from src.models.file_model import FileModel, FileListResponse
from src.services.file_service import FileService
import os

router = APIRouter()

# Инициализация сервиса файлов
file_service = FileService()

@router.get("/", response_model=FileListResponse)
async def list_files():
    """Получить список всех файлов"""
    try:
        files = file_service.list_files()
        return FileListResponse(files=files)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения списка файлов: {str(e)}")

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Загрузка файла"""
    try:
        # Проверяем тип файла (это просто пример)
        if not file.filename:
            raise HTTPException(status_code=400, detail="Не указано имя файла")
        
        # Сохраняем файл
        file_location = os.path.join("storage", file.filename)
        os.makedirs("storage", exist_ok=True)
        
        with open(file_location, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Создаем информацию о файле
        file_info = file_service.create_file_info({
            'name': file.filename,
            'path': file_location,
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
    """Скачивание файла"""
    try:
        file_path = file_service.get_file_path(file_id)
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Файл не найден")
            
        # Для простоты возвращаем путь к файлу (в реальном приложении нужно использовать FileResponse)
        return {"file_path": file_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка скачивания файла: {str(e)}")