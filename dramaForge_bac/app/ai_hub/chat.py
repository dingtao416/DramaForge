"""
DramaForge AI Hub - Chat Service
Text generation (LLM) via laozhang.ai OpenAI-compatible endpoint.
Supports 200+ models: GPT-4, Claude, Gemini, DeepSeek, Qwen, etc.
"""

from __future__ import annotations

import json
from typing import Any, AsyncIterator, Optional

from loguru import logger

from app.core.config import settings
from app.ai_hub._client import BaseClient, HubClientError
from app.ai_hub._models import ChatMessage, ChatResponse


class ChatService:
    """Text generation service - the most-used capability in DramaForge."""

    # ──────────── Core API ────────────

    async def complete(
        self,
        messages: list[dict | ChatMessage],
        *,
        model: str = None,
        temperature: float = None,
        max_tokens: int = None,
        response_format: dict = None,
        api_key: str = None,
        base_url: str = None,
        **kwargs,
    ) -> ChatResponse:
        """
        Send a chat completion request.

        Args:
            messages: Conversation messages (dicts or ChatMessage objects).
            model: Model name (default from config).
            temperature: Sampling temperature (default from config).
            max_tokens: Max output tokens (default from config).
            response_format: e.g. {"type": "json_object"}.

        Returns:
            ChatResponse with content, token usage, etc.
        """
        use_model = model or settings.llm_model
        use_temp = temperature if temperature is not None else settings.llm_temperature
        use_max = max_tokens or settings.llm_max_tokens

        # Normalize messages to dicts
        msg_dicts = [
            m.model_dump() if isinstance(m, ChatMessage) else m
            for m in messages
        ]

        logger.info(f"chat.complete | model={use_model} msgs={len(msg_dicts)}")

        params: dict[str, Any] = {
            "model": use_model,
            "messages": msg_dicts,
            "temperature": use_temp,
            "max_tokens": use_max,
        }
        if response_format:
            params["response_format"] = response_format
        params.update(kwargs)

        client = BaseClient.openai(api_key, base_url)

        resp = await BaseClient.with_retry(
            lambda: client.chat.completions.create(**params),
            label=f"chat:{use_model}",
        )

        if not resp.choices:
            raise HubClientError(
                f"API returned empty choices for model '{use_model}'. "
                f"The model may not be available at this endpoint.",
                status_code=0,
            )
        result = ChatResponse(
            content=resp.choices[0].message.content or "",
            model=resp.model,
            prompt_tokens=resp.usage.prompt_tokens if resp.usage else 0,
            completion_tokens=resp.usage.completion_tokens if resp.usage else 0,
            total_tokens=resp.usage.total_tokens if resp.usage else 0,
            finish_reason=resp.choices[0].finish_reason or "",
        )

        logger.info(
            f"chat.complete done | model={result.model} "
            f"tokens={result.total_tokens}"
        )
        return result

    # ──────────── Convenience Shortcuts ────────────

    async def ask(
        self,
        prompt: str,
        *,
        system: str = "",
        model: str = None,
        temperature: float = None,
        max_tokens: int = None,
        api_key: str = None,
        base_url: str = None,
        **kwargs,
    ) -> str:
        """
        Simple one-shot question -> answer.

        Example:
            answer = await ai_hub.chat.ask("写一个100字的悬疑故事开头")
        """
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        resp = await self.complete(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=api_key,
            base_url=base_url,
            **kwargs,
        )
        return resp.content

    async def ask_json(
        self,
        prompt: str,
        *,
        system: str = "",
        model: str = None,
        temperature: float = 0.3,
        max_tokens: int = None,
        api_key: str = None,
        base_url: str = None,
        **kwargs,
    ) -> dict:
        """
        One-shot question -> JSON dict.

        Example:
            data = await ai_hub.chat.ask_json("列出 3 个角色，返回 JSON")
        """
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        resp = await self.complete(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
            api_key=api_key,
            base_url=base_url,
            **kwargs,
        )
        return _parse_json(resp.content)

    async def complete_json(
        self,
        messages: list[dict | ChatMessage],
        *,
        model: str = None,
        temperature: float = 0.3,
        max_tokens: int = None,
        api_key: str = None,
        base_url: str = None,
        **kwargs,
    ) -> dict:
        """
        Multi-turn conversation -> JSON dict.

        Example:
            data = await ai_hub.chat.complete_json(messages=[...])
        """
        resp = await self.complete(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
            api_key=api_key,
            base_url=base_url,
            **kwargs,
        )
        return _parse_json(resp.content)

    async def stream(
        self,
        messages: list[dict | ChatMessage],
        *,
        model: str = None,
        temperature: float = None,
        max_tokens: int = None,
        api_key: str = None,
        base_url: str = None,
        **kwargs,
    ) -> AsyncIterator[str]:
        """
        Streaming chat - yields content chunks.

        Example:
            async for chunk in ai_hub.chat.stream(messages):
                print(chunk, end="")
        """
        use_model = model or settings.llm_model
        use_temp = temperature if temperature is not None else settings.llm_temperature
        use_max = max_tokens or settings.llm_max_tokens

        msg_dicts = [
            m.model_dump() if isinstance(m, ChatMessage) else m
            for m in messages
        ]

        logger.info(f"chat.stream | model={use_model}")

        client = BaseClient.openai(api_key, base_url)
        resp_stream = await client.chat.completions.create(
            model=use_model,
            messages=msg_dicts,
            temperature=use_temp,
            max_tokens=use_max,
            stream=True,
            **kwargs,
        )

        async for chunk in resp_stream:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta


# ──────────── Helpers ────────────

def _parse_json(text: str) -> dict:
    """Best-effort JSON extraction from LLM output."""
    import re

    # Strategy 1: Direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Strategy 2: Extract from ```json ... ``` or ``` ... ``` blocks
    for fence in ("```json", "```"):
        if fence in text:
            inner = text.split(fence, 1)[1].split("```", 1)[0].strip()
            try:
                return json.loads(inner)
            except json.JSONDecodeError:
                continue

    # Strategy 3: Find first { to last }
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        candidate = text[start:end + 1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

        # Strategy 4: Fix trailing commas
        try:
            fixed = re.sub(r',\s*}', '}', candidate)
            fixed = re.sub(r',\s*]', ']', fixed)
            return json.loads(fixed)
        except json.JSONDecodeError:
            pass

        # Strategy 5: Fix unescaped control characters inside JSON string values.
        # LLMs often embed raw newlines/tabs inside content fields, which breaks JSON.
        try:
            fixed = _fix_unescaped_string_content(candidate)
            return json.loads(fixed)
        except json.JSONDecodeError:
            pass

        # Strategy 6: Try to find the last complete JSON object by scanning
        # for balanced braces (handles truncation by max_tokens)
        try:
            truncated = _truncate_to_last_complete_json(candidate)
            if truncated != candidate:
                return json.loads(truncated)
        except json.JSONDecodeError:
            pass

    logger.error(
        "Failed to parse JSON from LLM output (length={}). "
        "First 300 chars: {!r} ... Last 300 chars: {!r}",
        len(text),
        text[:300],
        text[-300:],
    )
    raise ValueError(f"Cannot parse JSON from LLM output (length={len(text)})")


def _fix_unescaped_string_content(json_text: str) -> str:
    """Fix common LLM JSON issues: unescaped newlines/tabs/quotes inside string values."""
    import re

    result = []
    i = 0
    in_string = False
    string_char = None
    while i < len(json_text):
        ch = json_text[i]

        if not in_string:
            result.append(ch)
            if ch in ('"', "'"):
                in_string = True
                string_char = ch
            i += 1
        else:
            if ch == '\\':
                result.append(ch)
                if i + 1 < len(json_text):
                    result.append(json_text[i + 1])
                    i += 1
                i += 1
            elif ch == string_char:
                result.append(ch)
                in_string = False
                string_char = None
                i += 1
            elif ch in ('\n', '\r', '\t'):
                # Escape control characters that break JSON strings
                escape_map = {'\n': '\\n', '\r': '\\r', '\t': '\\t'}
                result.append(escape_map[ch])
                i += 1
            else:
                result.append(ch)
                i += 1

    return ''.join(result)


def _truncate_to_last_complete_json(json_text: str) -> str:
    """Truncate JSON text to the last position where braces/brackets are balanced."""
    stack = []
    in_string = False
    string_char = None
    last_complete = 0

    for i, ch in enumerate(json_text):
        if in_string:
            if ch == '\\':
                continue  # skip next char
            if ch == string_char:
                in_string = False
            continue

        if ch in ('"', "'"):
            in_string = True
            string_char = ch
            continue

        if ch in ('{', '['):
            stack.append(ch)
        elif ch in ('}', ']'):
            expected = '{' if ch == '}' else '['
            if stack and stack[-1] == expected:
                stack.pop()
                if not stack:
                    last_complete = i + 1
            else:
                break  # unbalanced — stop here

    if last_complete > 0 and last_complete < len(json_text):
        return json_text[:last_complete]
    return json_text
