"""
API endpoints for authentication

Обработчики синхронные: FastAPI выполняет их в пуле потоков,
поэтому отправка письма и хеширование пароля не блокируют сервер.
"""

import smtplib
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from src.config.settings import SESSION_COOKIE_NAME, SESSION_TTL_HOURS, COOKIE_SECURE
from src.models.auth_model import User, PasswordRequest, LoginRequest
from src.services import auth_service
from src.api.deps import get_current_user

router = APIRouter()

@router.post("/request-password")
def request_password(data: PasswordRequest, request: Request):
    """Сгенерировать пароль и отправить его на email (регистрация и восстановление)"""
    try:
        email = auth_service.request_password(data.email, str(request.url_for("login_page")))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except auth_service.RateLimitError as e:
        raise HTTPException(status_code=429, detail=str(e))
    except (smtplib.SMTPException, OSError) as e:
        print(f"Ошибка отправки письма на {data.email}: {e}")
        raise HTTPException(status_code=502, detail="Не удалось отправить письмо, попробуйте позже")
    return {"message": f"Пароль отправлен на {email}"}

@router.post("/login", response_model=User)
def login(data: LoginRequest, response: Response):
    """Вход по email и паролю; сессия сохраняется в cookie"""
    try:
        token, user = auth_service.login(data.email, data.password)
    except auth_service.AuthError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except auth_service.RateLimitError as e:
        raise HTTPException(status_code=429, detail=str(e))

    response.set_cookie(
        SESSION_COOKIE_NAME, token,
        max_age=SESSION_TTL_HOURS * 3600,
        httponly=True, samesite="lax", secure=COOKIE_SECURE
    )
    return user

@router.post("/logout")
def logout(request: Request, response: Response):
    """Выход: удалить сессию и cookie"""
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if token:
        auth_service.logout(token)
    response.delete_cookie(SESSION_COOKIE_NAME)
    return {"message": "Вы вышли из системы"}

@router.get("/me", response_model=User)
def me(user: User = Depends(get_current_user)):
    """Текущий пользователь"""
    return user
