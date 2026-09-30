"""
Service for file operations
"""

from src.models.file_model import FileModel, CreateFileModel
import os
import uuid
from datetime import datetime
from typing import List, Optional

class FileService:
    """Сервис для работы с файлами"""
    
    def __init__(self):
        self.storage_path = "storage"
        os.makedirs(self.storage_path, exist_ok=True)
        
    def list_files(self) -> List[FileModel]:
        """Получить список всех файлов"""
        files = []
        try:
            if not os.path.exists(self.storage_path):
                return files
                
            for filename in os.listdir(self.storage_path):
                file_path = os.path.join(self.storage_path, filename)
                stat = os.stat(file_path)
                
                # Создаем модель файла с уникальным ID
                file_model = FileModel(
                    id=str(uuid.uuid4()),
                    name=filename,
                    path=file_path,
                    size=stat.st_size,
                    type='folder' if os.path.isdir(file_path) else 'file',
                    created_at=datetime.fromtimestamp(stat.st_ctime),
                    updated_at=datetime.fromtimestamp(stat.st_mtime)
                )
                files.append(file_model)
                
        except Exception as e:
            print(f"Ошибка получения списка файлов: {e}")
            
        return files
    
    def create_file_info(self, file_data: dict) -> FileModel:
        """Создать информацию о файле"""
        # В реальном приложении здесь может быть логика сохранения в БД
        # Для примера просто возвращаем модель файла
        return FileModel(
            id=str(uuid.uuid4()),
            name=file_data['name'],
            path=file_data['path'],
            size=file_data['size'],
            type=file_data['type'],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    def delete_file(self, file_id: str) -> bool:
        """Удалить файл"""
        try:
            # В реальном приложении здесь должна быть логика поиска файла по ID
            # Для примера удаляем первый файл из хранилища
            files = self.list_files()
            if not files:
                return False
                
            # Удаляем первый файл (в реальности нужно искать по ID)
            first_file = files[0]
            if os.path.exists(first_file.path):
                os.remove(first_file.path)
                return True
            return False
            
        except Exception as e:
            print(f"Ошибка удаления файла: {e}")
            return False
    
    def get_file_path(self, file_id: str) -> str:
        """Получить путь к файлу"""
        # В реальном приложении здесь должна быть логика поиска файла по ID
        files = self.list_files()
        if files:
            return files[0].path  # Для примера возвращаем первый файл
        return ""