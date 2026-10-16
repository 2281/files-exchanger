"""
Общие зависимости API
"""

from typing import Optional
from fastapi import Depends, HTTPException, Request
from src.config.settings import SESSION_COOKIE_NAME
from src.models.auth_model import User
from src.services import auth_service

def get_optional_user(request: Request) -> Optional[User]:
    """Текущий пользователь по cookie сессии или None"""
    token = request.cookies.get(SESSION_COOKIE_NAME)
    return auth_service.get_user_by_session(token) if token else None

def get_current_user(user: Optional[User] = Depends(get_optional_user)) -> User:
    """Текущий пользователь; без входа — 401"""
    if not user:
        raise HTTPException(status_code=401, detail="Требуется вход")
    return user
