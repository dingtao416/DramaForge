"""
DramaForge v2.0 — Chat API (Conversational Agent)
===================================================
Conversation CRUD + SSE streaming chat endpoint.
Adapted from IAA project patterns, using DramaForge's ai_hub.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.ai_hub import ChatMessage
from app.core.security import CurrentUser, DbSession
from app.engines.chat_engine import chat_engine
from app.models.user import Conversation, Message, MessageRole

router = APIRouter(prefix="/chat", tags=["Chat"])


# ═══════════════════════════════════════════════════════════════════
# Schemas
# ═══════════════════════════════════════════════════════════════════

class SendMessageRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=10000, description="Message content")
    conversation_id: Optional[int] = Field(None, description="Existing conversation id (omit to create new)")
    mode: Optional[str] = Field(None, description="Agent mode: general / scriptwriter / director / project")
    project_id: Optional[int] = Field(None, description="Link chat to a project")
    stream: bool = Field(True, description="Whether to use SSE streaming")
    model: Optional[str] = Field(None, description="Override LLM model")
    temperature: Optional[float] = Field(None, ge=0, le=2, description="Override temperature")


class MessageResponse(BaseModel):
    id: int
    conversation_id: int
    role: str
    content: str
    meta_json: Optional[dict] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationResponse(BaseModel):
    id: int
    title: Optional[str] = None
    mode: Optional[str] = None
    project_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    message_count: int = 0

    model_config = {"from_attributes": True}


class ConversationDetailResponse(ConversationResponse):
    messages: list[MessageResponse] = []


class ChatCompletionResponse(BaseModel):
    message: MessageResponse
    conversation_id: int


# ═══════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════

def sse_event(event: str, data: dict | str | None) -> str:
    """Format a Server-Sent Event string."""
    payload = data if isinstance(data, str) else json.dumps(data, ensure_ascii=False)
    return f"event: {event}\ndata: {payload}\n\n"


def _build_history(messages: list[Message], limit: int = 20) -> list[ChatMessage]:
    """Convert DB messages to ChatMessage objects for the engine."""
    history: list[ChatMessage] = []
    for msg in messages[-limit:]:
        history.append(ChatMessage(role=msg.role.value, content=msg.content))
    return history


# ═══════════════════════════════════════════════════════════════════
# Endpoints
# ═══════════════════════════════════════════════════════════════════

@router.post("/message")
async def send_message(
    request: SendMessageRequest,
    user: CurrentUser,
    db: DbSession,
):
    """
    Send a chat message.

    - If `stream=true` (default): returns SSE stream (`text/event-stream`)
    - If `stream=false`: returns JSON with full completion

    SSE events:
        - `conversation` — {id, title}
        - `user_message` — {id, content}
        - `delta`        — {content: "chunk..."}
        - `done`         — {message_id, finish_reason}
        - `error`        — {code, message}
    """

    # ── Get or create conversation ────────────────────────────
    if request.conversation_id:
        result = await db.execute(
            select(Conversation)
            .options(selectinload(Conversation.messages))
            .where(
                Conversation.id == request.conversation_id,
                Conversation.user_id == user.id,
            )
        )
        conversation = result.scalar_one_or_none()
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )
    else:
        title = request.content[:50] + ("..." if len(request.content) > 50 else "")
        conversation = Conversation(
            user_id=user.id,
            title=title,
            mode=request.mode,
            project_id=request.project_id,
        )
        db.add(conversation)
        await db.flush()

    # ── Save user message ─────────────────────────────────────
    user_message = Message(
        conversation_id=conversation.id,
        role=MessageRole.USER,
        content=request.content,
    )
    db.add(user_message)
    await db.flush()

    # ── Build conversation history ────────────────────────────
    existing_messages = conversation.messages if request.conversation_id else []
    history = _build_history(existing_messages)

    mode = request.mode or conversation.mode

    # ══════════════════════════════════════════════════════════
    # Streaming mode (SSE)
    # ══════════════════════════════════════════════════════════
    if request.stream:
        async def event_generator():
            try:
                # Meta events
                yield sse_event("conversation", {
                    "id": conversation.id,
                    "title": conversation.title,
                })
                yield sse_event("user_message", {
                    "id": user_message.id,
                    "content": request.content,
                })

                # Stream LLM response
                full_content = ""
                async for event in chat_engine.run_stream(
                    user_message=request.content,
                    mode=mode,
                    history=history,
                    model=request.model,
                    temperature=request.temperature,
                ):
                    event_type = event["type"]
                    event_data = event["data"]

                    if event_type == "content":
                        full_content += event_data
                        yield sse_event("delta", {"content": event_data})
                    elif event_type == "error":
                        yield sse_event("error", {
                            "code": "STREAM_ERROR",
                            "message": event_data,
                        })
                        break
                    elif event_type == "done":
                        break

                # Save assistant message to DB
                assistant_message = Message(
                    conversation_id=conversation.id,
                    role=MessageRole.ASSISTANT,
                    content=full_content,
                )
                db.add(assistant_message)
                await db.commit()
                await db.refresh(assistant_message)

                yield sse_event("done", {
                    "message_id": assistant_message.id,
                    "finish_reason": "stop",
                })

            except Exception as exc:
                yield sse_event("error", {
                    "code": "STREAM_ERROR",
                    "message": str(exc),
                })

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    # ══════════════════════════════════════════════════════════
    # Non-streaming mode
    # ══════════════════════════════════════════════════════════
    content = await chat_engine.run(
        user_message=request.content,
        mode=mode,
        history=history,
        model=request.model,
        temperature=request.temperature,
    )

    assistant_message = Message(
        conversation_id=conversation.id,
        role=MessageRole.ASSISTANT,
        content=content,
    )
    db.add(assistant_message)
    await db.commit()
    await db.refresh(assistant_message)

    return ChatCompletionResponse(
        conversation_id=conversation.id,
        message=MessageResponse(
            id=assistant_message.id,
            conversation_id=conversation.id,
            role=assistant_message.role.value,
            content=assistant_message.content,
            meta_json=assistant_message.meta_json,
            created_at=assistant_message.created_at,
        ),
    )


# ═══════════════════════════════════════════════════════════════════
# Conversation CRUD
# ═══════════════════════════════════════════════════════════════════

@router.get("/conversations", response_model=list[ConversationResponse])
async def list_conversations(
    user: CurrentUser,
    db: DbSession,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """List user conversations, newest first."""
    count_result = await db.execute(
        select(func.count(Conversation.id)).where(Conversation.user_id == user.id)
    )
    total = count_result.scalar() or 0

    result = await db.execute(
        select(Conversation)
        .where(Conversation.user_id == user.id)
        .order_by(Conversation.updated_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    conversations = result.scalars().all()

    items = []
    for conv in conversations:
        msg_count_result = await db.execute(
            select(func.count(Message.id)).where(Message.conversation_id == conv.id)
        )
        msg_count = msg_count_result.scalar() or 0
        items.append(ConversationResponse(
            id=conv.id,
            title=conv.title,
            mode=conv.mode,
            project_id=conv.project_id,
            created_at=conv.created_at,
            updated_at=conv.updated_at,
            message_count=msg_count,
        ))

    return items


@router.get("/conversations/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation(
    conversation_id: int,
    user: CurrentUser,
    db: DbSession,
):
    """Get a conversation with all messages."""
    result = await db.execute(
        select(Conversation)
        .options(selectinload(Conversation.messages))
        .where(
            Conversation.id == conversation_id,
            Conversation.user_id == user.id,
        )
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    return ConversationDetailResponse(
        id=conversation.id,
        title=conversation.title,
        mode=conversation.mode,
        project_id=conversation.project_id,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        message_count=len(conversation.messages),
        messages=[
            MessageResponse(
                id=msg.id,
                conversation_id=conversation.id,
                role=msg.role.value,
                content=msg.content,
                meta_json=msg.meta_json,
                created_at=msg.created_at,
            )
            for msg in conversation.messages
        ],
    )


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: int,
    user: CurrentUser,
    db: DbSession,
):
    """Delete a conversation and all its messages."""
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == user.id,
        )
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    await db.delete(conversation)
    await db.commit()

    return {"deleted": True, "conversation_id": conversation_id}
