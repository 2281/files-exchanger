"""
API endpoints for link operations
"""

from fastapi import APIRouter, HTTPException, Depends
from src.models.file_model import LinkResponse
from src.services.file_service import FileService
import secrets
import string
import os

router = APIRouter()

# Инициализация сервиса файлов
file_service = FileService()

def generate_unique_id(length: int = 10) -> str:
    """Генерация уникального ID для ссылки"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

@router.post("/{file_id}")
async def create_link(file_id: str):
    """Создать прямую ссылку на файл"""
    try:
        # Проверяем существование файла
        file_model = file_service.get_file_by_id(file_id)
        if not file_model:
            raise HTTPException(status_code=404, detail="Файл не найден")
        
        # Генерируем уникальный хеш для ссылки
        link_hash = generate_unique_id()
        
        # В реальном приложении тут можно сохранить ссылку в БД или кэш
        # Здесь просто возвращаем URL (в реальности может быть https://domain/api/download/{file_id}?link={link_hash})
        
        url = f"/api/download/{file_id}"
        return LinkResponse(url=url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка создания ссылки: {str(e)}")