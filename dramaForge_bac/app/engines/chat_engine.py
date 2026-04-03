"""
DramaForge v2.0 — Chat Agent Engine
=====================================
Wraps ai_hub.chat with DramaForge-specific system prompts and modes.
Supports both full and streaming responses.
"""

from __future__ import annotations

from typing import Any, AsyncIterator, Optional

from loguru import logger

from app.ai_hub import ai_hub, ChatMessage


# ═══════════════════════════════════════════════════════════════════
# System Prompts per mode
# ═══════════════════════════════════════════════════════════════════

SYSTEM_PROMPTS: dict[str, str] = {
    "general": (
        "你是 DramaForge AI 助手，一个专业的短剧视频创作平台的智能助理。\n"
        "你可以帮助用户：\n"
        "- 构思短剧剧本创意和故事大纲\n"
        "- 设计角色性格、背景和对白\n"
        "- 规划分镜、场景和拍摄风格\n"
        "- 解答平台使用相关问题\n\n"
        "请用简洁、专业且富有创意的方式回复。默认使用中文。"
    ),
    "scriptwriter": (
        "你是 DramaForge 专业编剧顾问。你精通短视频剧本创作，包括：\n"
        "- 短剧剧本结构（钩子→冲突→反转→高潮→结尾）\n"
        "- 角色塑造与对白设计\n"
        "- 节奏控制与情绪曲线\n"
        "- 不同题材（甜宠、悬疑、逆袭、穿越等）的创作技巧\n\n"
        "请以编剧导师的身份回答用户的创作问题，提供具体可执行的建议。"
    ),
    "director": (
        "你是 DramaForge 导演助理。你精通短视频分镜与视觉叙事：\n"
        "- 镜头语言（特写、中景、远景、运镜）\n"
        "- 场景构图与色彩搭配\n"
        "- 节奏剪辑与转场设计\n"
        "- AI 生成图片/视频的 prompt 优化技巧\n\n"
        "请以视觉专家的身份帮助用户规划分镜和视觉风格。"
    ),
    "project": (
        "你是 DramaForge 项目助手。用户正在进行一个具体的短剧项目。\n"
        "请结合项目上下文（如果提供）帮助用户完成当前阶段的工作。\n"
        "你的职责包括：\n"
        "- 根据已有剧本/大纲提供改进建议\n"
        "- 帮助完善角色和场景设定\n"
        "- 协助编写具体的分镜描述和对白\n"
        "- 为 AI 图片/视频生成优化 prompt\n\n"
        "请始终围绕用户当前的项目进展来回复。"
    ),
}

DEFAULT_MODE = "general"


# ═══════════════════════════════════════════════════════════════════
# Chat Engine
# ═══════════════════════════════════════════════════════════════════

class ChatEngine:
    """
    DramaForge conversational agent engine.

    Supports multiple modes (general / scriptwriter / director / project)
    and wraps ai_hub.chat for both blocking and streaming calls.
    """

    def get_system_prompt(self, mode: str | None = None) -> str:
        """Get the system prompt for the given mode."""
        return SYSTEM_PROMPTS.get(mode or DEFAULT_MODE, SYSTEM_PROMPTS[DEFAULT_MODE])

    def _build_messages(
        self,
        user_message: str,
        *,
        mode: str | None = None,
        history: list[ChatMessage] | None = None,
        project_context: str | None = None,
    ) -> list[dict]:
        """Build the full message list for the LLM call."""
        messages: list[dict] = []

        # System prompt
        system_prompt = self.get_system_prompt(mode)
        if project_context:
            system_prompt += f"\n\n--- 项目上下文 ---\n{project_context}"
        messages.append({"role": "system", "content": system_prompt})

        # Conversation history (last 20 messages max)
        if history:
            for msg in history[-20:]:
                if isinstance(msg, ChatMessage):
                    messages.append(msg.model_dump())
                elif isinstance(msg, dict):
                    messages.append(msg)

        # Current user message
        messages.append({"role": "user", "content": user_message})

        return messages

    async def run(
        self,
        user_message: str,
        *,
        mode: str | None = None,
        history: list[ChatMessage] | None = None,
        project_context: str | None = None,
        model: str | None = None,
        temperature: float | None = None,
    ) -> str:
        """
        Non-streaming chat completion. Returns the full assistant response.
        """
        messages = self._build_messages(
            user_message,
            mode=mode,
            history=history,
            project_context=project_context,
        )

        logger.info(f"ChatEngine.run | mode={mode or DEFAULT_MODE} msgs={len(messages)}")

        resp = await ai_hub.chat.complete(
            messages=messages,
            model=model,
            temperature=temperature,
        )
        return resp.content

    async def run_stream(
        self,
        user_message: str,
        *,
        mode: str | None = None,
        history: list[ChatMessage] | None = None,
        project_context: str | None = None,
        model: str | None = None,
        temperature: float | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        """
        Streaming chat completion. Yields SSE-compatible event dicts.

        Event types:
            {"type": "content", "data": "..."}   — text chunk
            {"type": "done",    "data": None}     — stream finished
            {"type": "error",   "data": "..."}    — error occurred
        """
        messages = self._build_messages(
            user_message,
            mode=mode,
            history=history,
            project_context=project_context,
        )

        logger.info(f"ChatEngine.run_stream | mode={mode or DEFAULT_MODE} msgs={len(messages)}")

        try:
            async for chunk in ai_hub.chat.stream(
                messages=messages,
                model=model,
                temperature=temperature,
            ):
                yield {"type": "content", "data": chunk}

            yield {"type": "done", "data": None}

        except Exception as exc:
            logger.error(f"ChatEngine stream error: {exc}")
            yield {"type": "error", "data": str(exc)}


# Module-level singleton
chat_engine = ChatEngine()
