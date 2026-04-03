"""
DramaForge v2.0 — User Authentication API
==========================================
Registration, login, token refresh, and user profile endpoints.
Adapted from IAA project patterns.
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select

from app.core.security import (
    CurrentUser,
    DbSession,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import User, UserStatus

router = APIRouter(prefix="/user", tags=["User"])


# ═══════════════════════════════════════════════════════════════════
# Request / Response schemas
# ═══════════════════════════════════════════════════════════════════

class RegisterRequest(BaseModel):
    email: str | None = Field(default=None, description="Email address")
    phone: str | None = Field(default=None, min_length=6, max_length=20, description="Phone number")
    password: str = Field(..., min_length=6, max_length=128, description="Password")
    nickname: str | None = Field(default=None, max_length=128, description="Display name")


class LoginRequest(BaseModel):
    email: str | None = Field(default=None, description="Email address")
    phone: str | None = Field(default=None, description="Phone number")
    password: str = Field(..., description="Password")


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

    model_config = {"from_attributes": True}


# ═══════════════════════════════════════════════════════════════════
# Endpoints
# ═══════════════════════════════════════════════════════════════════

@router.post("/register", response_model=AuthTokens, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    db: DbSession,
):
    """Register a new user and return JWT tokens."""
    if not request.email and not request.phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either email or phone must be provided",
        )

    # Check for duplicates
    if request.email:
        existing = await db.execute(select(User).where(User.email == request.email))
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )

    if request.phone:
        existing = await db.execute(select(User).where(User.phone == request.phone))
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Phone already registered",
            )

    # Create user
    user = User(
        email=request.email,
        phone=request.phone,
        password_hash=hash_password(request.password),
        nickname=request.nickname or (request.email or request.phone),
    )
    db.add(user)
    await db.flush()

    # Generate tokens
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)

    return AuthTokens(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=60 * 24 * 60,  # 1 day in seconds
    )


@router.post("/login", response_model=AuthTokens)
async def login(
    request: LoginRequest,
    db: DbSession,
):
    """Login with email/phone and password."""
    if not request.email and not request.phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either email or phone must be provided",
        )

    # Find user
    if request.email:
        result = await db.execute(select(User).where(User.email == request.email))
    else:
        result = await db.execute(select(User).where(User.phone == request.phone))

    user = result.scalar_one_or_none()

    if not user or not user.password_hash or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    if user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is disabled",
        )

    # Generate tokens
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)

    return AuthTokens(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=60 * 24 * 60,
    )


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

    access_token = create_access_token(user.id)
    new_refresh_token = create_refresh_token(user.id)

    return AuthTokens(
        access_token=access_token,
        refresh_token=new_refresh_token,
        expires_in=60 * 24 * 60,
    )


@router.post("/logout")
async def logout(user: CurrentUser):
    """Logout (client should clear tokens)."""
    return {"logged_out": True}


@router.get("/me", response_model=UserResponse)
async def get_me(user: CurrentUser):
    """Get current user information."""
    return UserResponse(
        id=user.id,
        email=user.email,
        phone=user.phone,
        nickname=user.nickname,
        avatar_url=user.avatar_url,
        status=user.status.value,
        created_at=user.created_at,
    )
