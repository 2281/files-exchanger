"""
Файлообменник - Точка входа в приложение
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from src.api.files import router as files_router
from src.api.links import router as links_router
import os

# Создание приложения FastAPI
app = FastAPI(
    title="Файлообменник",
    description="Файлообменник между пользователями внутри локальной сети",
    version="1.0.0"
)

# Подключение маршрутов API
app.include_router(files_router, prefix="/api/files", tags=["files"])
app.include_router(links_router, prefix="/api/links", tags=["links"])

# Подключение статических файлов
app.mount("/static", StaticFiles(directory="static"), name="static")

# Шаблоны для веб-интерфейса
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Главная страница — список файлов"""
    return templates.TemplateResponse("index.html", {"request": {}})

@app.get("/upload", response_class=HTMLResponse)
async def read_upload():
    """Страница загрузки файлов"""
    return templates.TemplateResponse("upload.html", {"request": {}})

@app.get("/health")
async def health_check():
    """Проверка статуса сервиса"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)