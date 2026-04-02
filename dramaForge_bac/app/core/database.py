"""
DramaForge v2.0 — Database Engine & Session Management
=======================================================

Provides async SQLAlchemy 2.0 engine, session factory, Base class,
dependency injection helper, and auto-table-creation utility.

Usage:
    from app.core.database import get_db, init_db, Base

    # FastAPI dependency injection
    @router.get("/items")
    async def list_items(db: AsyncSession = Depends(get_db)):
        ...

    # On startup — create all tables
    await init_db()
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

# ──────────── Async Engine ────────────────────────────────────────
# `echo=True` when debug for SQL logging; pool settings for SQLite
async_engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    # SQLite does not support pool_size / max_overflow, but the
    # driver (aiosqlite) ignores them silently.  For Postgres you
    # would tune these.
    future=True,
)

# ──────────── Session Factory ─────────────────────────────────────
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ──────────── Declarative Base ────────────────────────────────────
class Base(DeclarativeBase):
    """
    Base class for all ORM models.

    Using the SQLAlchemy 2.0 ``DeclarativeBase`` style so that
    sub-classes can leverage ``Mapped[]`` annotations.
    """
    pass


# ──────────── Dependency Injection ────────────────────────────────
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that yields an async database session.

    The session is automatically closed after the request finishes,
    even if an exception occurs.

    Example::

        @router.get("/projects")
        async def list_projects(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(Project))
            return result.scalars().all()
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ──────────── Auto-create Tables ──────────────────────────────────
async def init_db() -> None:
    """
    Create all tables that inherit from ``Base``.

    Call this during application startup (e.g. in a ``@app.on_event("startup")``
    or Lifespan handler).

    **Important**: All model modules must be imported *before* calling this
    function so that ``Base.metadata`` contains their table definitions.
    """
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Dispose the engine connection pool. Call on shutdown."""
    await async_engine.dispose()
