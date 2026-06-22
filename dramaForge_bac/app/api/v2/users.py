"""
DramaForge v2.0 - User Authentication API
==========================================
Email verification code login, token refresh, and user profile endpoints.
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.core.security import (
    CurrentUser,
    DbSession,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.models.user import User, UserStatus
from app.services.email_verification_service import (
    LOGIN_PURPOSE,
    issue_email_code,
    normalize_email,
    verify_email_code,
)

router = APIRouter(prefix="/user", tags=["User"])

EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
CODE_PATTERN = r"^\d{4,10}$"


class SendEmailCodeRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=255, pattern=EMAIL_PATTERN)


class SendEmailCodeResponse(BaseModel):
    sent: bool = True
    expires_in: int
    resend_after: int


class RegisterRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=255, pattern=EMAIL_PATTERN)
    code: str = Field(..., pattern=CODE_PATTERN, description="Email verification code")
    nickname: str | None = Field(default=None, max_length=128, description="Display name")


class LoginRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=255, pattern=EMAIL_PATTERN)
    code: str = Field(..., pattern=CODE_PATTERN, description="Email verification code")


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., description="Refresh token")


class AuthTokens(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    id: int
    email: str | None = None
    phone: str | None = None
    nickname: str | None = None
    avatar_url: str | None = None
    status: str
    created_at: datetime
    credits: int = 0
    plan_code: str = "free"

    model_config = {"from_attributes": True}


def _tokens_for_user(user: User) -> AuthTokens:
    return AuthTokens(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
        expires_in=60 * 24 * 60,
    )


@router.post("/send-login-code", response_model=SendEmailCodeResponse)
async def send_login_code(
    request: SendEmailCodeRequest,
    db: DbSession,
):
    """Send a one-time email code for passwordless login or registration."""
    from app.core.config import settings

    await issue_email_code(db, request.email, LOGIN_PURPOSE)
    return SendEmailCodeResponse(
        expires_in=settings.email_code_expire_minutes * 60,
        resend_after=settings.email_code_resend_seconds,
    )


@router.post("/register", response_model=AuthTokens, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    db: DbSession,
):
    """Register a new email user after verifying the email code."""
    email = normalize_email(request.email)
    existing = await db.execute(select(User).where(User.email == email))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    try:
        await verify_email_code(db, email, request.code, LOGIN_PURPOSE)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    user = User(
        email=email,
        password_hash=None,
        nickname=request.nickname or email,
    )
    db.add(user)
    await db.flush()

    return _tokens_for_user(user)


@router.post("/login", response_model=AuthTokens)
async def login(
    request: LoginRequest,
    db: DbSession,
):
    """Login with an email verification code. Create the account if needed."""
    email = normalize_email(request.email)

    try:
        await verify_email_code(db, email, request.code, LOGIN_PURPOSE)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        user = User(
            email=email,
            password_hash=None,
            nickname=email,
        )
        db.add(user)
        await db.flush()

    if user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is disabled",
        )

    return _tokens_for_user(user)


@router.post("/refresh", response_model=AuthTokens)
async def refresh_token(
    request: RefreshTokenRequest,
    db: DbSession,
):
    """Refresh an access token using a valid refresh token."""
    payload = decode_token(request.refresh_token)

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()

    if not user or user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or disabled",
        )

    return _tokens_for_user(user)


@router.post("/logout")
async def logout(user: CurrentUser):
    """Logout. The client clears stored tokens."""
    return {"logged_out": True}


@router.get("/me", response_model=UserResponse)
async def get_me(user: CurrentUser, db: DbSession):
    """Get current user information, including billing summary."""
    from app.services.billing_service import get_balance, get_user_plan_code, grant_daily_credits_if_needed

    await grant_daily_credits_if_needed(db, user.id)
    await db.commit()

    credits = await get_balance(db, user.id)
    plan_code = await get_user_plan_code(db, user.id)

    return UserResponse(
        id=user.id,
        email=user.email,
        phone=user.phone,
        nickname=user.nickname,
        avatar_url=user.avatar_url,
        status=user.status.value,
        created_at=user.created_at,
        credits=credits,
        plan_code=plan_code,
    )
