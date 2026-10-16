"""
Отправка email
"""

import smtplib
import ssl
from email.message import EmailMessage
from src.config import settings

def send_email(to: str, subject: str, body: str):
    """Отправить письмо. Без настроенного SMTP письмо печатается в консоль сервера.

    При ошибке отправки выбрасывает smtplib.SMTPException или OSError.
    """
    if not settings.SMTP_HOST:
        print(f"\n===== EMAIL (SMTP не настроен) =====\nКому: {to}\nТема: {subject}\n\n{body}\n=====\n", flush=True)
        return

    message = EmailMessage()
    message["From"] = settings.SMTP_FROM
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body)

    context = ssl.create_default_context()
    if settings.SMTP_USE_SSL:
        server = smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, context=context, timeout=15)
    else:
        server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15)

    with server:
        if not settings.SMTP_USE_SSL and settings.SMTP_STARTTLS:
            server.starttls(context=context)
        if settings.SMTP_USER:
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.send_message(message)
