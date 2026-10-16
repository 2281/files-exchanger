"""
Storage service for file operations
"""

import os
import zipfile
import tempfile
from src.config.settings import STORAGE_PATH

class FileStorage:
    """Сервис хранения файлов"""

    def __init__(self, storage_path: str = STORAGE_PATH):
        self.storage_path = storage_path
        os.makedirs(storage_path, exist_ok=True)

    def save_file(self, file_data: bytes, filename: str, directory: str = None) -> str:
        """Сохранить файл в директорию (по умолчанию — корень хранилища)"""
        file_path = os.path.join(directory or self.storage_path, filename)
        if os.path.exists(file_path):
            raise FileExistsError(f"Файл '{filename}' уже существует")
        with open(file_path, 'wb') as f:
            f.write(file_data)
        return file_path

    def create_zip_archive(self, folder_path: str) -> str:
        """Создать ZIP архив папки во временной директории.

        Вызывающий код отвечает за удаление архива после использования.
        """
        fd, archive_path = tempfile.mkstemp(suffix=".zip")
        os.close(fd)
        try:
            with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(folder_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arc_path = os.path.relpath(file_path, folder_path)
                        zipf.write(file_path, arc_path)
        except Exception:
            os.remove(archive_path)
            raise
        return archive_path
