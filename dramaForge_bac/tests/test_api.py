import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.models  # noqa: F401
from app.api.v2 import assets
from app.core.database import Base
from app.models.character import Character, CharacterRole
from app.models.project import Project
from app.models.scene import SceneLocation
from app.models.user import User


def test_test_suite_is_configured():
    assert True


@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_global_assets_include_characters_and_scenes(db_session):
    user = User(username="owner")
    db_session.add(user)
    await db_session.flush()

    project = Project(user_id=user.id, title="Demo")
    db_session.add(project)
    await db_session.flush()

    db_session.add(
        Character(
            project_id=project.id,
            name="Hero",
            role=CharacterRole.PROTAGONIST,
            reference_images=["/hero.png"],
        )
    )
    db_session.add(
        SceneLocation(
            project_id=project.id,
            name="Bridge",
            reference_images=["/bridge.png"],
        )
    )
    await db_session.flush()

    result = await assets.list_global_assets(
        user=user,
        skip=0,
        limit=50,
        role=None,
        db=db_session,
    )

    assert {(item.type, item.name, item.uid) for item in result} == {
        ("character", "Hero", "character:1"),
        ("scene", "Bridge", "scene:1"),
    }
