"""
Подключение к базе данных SQLite и схема таблиц
"""

import sqlite3
from contextlib import contextmanager
from src.config.settings import DB_PATH

SCHEMA = '''
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT,
    password_requested_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS sessions (
    token_hash TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    expires_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS files (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    path TEXT NOT NULL,
    size INTEGER NOT NULL,
    type TEXT NOT NULL,
    owner_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    parent_id TEXT REFERENCES files(id) ON DELETE CASCADE,
    is_public INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_files_parent ON files(parent_id);
CREATE INDEX IF NOT EXISTS idx_files_owner ON files(owner_id);

CREATE TABLE IF NOT EXISTS share_links (
    id TEXT PRIMARY KEY,
    token_hash TEXT NOT NULL UNIQUE,
    file_id TEXT NOT NULL REFERENCES files(id) ON DELETE CASCADE,
    created_by TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP NOT NULL,
    expires_at TIMESTAMP NOT NULL
);
'''

@contextmanager
def connect():
    """Открыть соединение; изменения фиксируются при выходе без ошибок"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

def init_db():
    """Создать таблицы при необходимости"""
    with connect() as conn:
        columns = {row['name'] for row in conn.execute('PRAGMA table_info(files)')}
        if columns and 'owner_id' not in columns:
            raise RuntimeError(
                f"База данных {DB_PATH} создана старой версией приложения (без пользователей). "
                f"Удалите {DB_PATH} и содержимое папки storage, затем запустите приложение снова."
            )
        conn.executescript(SCHEMA)
