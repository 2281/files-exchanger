"""
API endpoints for temporary links
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request
from src.models.auth_model import User
from src.models.file_model import CreateLinkModel, LinkModel, LinkResponse
from src.services import link_service
from src.api.deps import get_current_user
from src.api.files import file_service, file_response, get_accessible_file

router = APIRouter()

# Публичные адреса ссылок (без входа), подключаются без префикса /api
share_router = APIRouter()

@router.post("/{file_id}", response_model=LinkResponse)
async def create_link(file_id: str, request: Request, data: CreateLinkModel = CreateLinkModel(),
                      user: User = Depends(get_current_user)):
    """Создать временную ссылку на доступный пользователю файл или папку"""
    file = get_accessible_file(file_id, user)
    token, link = link_service.create_link(file.id, user.id, data.expires_in_hours)
    return LinkResponse(url=str(request.url_for("open_shared_link", token=token)), link=link)

@router.get("/", response_model=List[LinkModel])
async def list_links(user: User = Depends(get_current_user)):
    """Действующие ссылки, созданные пользователем"""
    return link_service.list_links(user.id)

@router.delete("/{link_id}")
async def delete_link(link_id: str, user: User = Depends(get_current_user)):
    """Отозвать ссылку"""
    if not link_service.delete_link(link_id, user.id):
        raise HTTPException(status_code=404, detail="Ссылка не найдена")
    return {"message": "Ссылка отозвана"}

@share_router.get("/s/{token}")
async def open_shared_link(token: str):
    """Скачать файл или папку по временной ссылке.

    Ссылка работает, пока не истекла и пока у ее создателя есть доступ к объекту
    (например, владелец не снял пометку «видна всем»).
    """
    resolved = link_service.resolve(token)
    file = None
    if resolved:
        file_id, created_by = resolved
        file = file_service.get_file(file_id, created_by)
    if not file or not file_service.can_read(file, created_by):
        raise HTTPException(status_code=404, detail="Ссылка недействительна или срок ее действия истек")
    return file_response(file)
