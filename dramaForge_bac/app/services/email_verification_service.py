from __future__ import annotations

import asyncio
import hashlib
import hmac
import secrets
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.user import EmailVerificationCode

LOGIN_PURPOSE = "login"


def normalize_email(email: str) -> str:
    return email.strip().lower()


def _code_hash(email: str, code: str, purpose: str) -> str:
    message = f"{normalize_email(email)}:{purpose}:{code}".encode("utf-8")
    secret = settings.jwt_secret_key.encode("utf-8")
    return hmac.new(secret, message, hashlib.sha256).hexdigest()


def _generate_code() -> str:
    length = max(4, min(settings.email_code_length, 10))
    start = 10 ** (length - 1)
    end = (10 ** length) - 1
    return str(secrets.randbelow(end - start + 1) + start)


async def issue_email_code(
    db: AsyncSession,
    email: str,
    purpose: str = LOGIN_PURPOSE,
) -> None:
    normalized_email = normalize_email(email)
    now = datetime.utcnow()

    latest = await db.execute(
        select(EmailVerificationCode)
        .where(
            EmailVerificationCode.email == normalized_email,
            EmailVerificationCode.purpose == purpose,
        )
        .order_by(EmailVerificationCode.created_at.desc())
        .limit(1)
    )
    latest_code = latest.scalar_one_or_none()
    if latest_code and latest_code.created_at:
        elapsed = (now - latest_code.created_at).total_seconds()
        if elapsed < settings.email_code_resend_seconds:
            wait_seconds = int(settings.email_code_resend_seconds - elapsed)
            raise ValueError(f"验证码发送过于频繁，请 {wait_seconds} 秒后再试")

    code = _generate_code()
    record = EmailVerificationCode(
        email=normalized_email,
        purpose=purpose,
        code_hash=_code_hash(normalized_email, code, purpose),
        expires_at=now + timedelta(minutes=settings.email_code_expire_minutes),
    )
    db.add(record)
    await db.flush()

    await send_email_code(normalized_email, code)


async def verify_email_code(
    db: AsyncSession,
    email: str,
    code: str,
    purpose: str = LOGIN_PURPOSE,
) -> None:
    normalized_email = normalize_email(email)
    now = datetime.utcnow()
    result = await db.execute(
        select(EmailVerificationCode)
        .where(
            EmailVerificationCode.email == normalized_email,
            EmailVerificationCode.purpose == purpose,
            EmailVerificationCode.used_at.is_(None),
            EmailVerificationCode.expires_at > now,
        )
        .order_by(EmailVerificationCode.created_at.desc())
        .limit(1)
    )
    record = result.scalar_one_or_none()
    if not record:
        raise ValueError("验证码不存在或已过期")

    if record.attempts >= settings.email_code_max_attempts:
        raise ValueError("验证码尝试次数过多，请重新获取")

    record.attempts += 1
    expected_hash = _code_hash(normalized_email, code.strip(), purpose)
    if not hmac.compare_digest(record.code_hash, expected_hash):
        await db.flush()
        raise ValueError("验证码错误")

    record.used_at = now
    await db.flush()


async def send_email_code(email: str, code: str) -> None:
    if not settings.smtp_host:
        if settings.debug:
            logger.warning(f"Email verification code for {email}: {code}")
            return
        raise RuntimeError("SMTP is not configured")

    await asyncio.to_thread(_send_email_code_sync, email, code)


def _send_email_code_sync(email: str, code: str) -> None:
    sender = settings.smtp_from or settings.smtp_username
    if not sender:
        raise RuntimeError("SMTP sender is not configured")

    subject = "DramaForge 登录验证码"
    body = (
        f"您的 DramaForge 登录验证码是：{code}\n\n"
        f"验证码 {settings.email_code_expire_minutes} 分钟内有效。"
        "如果这不是您本人操作，请忽略此邮件。"
    )
    message = MIMEText(body, "plain", "utf-8")
    message["Subject"] = subject
    message["From"] = sender
    message["To"] = email

    if settings.smtp_use_ssl:
        smtp = smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, timeout=10)
    else:
        smtp = smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10)

    with smtp:
        if settings.smtp_use_tls and not settings.smtp_use_ssl:
            smtp.starttls()
        if settings.smtp_username:
            smtp.login(settings.smtp_username, settings.smtp_password)
        smtp.sendmail(sender, [email], message.as_string())
