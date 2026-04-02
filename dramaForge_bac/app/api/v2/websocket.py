"""
DramaForge v2.0 — WebSocket Real-time Push
============================================
WebSocket endpoint for real-time task progress updates.
"""

from __future__ import annotations

import asyncio
import json
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger

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


@router.websocket("/ws/tasks/{task_id}")
async def task_websocket(
    ws: WebSocket,
    task_id: str,
):
    """
    WebSocket endpoint for real-time task progress.

    Sends JSON messages:
    - {"type": "progress", "task_id": "...", "status": "running", ...}
    - {"type": "completed", "task_id": "...", "result": {...}}
    - {"type": "error", "task_id": "...", "error": "..."}
    """
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
