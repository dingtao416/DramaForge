"""
DramaForge v2.0 — Episodes API
================================
Endpoints for episode management and statistics.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from pydantic import BaseModel, Field
from loguru import logger

from app.core.database import get_db
from app.models.project import Project
from app.models.script import Script
from app.models.episode import Episode
from app.models.segment import Segment
from app.models.shot import Shot
from app.schemas.episode import EpisodeOverview, EpisodeDetail
from app.ai_hub import ai_hub
from app.prompts.script_prompts import SCRIPT_STRUCTURED_SYSTEM
from app.services.user_model_resolver import user_model_resolver
from app.core.security import CurrentUser, DbSession, get_user_project
from app.core.billing_deps import require_credits

router = APIRouter()


class EpisodeRegenerateRequest(BaseModel):
    """Request to regenerate a single episode's content."""
    user_prompt: str = Field(
        default="",
        description="用户对重新生成内容的指引，为空则自动根据剧本上下文重新生成",
    )
    keep_storyboard: bool = Field(
        default=True,
        description="是否保留已有的分镜和素材数据",
    )


@router.get("/projects/{project_id}/episodes", response_model=list[EpisodeOverview])
async def list_episodes(
    project_id: int,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """List all episodes with statistics (character count, scene count, etc.)."""
    # Verify project ownership
    await get_user_project(project_id, user, db)

    # Get script for the project
    stmt = (
        select(Script)
        .where(Script.project_id == project_id)
        .options(selectinload(Script.episodes))
    )
    result = await db.execute(stmt)
    script = result.scalar_one_or_none()
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")

    episodes_data = []
    for ep in script.episodes:
        # Count segments and shots
        seg_stmt = select(Segment).where(Segment.episode_id == ep.id)
        seg_result = await db.execute(seg_stmt)
        segments = seg_result.scalars().all()

        total_shots = 0
        total_duration = 0.0
        unique_chars = set()
        unique_scenes = set()

        for seg in segments:
            shot_stmt = select(Shot).where(Shot.segment_id == seg.id)
            shot_result = await db.execute(shot_stmt)
            shots = shot_result.scalars().all()
            total_shots += len(shots)
            for shot in shots:
                if shot.duration:
                    total_duration += shot.duration
                if shot.scene_ref:
                    unique_scenes.add(shot.scene_ref)
                if shot.characters:
                    for ch in shot.characters:
                        if isinstance(ch, dict) and "char_id" in ch:
                            unique_chars.add(ch["char_id"])

        episodes_data.append(
            EpisodeOverview(
                id=ep.id,
                number=ep.number,
                title=ep.title,
                is_approved=ep.is_approved,
                character_count=len(unique_chars),
                scene_count=len(unique_scenes),
                segment_count=len(segments),
                total_duration=total_duration,
                created_at=ep.created_at,
            )
        )

    return episodes_data


@router.get("/projects/{project_id}/episodes/{episode_id}", response_model=EpisodeDetail)
async def get_episode(
    project_id: int,
    episode_id: int,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Get full episode details."""
    # Verify project ownership
    await get_user_project(project_id, user, db)

    episode = await db.get(Episode, episode_id)
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")

    # Verify it belongs to the right project
    stmt = select(Script).where(Script.id == episode.script_id)
    result = await db.execute(stmt)
    script = result.scalar_one_or_none()
    if not script or script.project_id != project_id:
        raise HTTPException(status_code=404, detail="Episode not found in this project")

    return episode


@router.post("/projects/{project_id}/episodes/{episode_id}/regenerate")
async def regenerate_episode(
    project_id: int,
    episode_id: int,
    body: EpisodeRegenerateRequest = EpisodeRegenerateRequest(),
    user: CurrentUser = None,
    db: AsyncSession = Depends(get_db),
):
    """Regenerate a single episode's content via AI, preserving downstream data."""
    # Verify project ownership
    project = await get_user_project(project_id, user, db)

    if user:
        await require_credits(db, user.id, "script_gen", description="剧集内容重新生成")
        # Commit credits immediately to release the SQLite write lock during the AI call below.
        # If the AI call fails later, credits are already spent (fail-fast billing).
        await db.commit()

    episode = await db.get(Episode, episode_id)
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")

    # Verify episode belongs to this project
    stmt = (
        select(Script)
        .where(Script.id == episode.script_id)
        .options(selectinload(Script.episodes))
    )
    result = await db.execute(stmt)
    script = result.scalar_one_or_none()
    if not script or script.project_id != project_id:
        raise HTTPException(status_code=404, detail="Episode not found in this project")

    # Build context from the script and sibling episodes
    if user:
        resolved = await user_model_resolver.resolve(db, user.id, "chat")
        chat_model = resolved.model_id
        chat_api_key = resolved.api_key
        chat_base_url = resolved.base_url
        chat_options = resolved.raw_params or {}
    else:
        chat_model = chat_api_key = chat_base_url = None
        chat_options = {}

    # Build context from the script and sibling episodes
    sibling_summaries = []
    for ep in script.episodes:
        if ep.id != episode_id:
            sibling_summaries.append(
                f"第{ep.number}集《{ep.title or ''}》：{ep.content[:200] if ep.content else '（暂无内容）'}..."
            )

    context_text = f"""你正在改写短剧《{project.title}》的第{episode.number}集。

## 剧本背景
- 主角：{script.protagonist or '未指定'}
- 类型：{script.genre or '未指定'}
- 梗概：{script.synopsis or '未指定'}
- 背景：{script.background or '未指定'}

## 相邻剧集摘要
{"\n".join(sibling_summaries) if sibling_summaries else '暂无其他剧集'}

## 当前第{episode.number}集内容
{episode.content or '（暂无内容）'}

## 改写要求
{body.user_prompt or '请根据剧本整体背景，优化本集的内容和节奏，保持角色性格一致，增强戏剧张力。输出的 content 字段必须是完整剧本正文（非摘要），严格遵循格式：场景标记用 △，角色对话用 **角色名**（语气）："台词"，每集末尾要有钩子。'}

请输出一个 JSON 对象，格式如下：
```json
{{
  "title": "本集标题",
  "content": "完整剧本正文（每集≥800字，≥3场次，含△场景/**角色**对话/♪音乐/>🎣钩子/>📺预告）"
}}
```"""

    # Call AI
    messages = [
        {"role": "system", "content": SCRIPT_STRUCTURED_SYSTEM},
        {"role": "user", "content": context_text},
    ]

    logger.info(f"Regenerating episode {episode_id} (ep {episode.number})")

    raw_json = await ai_hub.chat.complete_json(
        messages=messages,
        temperature=0.7,
        max_tokens=4096,
        model=chat_model,
        api_key=chat_api_key,
        base_url=chat_base_url,
        **{
            k: v
            for k, v in chat_options.items()
            if k not in {"model", "messages", "temperature", "max_tokens", "response_format", "stream"}
        },
    )

    # Update episode
    new_title = raw_json.get("title", "").strip()
    new_content = raw_json.get("content", "").strip()

    if new_title:
        episode.title = new_title
    if new_content:
        episode.content = new_content

    await db.flush()
    await db.refresh(episode)

    return {
        "message": "Episode regenerated",
        "episode_id": episode.id,
        "title": episode.title,
        "content_length": len(episode.content or ""),
    }
