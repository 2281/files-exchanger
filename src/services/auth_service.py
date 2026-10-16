"""
Сервис аутентификации: выдача пароля по email, вход, сессии
"""

import hashlib
import hmac
import re
import secrets
import threading
import uuid
from datetime import datetime, timedelta
from typing import Optional
from src.config import settings
from src.db import connect
from src.models.auth_model import User
from src.services import email_service

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# Символы пароля без легко путаемых (0/O, 1/l/I)
PASSWORD_ALPHABET = "abcdefghijkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789"
PASSWORD_LENGTH = 12

# Параметры scrypt (около 16 МБ памяти на одну проверку)
SCRYPT_N, SCRYPT_R, SCRYPT_P = 2 ** 14, 8, 1

class AuthError(Exception):
    """Неверные учетные данные"""

class RateLimitError(Exception):
    """Слишком частые запросы"""

def normalize_email(email: str) -> str:
    """Привести email к нижнему регистру и проверить формат"""
    email = (email or "").strip().lower()
    if len(email) > 254 or not EMAIL_RE.match(email):
        raise ValueError("Некорректный email")
    return email

def generate_password() -> str:
    return ''.join(secrets.choice(PASSWORD_ALPHABET) for _ in range(PASSWORD_LENGTH))

def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=SCRYPT_N, r=SCRYPT_R, p=SCRYPT_P)
    return f"scrypt${salt.hex()}${digest.hex()}"

def verify_password(password: str, stored_hash: str) -> bool:
    try:
        algorithm, salt_hex, digest_hex = stored_hash.split("$")
    except ValueError:
        return False
    if algorithm != "scrypt":
        return False
    digest = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt_hex), n=SCRYPT_N, r=SCRYPT_R, p=SCRYPT_P)
    return hmac.compare_digest(digest.hex(), digest_hex)

# Хеш для проверки, когда пользователя нет: время ответа не выдает существование email
_DUMMY_HASH = hash_password(generate_password())

def token_hash(token: str) -> str:
    """Хеш токена сессии или ссылки — в БД хранится только он"""
    return hashlib.sha256(token.encode()).hexdigest()

def _now() -> datetime:
    return datetime.now().replace(microsecond=0)

# Счетчики неудачных входов в памяти процесса: email -> (число неудач, заблокирован до)
_failed_logins: dict[str, tuple[int, Optional[datetime]]] = {}
_failed_logins_lock = threading.Lock()

def _check_login_lock(email: str):
    with _failed_logins_lock:
        _, locked_until = _failed_logins.get(email, (0, None))
    if locked_until and locked_until > _now():
        raise RateLimitError("Слишком много неудачных попыток входа. Попробуйте через несколько минут")

def _register_login_failure(email: str):
    with _failed_logins_lock:
        count, _ = _failed_logins.get(email, (0, None))
        count += 1
        if count >= settings.LOGIN_MAX_ATTEMPTS:
            _failed_logins[email] = (0, _now() + timedelta(minutes=settings.LOGIN_LOCK_MINUTES))
        else:
            _failed_logins[email] = (count, None)

def request_password(email: str, login_url: str) -> str:
    """Сгенерировать пароль и отправить его на email. Новый пользователь создается автоматически.

    Пароль сохраняется только после успешной отправки письма. Возвращает нормализованный email.
    """
    email = normalize_email(email)
    now = _now()

    with connect() as conn:
        row = conn.execute('SELECT id, password_requested_at FROM users WHERE email = ?', (email,)).fetchone()

    if row and row['password_requested_at']:
        requested_at = datetime.fromisoformat(row['password_requested_at'])
        if now - requested_at < timedelta(seconds=settings.PASSWORD_REQUEST_INTERVAL_SECONDS):
            raise RateLimitError("Пароль уже был отправлен недавно. Повторите запрос через минуту")

    password = generate_password()
    email_service.send_email(
        email,
        "Пароль для входа в файлообменник",
        f"Здравствуйте!\n\n"
        f"Для входа в файлообменник используйте:\n"
        f"  Логин: {email}\n"
        f"  Пароль: {password}\n\n"
        f"Страница входа: {login_url}\n\n"
        f"Если вы не запрашивали пароль, просто проигнорируйте это письмо.\n"
    )

    with connect() as conn:
        if row:
            conn.execute(
                'UPDATE users SET password_hash = ?, password_requested_at = ? WHERE id = ?',
                (hash_password(password), now.isoformat(), row['id'])
            )
        else:
            conn.execute(
                'INSERT INTO users (id, email, password_hash, password_requested_at, created_at) VALUES (?, ?, ?, ?, ?)',
                (str(uuid.uuid4()), email, hash_password(password), now.isoformat(), now.isoformat())
            )
    return email

def login(email: str, password: str) -> tuple[str, User]:
    """Проверить email и пароль, создать сессию. Возвращает токен сессии и пользователя."""
    try:
        email = normalize_email(email)
    except ValueError:
        raise AuthError("Неверный email или пароль")

    _check_login_lock(email)

    with connect() as conn:
        row = conn.execute('SELECT id, email, password_hash FROM users WHERE email = ?', (email,)).fetchone()

    if not row or not row['password_hash']:
        verify_password(password, _DUMMY_HASH)
        _register_login_failure(email)
        raise AuthError("Неверный email или пароль")
    if not verify_password(password, row['password_hash']):
        _register_login_failure(email)
        raise AuthError("Неверный email или пароль")

    with _failed_logins_lock:
        _failed_logins.pop(email, None)

    token = secrets.token_urlsafe(32)
    now = _now()
    with connect() as conn:
        conn.execute('DELETE FROM sessions WHERE expires_at <= ?', (now.isoformat(),))
        conn.execute(
            'INSERT INTO sessions (token_hash, user_id, expires_at) VALUES (?, ?, ?)',
            (token_hash(token), row['id'], (now + timedelta(hours=settings.SESSION_TTL_HOURS)).isoformat())
        )
    return token, User(id=row['id'], email=row['email'])

def get_user_by_session(token: str) -> Optional[User]:
    """Пользователь по токену действующей сессии"""
    with connect() as conn:
        row = conn.execute('''
            SELECT u.id, u.email FROM sessions s JOIN users u ON u.id = s.user_id
            WHERE s.token_hash = ? AND s.expires_at > ?
        ''', (token_hash(token), _now().isoformat())).fetchone()
    return User(id=row['id'], email=row['email']) if row else None

def logout(token: str):
    with connect() as conn:
        conn.execute('DELETE FROM sessions WHERE token_hash = ?', (token_hash(token),))
