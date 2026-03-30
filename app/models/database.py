"""
DramaForge - Database Models
SQLAlchemy ORM models for projects, scripts, storyboards, etc.
"""

import enum
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, relationship, sessionmaker

from config import settings


class Base(DeclarativeBase):
    pass


# ==================== Enums ====================

class ProjectStatus(str, enum.Enum):
    DRAFT = "draft"                 # 草稿
    SCRIPT_READY = "script_ready"   # 剧本就绪
    STORYBOARD_READY = "storyboard_ready"  # 分镜就绪
    GENERATING = "generating"       # 生成中
    COMPLETED = "completed"         # 已完成
    FAILED = "failed"               # 失败


class StoryboardStatus(str, enum.Enum):
    PENDING = "pending"             # 待审核
    APPROVED = "approved"           # 已审核通过
    REJECTED = "rejected"           # 已驳回
    IMAGE_GENERATING = "image_generating"  # 图片生成中
    IMAGE_READY = "image_ready"     # 图片已就绪
    AUDIO_GENERATING = "audio_generating"  # 音频生成中
    AUDIO_READY = "audio_ready"     # 音频已就绪
    COMPLETED = "completed"         # 完成


class DramaGenre(str, enum.Enum):
    ROMANCE = "romance"         # 甜宠
    SUSPENSE = "suspense"       # 悬疑
    COMEDY = "comedy"           # 搞笑
    FANTASY = "fantasy"         # 奇幻
    URBAN = "urban"             # 都市
    HISTORICAL = "historical"   # 古装
    HORROR = "horror"           # 恐怖
    OTHER = "other"             # 其他


# ==================== Models ====================

class Project(Base):
    """短剧项目"""
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False, comment="项目标题")
    description = Column(Text, nullable=True, comment="项目描述")
    genre = Column(Enum(DramaGenre), default=DramaGenre.OTHER, comment="剧种类型")
    status = Column(Enum(ProjectStatus), default=ProjectStatus.DRAFT, comment="项目状态")
    target_duration = Column(Integer, default=60, comment="目标时长(秒)")
    target_episodes = Column(Integer, default=1, comment="目标集数")
    style_prompt = Column(Text, nullable=True, comment="画面风格描述")
    llm_provider = Column(String(50), nullable=True, comment="使用的LLM")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    scripts = relationship("Script", back_populates="project", cascade="all, delete-orphan")
    characters = relationship("Character", back_populates="project", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Project(id={self.id}, title='{self.title}', status={self.status})>"


class Character(Base):
    """角色设定"""
    __tablename__ = "characters"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    name = Column(String(100), nullable=False, comment="角色名")
    description = Column(Text, nullable=True, comment="角色描述")
    appearance = Column(Text, nullable=True, comment="外貌描述(用于图片生成一致性)")
    voice = Column(String(100), nullable=True, comment="配音声色")

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="characters")

    def __repr__(self):
        return f"<Character(id={self.id}, name='{self.name}')>"


class Script(Base):
    """剧本"""
    __tablename__ = "scripts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    episode = Column(Integer, default=1, comment="集数")
    title = Column(String(200), nullable=True, comment="本集标题")
    content = Column(Text, nullable=False, comment="剧本内容")
    outline = Column(Text, nullable=True, comment="大纲")
    is_approved = Column(Integer, default=0, comment="是否审核通过 0-否 1-是")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="scripts")
    storyboards = relationship("Storyboard", back_populates="script", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Script(id={self.id}, episode={self.episode})>"


class Storyboard(Base):
    """分镜"""
    __tablename__ = "storyboards"

    id = Column(Integer, primary_key=True, autoincrement=True)
    script_id = Column(Integer, ForeignKey("scripts.id"), nullable=False)
    sequence = Column(Integer, nullable=False, comment="分镜序号")
    scene_description = Column(Text, nullable=False, comment="场景描述")
    narration = Column(Text, nullable=True, comment="旁白文本")
    dialogue = Column(Text, nullable=True, comment="对白文本")
    image_prompt = Column(Text, nullable=True, comment="图片生成提示词")
    duration = Column(Float, default=5.0, comment="预计时长(秒)")
    transition = Column(String(50), default="crossfade", comment="转场效果")
    status = Column(Enum(StoryboardStatus), default=StoryboardStatus.PENDING, comment="状态")

    # Generated assets
    image_path = Column(String(500), nullable=True, comment="生成的图片路径")
    audio_path = Column(String(500), nullable=True, comment="生成的音频路径")
    audio_duration = Column(Float, nullable=True, comment="实际音频时长(秒)")
    subtitle_path = Column(String(500), nullable=True, comment="字幕文件路径")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    script = relationship("Script", back_populates="storyboards")

    def __repr__(self):
        return f"<Storyboard(id={self.id}, seq={self.sequence}, status={self.status})>"


class GeneratedVideo(Base):
    """生成的视频"""
    __tablename__ = "generated_videos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    script_id = Column(Integer, ForeignKey("scripts.id"), nullable=False)
    video_path = Column(String(500), nullable=True, comment="视频文件路径")
    duration = Column(Float, nullable=True, comment="视频时长(秒)")
    resolution = Column(String(20), default="1080x1920", comment="分辨率")
    status = Column(String(20), default="pending", comment="状态")

    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<GeneratedVideo(id={self.id}, status={self.status})>"


# ==================== Database Engine ====================

engine = create_engine(settings.database_url, echo=settings.debug)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize database - create all tables."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency for FastAPI - yields a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
