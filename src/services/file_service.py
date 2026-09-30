"""
Service for file operations
"""

from src.models.file_model import FileModel, CreateFileModel
import os
import uuid
from datetime import datetime
from typing import List, Optional
import sqlite3

class FileService:
    """Сервис для работы с файлами"""
    
    def __init__(self):
        self.storage_path = "storage"
        os.makedirs(self.storage_path, exist_ok=True)
        self.init_db()
        
    def init_db(self):
        """Инициализация базы данных"""
        conn = sqlite3.connect('files.db')
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS files (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                path TEXT NOT NULL,
                size INTEGER NOT NULL,
                type TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
        
    def list_files(self) -> List[FileModel]:
        """Получить список всех файлов"""
        files = []
        try:
            if not os.path.exists(self.storage_path):
                return files
                
            # Получаем файлы из БД
            conn = sqlite3.connect('files.db')
            cursor = conn.cursor()
            cursor.execute('SELECT id, name, path, size, type, created_at, updated_at FROM files')
            rows = cursor.fetchall()
            conn.close()
            
            for row in rows:
                file_model = FileModel(
                    id=row[0],
                    name=row[1],
                    path=row[2],
                    size=row[3],
                    type=row[4],
                    created_at=datetime.fromisoformat(row[5]),
                    updated_at=datetime.fromisoformat(row[6]) if row[6] else None
                )
                files.append(file_model)
                
        except Exception as e:
            print(f"Ошибка получения списка файлов: {e}")
            
        return files
    
    def create_file_info(self, file_data: dict) -> FileModel:
        """Создать информацию о файле"""
        # Генерируем уникальный ID
        file_id = str(uuid.uuid4())
        
        # Сохраняем в БД
        conn = sqlite3.connect('files.db')
        cursor = conn.cursor()
        now = datetime.now()
        cursor.execute('''
            INSERT INTO files (id, name, path, size, type, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            file_id,
            file_data['name'],
            file_data['path'],
            file_data['size'],
            file_data['type'],
            now.isoformat(),
            now.isoformat()
        ))
        conn.commit()
        conn.close()
        
        # Возвращаем модель файла
        return FileModel(
            id=file_id,
            name=file_data['name'],
            path=file_data['path'],
            size=file_data['size'],
            type=file_data['type'],
            created_at=now,
            updated_at=now
        )
    
    def delete_file(self, file_id: str) -> bool:
        """Удалить файл"""
        try:
            # Ищем файл в БД
            conn = sqlite3.connect('files.db')
            cursor = conn.cursor()
            cursor.execute('SELECT path FROM files WHERE id = ?', (file_id,))
            row = cursor.fetchone()
            
            if not row:
                conn.close()
                return False
                
            file_path = row[0]
            
            # Удаляем файл с диска
            if os.path.exists(file_path):
                os.remove(file_path)
                
            # Удаляем из БД
            cursor.execute('DELETE FROM files WHERE id = ?', (file_id,))
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"Ошибка удаления файла: {e}")
            return False
    
    def get_file_path(self, file_id: str) -> str:
        """Получить путь к файлу"""
        try:
            conn = sqlite3.connect('files.db')
            cursor = conn.cursor()
            cursor.execute('SELECT path FROM files WHERE id = ?', (file_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return row[0]
            return ""
        except Exception as e:
            print(f"Ошибка получения пути к файлу: {e}")
            return ""
    
    def get_file_by_id(self, file_id: str) -> Optional[FileModel]:
        """Получить информацию о файле по ID"""
        try:
            conn = sqlite3.connect('files.db')
            cursor = conn.cursor()
            cursor.execute('SELECT id, name, path, size, type, created_at, updated_at FROM files WHERE id = ?', (file_id,))
            row = cursor.fetchone()
            conn.close()
            
            if not row:
                return None
                
            return FileModel(
                id=row[0],
                name=row[1],
                path=row[2],
                size=row[3],
                type=row[4],
                created_at=datetime.fromisoformat(row[5]),
                updated_at=datetime.fromisoformat(row[6]) if row[6] else None
            )
        except Exception as e:
            print(f"Ошибка получения информации о файле: {e}")
            return None