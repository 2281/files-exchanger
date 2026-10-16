"""
Service for file operations

Правила доступа:
- владелец видит и изменяет свои файлы и папки;
- файл или папку с пометкой «видна всем» (и все содержимое такой папки) видят все пользователи,
  но изменять (загружать, создавать, удалять, менять видимость) может только владелец.
"""

from src.models.file_model import FileModel
from src.config.settings import STORAGE_PATH
from src.db import connect
import os
import shutil
import uuid
from datetime import datetime
from typing import List, Optional

_SELECT = '''
    SELECT f.id, f.name, f.path, f.size, f.type, f.owner_id, f.parent_id, f.is_public,
           f.created_at, f.updated_at, u.email AS owner_email
    FROM files f JOIN users u ON u.id = f.owner_id
'''
_ORDER = ' ORDER BY f.type DESC, f.name COLLATE NOCASE'  # сначала папки

def validate_name(name: str) -> str:
    """Проверить имя файла/папки: без путей и служебных имен"""
    name = (name or "").strip()
    if not name or name in (".", "..") or os.path.basename(name) != name or "/" in name or "\\" in name:
        raise ValueError(f"Недопустимое имя: '{name}'")
    return name

def _row_to_model(row, viewer_id: str) -> FileModel:
    """Преобразовать строку БД в модель файла с учетом того, кто смотрит"""
    return FileModel(
        id=row['id'],
        name=row['name'],
        path=row['path'],
        owner_id=row['owner_id'],
        owner_email=row['owner_email'],
        parent_id=row['parent_id'],
        size=row['size'],
        type=row['type'],
        is_public=bool(row['is_public']),
        is_owner=row['owner_id'] == viewer_id,
        created_at=datetime.fromisoformat(row['created_at']),
        updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None
    )

class FileService:
    """Сервис для работы с файлами"""

    def __init__(self):
        self.storage_path = STORAGE_PATH
        os.makedirs(self.storage_path, exist_ok=True)

    def user_root(self, user_id: str) -> str:
        """Корневая папка пользователя на диске"""
        path = os.path.join(self.storage_path, user_id)
        os.makedirs(path, exist_ok=True)
        return path

    def _select(self, where: str, params: tuple, viewer_id: str) -> List[FileModel]:
        with connect() as conn:
            rows = conn.execute(_SELECT + ' WHERE ' + where + _ORDER, params).fetchall()
        return [_row_to_model(row, viewer_id) for row in rows]

    def get_file(self, file_id: str, viewer_id: str) -> Optional[FileModel]:
        """Получить файл по ID без проверки доступа"""
        files = self._select('f.id = ?', (file_id,), viewer_id)
        return files[0] if files else None

    def is_shared(self, file_id: str) -> bool:
        """Виден ли объект всем: он сам или одна из папок над ним помечены «видна всем»"""
        with connect() as conn:
            row = conn.execute('''
                WITH RECURSIVE chain(id, parent_id, is_public) AS (
                    SELECT id, parent_id, is_public FROM files WHERE id = ?
                    UNION ALL
                    SELECT f.id, f.parent_id, f.is_public FROM files f JOIN chain c ON f.id = c.parent_id
                )
                SELECT MAX(is_public) AS shared FROM chain
            ''', (file_id,)).fetchone()
        return bool(row['shared'])

    def can_read(self, file: FileModel, user_id: str) -> bool:
        return file.owner_id == user_id or self.is_shared(file.id)

    def list_root(self, user_id: str) -> List[FileModel]:
        """Корень пользователя: его файлы верхнего уровня и общие файлы других пользователей.

        Общий объект показывается в корне, только если он не виден через общую папку выше —
        иначе он доступен внутри этой папки.
        """
        own = self._select('f.owner_id = ? AND f.parent_id IS NULL', (user_id,), user_id)
        shared = [
            f for f in self._select('f.owner_id != ? AND f.is_public = 1', (user_id,), user_id)
            if f.parent_id is None or not self.is_shared(f.parent_id)
        ]
        return own + shared

    def list_children(self, folder: FileModel, viewer_id: str) -> List[FileModel]:
        """Прямое содержимое папки (доступ к самой папке проверяется вызывающим кодом)"""
        return self._select('f.parent_id = ?', (folder.id,), viewer_id)

    def readable_parent_id(self, file: FileModel, user_id: str) -> Optional[str]:
        """ID родительской папки, если она доступна пользователю"""
        if not file.parent_id:
            return None
        parent = self.get_file(file.parent_id, user_id)
        return parent.id if parent and self.can_read(parent, user_id) else None

    def create_file_info(self, name: str, path: str, size: int, type: str,
                         owner_id: str, parent_id: Optional[str] = None) -> FileModel:
        """Создать запись о файле или папке"""
        file_id = str(uuid.uuid4())
        now = datetime.now().replace(microsecond=0).isoformat()
        with connect() as conn:
            conn.execute('''
                INSERT INTO files (id, name, path, size, type, owner_id, parent_id, is_public, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, ?)
            ''', (file_id, name, path, size, type, owner_id, parent_id, now, now))
        return self.get_file(file_id, owner_id)

    def create_folder(self, folder_name: str, owner_id: str, parent: Optional[FileModel] = None) -> FileModel:
        """Создать папку в корне пользователя или внутри parent"""
        folder_name = validate_name(folder_name)
        directory = parent.path if parent else self.user_root(owner_id)
        folder_path = os.path.join(directory, folder_name)
        if os.path.exists(folder_path):
            raise FileExistsError(f"Папка или файл '{folder_name}' уже существует")
        os.makedirs(folder_path)
        return self.create_file_info(folder_name, folder_path, 0, 'folder', owner_id, parent.id if parent else None)

    def set_public(self, file: FileModel, is_public: bool) -> FileModel:
        """Пометить файл или папку как видимые всем или только владельцу"""
        with connect() as conn:
            conn.execute(
                'UPDATE files SET is_public = ?, updated_at = ? WHERE id = ?',
                (int(is_public), datetime.now().replace(microsecond=0).isoformat(), file.id)
            )
        return self.get_file(file.id, file.owner_id)

    def delete_file(self, file: FileModel):
        """Удалить файл или папку со всем содержимым.

        Записи вложенных объектов и ссылки на них удаляются каскадно (ON DELETE CASCADE).
        """
        if file.type == 'folder':
            if os.path.exists(file.path):
                shutil.rmtree(file.path)
        elif os.path.exists(file.path):
            os.remove(file.path)

        with connect() as conn:
            conn.execute('DELETE FROM files WHERE id = ?', (file.id,))
