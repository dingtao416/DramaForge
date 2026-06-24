"""
DramaForge v2.0 — WebSocket Real-time Push
============================================
WebSocket endpoint for real-time task progress updates.
Authentication via JWT token in query parameter: ?token=<jwt>
"""

from __future__ import annotations

import asyncio
import json
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from loguru import logger
from sqlalchemy import select

from app.core.security import decode_token
from app.core.database import AsyncSessionLocal
from app.tasks.asset_tasks import get_task_status as get_asset_task_status
from app.tasks.video_tasks import get_task_status as get_video_task_status

router = APIRouter()


class ConnectionManager:
    """Manages active WebSocket connections."""

    def __init__(self):
        self._connections: dict[str, list[WebSocket]] = {}

    async def connect(self, task_id: str, ws: WebSocket):
        """Accept and register a WebSocket connection for a task."""
        await ws.accept()
        if task_id not in self._connections:
            self._connections[task_id] = []
        self._connections[task_id].append(ws)
        logger.info(f"WS: client connected for task={task_id}")

    def disconnect(self, task_id: str, ws: WebSocket):
        """Remove a WebSocket connection."""
        if task_id in self._connections:
            self._connections[task_id] = [
                c for c in self._connections[task_id] if c != ws
            ]
            if not self._connections[task_id]:
                del self._connections[task_id]
        logger.info(f"WS: client disconnected from task={task_id}")

    async def send_to_task(self, task_id: str, message: dict):
        """Send a message to all connections watching a task."""
        if task_id not in self._connections:
            return
        dead = []
        for ws in self._connections[task_id]:
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(task_id, ws)

    @property
    def active_count(self) -> int:
        return sum(len(v) for v in self._connections.values())


# Global connection manager
manager = ConnectionManager()


def _get_task_status(task_id: str) -> dict:
    """Try to get task status from both asset and video task registries."""
    # Try asset tasks first
    status = get_asset_task_status(task_id)
    if status.get("status") != "not_found":
        return status

    # Try video tasks
    status = get_video_task_status(task_id)
    return status


async def _authenticate_ws(token: str | None) -> int:
    """Authenticate a WebSocket connection via JWT token. Returns user_id.

    Closes the WebSocket with 4001 if token is missing or invalid.
    """
    if not token:
        raise WebSocketDisconnect(code=4001, reason="Missing authentication token")

    try:
        payload = decode_token(token)
    except Exception:
        raise WebSocketDisconnect(code=4001, reason="Invalid authentication token")

    if payload.get("type") != "access":
        raise WebSocketDisconnect(code=4001, reason="Invalid token type")

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise WebSocketDisconnect(code=4001, reason="Invalid token payload")

    return int(user_id_str)


async def _verify_task_ownership(task_id: str, user_id: int) -> int | None:
    """Verify the user owns the project referenced by this task_id.

    Task ID formats:
        assets_{project_id}         → check Project.user_id
        regen_char_{char_id}        → Character.project_id → Project.user_id
        segment_{segment_id}        → Segment.episode_id → Script.project_id → Project.user_id
        compose_{episode_id}        → Episode.script_id → Script.project_id → Project.user_id

    Returns the project_id if authorized, raises WebSocketDisconnect(4003) otherwise.
    """
    from app.models.project import Project
    from app.models.character import Character
    from app.models.segment import Segment
    from app.models.episode import Episode
    from app.models.script import Script

    async with AsyncSessionLocal() as db:
        try:
            if task_id.startswith("assets_"):
                project_id = int(task_id.split("_", 1)[1])
                project = await db.get(Project, project_id)
                if not project or project.user_id != user_id:
                    raise WebSocketDisconnect(code=4003, reason="Forbidden: not your task")
                return project_id

            elif task_id.startswith("regen_char_"):
                char_id = int(task_id.split("_", 2)[2])
                char = await db.get(Character, char_id)
                if not char:
                    raise WebSocketDisconnect(code=4003, reason="Forbidden: task not found")
                project = await db.get(Project, char.project_id)
                if not project or project.user_id != user_id:
                    raise WebSocketDisconnect(code=4003, reason="Forbidden: not your task")
                return char.project_id

            elif task_id.startswith("segment_"):
                seg_id = int(task_id.split("_", 1)[1])
                seg = await db.get(Segment, seg_id)
                if not seg:
                    raise WebSocketDisconnect(code=4003, reason="Forbidden: task not found")
                episode = await db.get(Episode, seg.episode_id)
                if not episode:
                    raise WebSocketDisconnect(code=4003, reason="Forbidden: task not found")
                script = await db.get(Script, episode.script_id)
                if not script:
                    raise WebSocketDisconnect(code=4003, reason="Forbidden: task not found")
                project = await db.get(Project, script.project_id)
                if not project or project.user_id != user_id:
                    raise WebSocketDisconnect(code=4003, reason="Forbidden: not your task")
                return script.project_id

            elif task_id.startswith("compose_"):
                ep_id = int(task_id.split("_", 1)[1])
                episode = await db.get(Episode, ep_id)
                if not episode:
                    raise WebSocketDisconnect(code=4003, reason="Forbidden: task not found")
                script = await db.get(Script, episode.script_id)
                if not script:
                    raise WebSocketDisconnect(code=4003, reason="Forbidden: task not found")
                project = await db.get(Project, script.project_id)
                if not project or project.user_id != user_id:
                    raise WebSocketDisconnect(code=4003, reason="Forbidden: not your task")
                return script.project_id

            else:
                # Unknown task_id format — reject
                raise WebSocketDisconnect(code=4003, reason="Forbidden: unknown task format")

        except ValueError:
            raise WebSocketDisconnect(code=4003, reason="Forbidden: invalid task id")
        except WebSocketDisconnect:
            raise
        except Exception:
            raise WebSocketDisconnect(code=4003, reason="Forbidden: verification failed")


@router.websocket("/ws/tasks/{task_id}")
async def task_websocket(
    ws: WebSocket,
    task_id: str,
    token: str = Query(None),
):
    """
    WebSocket endpoint for real-time task progress.

    Authentication: pass JWT access token as query parameter:
        ws://host/api/v2/ws/tasks/{task_id}?token=<jwt_token>

    Sends JSON messages:
    - {"type": "progress", "task_id": "...", "status": "running", ...}
    - {"type": "completed", "task_id": "...", "result": {...}}
    - {"type": "error", "task_id": "...", "error": "..."}
    """
    # ── Authenticate ──
    user_id = await _authenticate_ws(token)

    # ── Verify the user owns the task's project ──
    await _verify_task_ownership(task_id, user_id)

    await manager.connect(task_id, ws)

    try:
        # Poll task status and push updates
        previous_status = None
        while True:
            status = _get_task_status(task_id)
            current = status.get("status", "not_found")

            # Only send updates when status changes
            if current != previous_status:
                if current == "running":
                    await ws.send_json({
                        "type": "progress",
                        "task_id": task_id,
                        **status,
                    })
                elif current == "completed":
                    await ws.send_json({
                        "type": "completed",
                        "task_id": task_id,
                        **status,
                    })
                    break  # Task done, close connection
                elif current == "failed":
                    await ws.send_json({
                        "type": "error",
                        "task_id": task_id,
                        **status,
                    })
                    break
                elif current == "not_found":
                    await ws.send_json({
                        "type": "error",
                        "task_id": task_id,
                        "error": "Task not found",
                    })
                    break

                previous_status = current

            # Also listen for client messages (ping/commands)
            try:
                data = await asyncio.wait_for(ws.receive_text(), timeout=2.0)
                # Handle client messages
                try:
                    msg = json.loads(data)
                    if msg.get("type") == "ping":
                        await ws.send_json({"type": "pong"})
                except json.JSONDecodeError:
                    pass
            except asyncio.TimeoutError:
                # No client message, continue polling
                pass

    except WebSocketDisconnect:
        logger.info(f"WS: client disconnected from task={task_id}")
    except Exception as e:
        logger.error(f"WS: error for task={task_id}: {e}")
    finally:
        manager.disconnect(task_id, ws)
