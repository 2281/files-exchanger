"""
Storage service for file operations
"""

import os
import zipfile
from pathlib import Path
from typing import Optional
import tempfile

class FileStorage:
    """Сервис хранения файлов"""
    
    def __init__(self, storage_path: str = "storage"):
        self.storage_path = storage_path
        os.makedirs(storage_path, exist_ok=True)
    
    def save_file(self, file_data: bytes, filename: str) -> str:
        """Сохранить файл"""
        file_path = os.path.join(self.storage_path, filename)
        with open(file_path, 'wb') as f:
            f.write(file_data)
        return file_path
    
    def delete_file(self, file_path: str) -> bool:
        """Удалить файл"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception:
            return False
    
    def create_zip_archive(self, folder_path: str) -> Optional[str]:
        """Создать ZIP архив папки"""
        try:
            # Создаем временный файл для архива
            archive_path = f"{folder_path}.zip"
            
            with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(folder_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arc_path = os.path.relpath(file_path, folder_path)
                        zipf.write(file_path, arc_path)
            
            return archive_path
        except Exception as e:
            print(f"Ошибка создания ZIP архива: {e}")
            return None
    
    def is_folder(self, path: str) -> bool:
        """Проверить, является ли путь папкой"""
        return os.path.isdir(path)