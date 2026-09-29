"""
Настройки приложения файлообменника
"""

import os

# Путь для хранения файлов
STORAGE_PATH = "./storage"

# Максимальный размер файла (в байтах)
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

# Разрешенные типы файлов
ALLOWED_EXTENSIONS = {
    ".txt", ".pdf", ".jpg", ".jpeg", ".png", ".gif", 
    ".zip", ".rar", ".doc", ".docx", ".xls", ".xlsx",
    ".ppt", ".pptx", ".mp3", ".mp4", ".avi", ".mkv"
}

# Создание директории хранения при необходимости
os.makedirs(STORAGE_PATH, exist_ok=True)