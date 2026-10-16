"""
Модели данных для аутентификации
"""

from pydantic import BaseModel

class User(BaseModel):
    """Пользователь"""
    id: str
    email: str

class PasswordRequest(BaseModel):
    """Запрос пароля на email"""
    email: str

class LoginRequest(BaseModel):
    """Вход по email и паролю"""
    email: str
    password: str
