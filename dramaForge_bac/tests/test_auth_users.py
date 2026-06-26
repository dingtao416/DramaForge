import pytest
import pytest_asyncio
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.models  # noqa: F401
from app.api.v2 import users
from app.core.database import Base
from app.models.user import User


@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest.fixture
def accept_verification_code(monkeypatch):
    async def verify_code(db, email, code, purpose):
        assert code == "123456"

    monkeypatch.setattr(users, "verify_email_code", verify_code)


@pytest.mark.asyncio
async def test_register_binds_username_email_and_password(db_session, accept_verification_code):
    tokens = await users.register(
        users.RegisterRequest(
            username="Creator01",
            email="Creator@example.com",
            password="password123",
            code="123456",
        ),
        db_session,
    )

    result = await db_session.execute(select(User).where(User.email == "creator@example.com"))
    user = result.scalar_one()

    assert tokens.access_token
    assert user.username == "creator01"
    assert user.password_hash
    assert user.password_hash != "password123"


@pytest.mark.asyncio
async def test_login_accepts_username_or_email_with_password(db_session, accept_verification_code):
    await users.register(
        users.RegisterRequest(
            username="Creator01",
            email="Creator@example.com",
            password="password123",
            code="123456",
        ),
        db_session,
    )

    username_tokens = await users.login(
        users.LoginRequest(account="Creator01", password="password123"),
        db_session,
    )
    email_tokens = await users.login(
        users.LoginRequest(account="creator@example.com", password="password123"),
        db_session,
    )

    assert username_tokens.access_token
    assert email_tokens.access_token


@pytest.mark.asyncio
async def test_login_missing_account_does_not_register(db_session):
    with pytest.raises(HTTPException) as exc_info:
        await users.login(
            users.LoginRequest(account="missing-user", password="password123"),
            db_session,
        )

    result = await db_session.execute(select(User))

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "账号不存在，请先注册"
    assert result.scalars().all() == []
