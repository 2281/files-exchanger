"""
Файлообменник - Точка входа в приложение
"""

from typing import Optional
from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from src.db import init_db
from src.models.auth_model import User
from src.api.deps import get_optional_user
from src.api.auth import router as auth_router
from src.api.files import router as files_router
from src.api.links import router as links_router, share_router

# Создание таблиц БД при необходимости
init_db()

# Создание приложения FastAPI
app = FastAPI(
    title="Файлообменник",
    description="Файлообменник между пользователями внутри локальной сети",
    version="1.0.0"
)

# Подключение маршрутов API
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(files_router, prefix="/api/files", tags=["files"])
app.include_router(links_router, prefix="/api/links", tags=["links"])
app.include_router(share_router, tags=["links"])

# Подключение статических файлов
app.mount("/static", StaticFiles(directory="static"), name="static")

# Шаблоны для веб-интерфейса
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, user: Optional[User] = Depends(get_optional_user)):
    """Главная страница — список файлов корня или папки (?folder_id=...)"""
    if not user:
        return RedirectResponse("/login")
    return templates.TemplateResponse("index.html", {"request": request, "user": user})

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, user: Optional[User] = Depends(get_optional_user)):
    """Страница входа и получения пароля"""
    if user:
        return RedirectResponse("/")
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/health")
async def health_check():
    """Проверка статуса сервиса"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
