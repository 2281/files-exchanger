"""
API endpoints for link operations
"""

from fastapi import APIRouter, HTTPException
from src.models.file_model import LinkResponse

router = APIRouter()

@router.post("/{file_id}")
async def create_link(file_id: str):
    """Создать прямую ссылку на файл"""
    try:
        # В реальном приложении здесь должна быть логика генерации уникальной ссылки
        # Для примера просто возвращаем URL для скачивания
        url = f"/api/download/{file_id}"
        return LinkResponse(url=url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка создания ссылки: {str(e)}")