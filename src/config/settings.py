"""
Настройки приложения файлообменника

Значения можно переопределить через переменные окружения или файл .env (см. .env.example)
"""

import os
from dotenv import load_dotenv

load_dotenv()

def _env_bool(name: str, default: bool) -> bool:
    return os.getenv(name, str(default)).strip().lower() in ("1", "true", "yes", "on")

# Путь для хранения файлов (внутри — отдельная папка на каждого пользователя)
STORAGE_PATH = os.getenv("STORAGE_PATH", "storage")

# Путь к базе данных
DB_PATH = os.getenv("DB_PATH", "files.db")

# Максимальный размер файла (в байтах)
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

# Разрешенные типы файлов
ALLOWED_EXTENSIONS = {
    ".txt", ".pdf", ".jpg", ".jpeg", ".png", ".gif",
    ".zip", ".rar", ".doc", ".docx", ".xls", ".xlsx",
    ".ppt", ".pptx", ".mp3", ".mp4", ".avi", ".mkv"
}

# Сессии
SESSION_COOKIE_NAME = "session"
SESSION_TTL_HOURS = int(os.getenv("SESSION_TTL_HOURS", 24 * 7))
COOKIE_SECURE = _env_bool("COOKIE_SECURE", False)  # включить после перехода на HTTPS

# Защита от перебора и спама
LOGIN_MAX_ATTEMPTS = 5                  # неудачных попыток входа подряд
LOGIN_LOCK_MINUTES = 5                  # блокировка входа после превышения
PASSWORD_REQUEST_INTERVAL_SECONDS = 60  # минимальный интервал между письмами с паролем

# Временные ссылки
LINK_MAX_DAYS = 30

# Отправка почты. Если SMTP_HOST не задан, письма печатаются в консоль сервера
SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM = os.getenv("SMTP_FROM", "") or SMTP_USER
SMTP_USE_SSL = _env_bool("SMTP_USE_SSL", False)    # SMTPS, обычно порт 465
SMTP_STARTTLS = _env_bool("SMTP_STARTTLS", True)   # STARTTLS, обычно порт 587

# Создание директории хранения при необходимости
os.makedirs(STORAGE_PATH, exist_ok=True)
