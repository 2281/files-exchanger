"""
Сервис временных ссылок на файлы и папки
"""

import secrets
import uuid
from datetime import datetime, timedelta
from typing import List, Optional
from src.db import connect
from src.models.file_model import LinkModel
from src.services.auth_service import token_hash

def _now() -> datetime:
    return datetime.now().replace(microsecond=0)

def _row_to_model(row) -> LinkModel:
    return LinkModel(
        id=row['id'],
        file_id=row['file_id'],
        file_name=row['file_name'],
        file_type=row['file_type'],
        created_at=datetime.fromisoformat(row['created_at']),
        expires_at=datetime.fromisoformat(row['expires_at'])
    )

_SELECT = '''
    SELECT l.id, l.file_id, l.created_at, l.expires_at, f.name AS file_name, f.type AS file_type
    FROM share_links l JOIN files f ON f.id = l.file_id
'''

def create_link(file_id: str, user_id: str, expires_in_hours: int) -> tuple[str, LinkModel]:
    """Создать ссылку. Возвращает токен (в БД хранится только его хеш) и описание ссылки."""
    token = secrets.token_urlsafe(32)
    link_id = str(uuid.uuid4())
    now = _now()
    with connect() as conn:
        conn.execute('DELETE FROM share_links WHERE expires_at <= ?', (now.isoformat(),))
        conn.execute('''
            INSERT INTO share_links (id, token_hash, file_id, created_by, created_at, expires_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (link_id, token_hash(token), file_id, user_id, now.isoformat(),
              (now + timedelta(hours=expires_in_hours)).isoformat()))
        row = conn.execute(_SELECT + ' WHERE l.id = ?', (link_id,)).fetchone()
    return token, _row_to_model(row)

def list_links(user_id: str) -> List[LinkModel]:
    """Действующие ссылки, созданные пользователем"""
    with connect() as conn:
        rows = conn.execute(
            _SELECT + ' WHERE l.created_by = ? AND l.expires_at > ? ORDER BY l.expires_at',
            (user_id, _now().isoformat())
        ).fetchall()
    return [_row_to_model(row) for row in rows]

def delete_link(link_id: str, user_id: str) -> bool:
    """Отозвать ссылку (только ее создатель)"""
    with connect() as conn:
        cursor = conn.execute('DELETE FROM share_links WHERE id = ? AND created_by = ?', (link_id, user_id))
    return cursor.rowcount > 0

def resolve(token: str) -> Optional[tuple[str, str]]:
    """Найти действующую ссылку по токену. Возвращает (file_id, created_by)."""
    with connect() as conn:
        row = conn.execute(
            'SELECT file_id, created_by FROM share_links WHERE token_hash = ? AND expires_at > ?',
            (token_hash(token), _now().isoformat())
        ).fetchone()
    return (row['file_id'], row['created_by']) if row else None
