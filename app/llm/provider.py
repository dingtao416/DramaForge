"""
DramaForge - LLM Provider
Unified LLM interface through laozhang.ai API gateway.
Compatible with OpenAI SDK format - supports 200+ models with a single API key.

Docs: https://docs.laozhang.ai/api-capabilities/text-generation
"""

import json
from typing import Any, Optional

from openai import AsyncOpenAI
from loguru import logger

from config import settings


class LLMProvider:
    """
    Unified LLM provider powered by laozhang.ai.

    All models (GPT-4, Claude, Gemini, DeepSeek, Qwen, etc.)
    are accessed through a single OpenAI-compatible endpoint.
    Just change the model name to switch between providers.
    """

    def __init__(self, model: Optional[str] = None):
        self.model = model or settings.llm_model
        self.client = AsyncOpenAI(
            api_key=settings.laozhang_api_key,
            base_url=settings.laozhang_base_url,
        )
        logger.info(f"LLMProvider initialized | model={self.model} base_url={settings.laozhang_base_url}")

    async def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = None,
        max_tokens: int = None,
        response_format: Optional[dict] = None,
        model: Optional[str] = None,
        **kwargs,
    ) -> str:
        """
        Send a chat completion request via laozhang.ai.

        Args:
            messages: List of message dicts with 'role' and 'content'.
            temperature: Sampling temperature (default from config).
            max_tokens: Maximum output tokens (default from config).
            response_format: Optional JSON response format.
            model: Override model for this request.

        Returns:
            The assistant's reply as a string.
        """
        use_model = model or self.model
        use_temp = temperature if temperature is not None else settings.llm_temperature
        use_max_tokens = max_tokens or settings.llm_max_tokens

        logger.info(f"LLM Request | model={use_model} temp={use_temp}")

        try:
            params = {
                "model": use_model,
                "messages": messages,
                "temperature": use_temp,
                "max_tokens": use_max_tokens,
            }
            if response_format:
                params["response_format"] = response_format

            params.update(kwargs)

            response = await self.client.chat.completions.create(**params)
            content = response.choices[0].message.content

            logger.info(
                f"LLM Response | model={use_model} "
                f"tokens_in={response.usage.prompt_tokens} "
                f"tokens_out={response.usage.completion_tokens}"
            )
            return content

        except Exception as e:
            logger.error(f"LLM Error | model={use_model} error={e}")
            raise

    async def chat_json(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 4096,
        model: Optional[str] = None,
        **kwargs,
    ) -> dict[str, Any]:
        """
        Send a chat request and parse the response as JSON.

        Returns:
            Parsed JSON dict.
        """
        response = await self.chat(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
            model=model,
            **kwargs,
        )

        # Try to parse JSON from response
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code blocks
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
                return json.loads(json_str)
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
                return json.loads(json_str)
            raise

    async def chat_stream(
        self,
        messages: list[dict[str, str]],
        temperature: float = None,
        max_tokens: int = None,
        model: Optional[str] = None,
        **kwargs,
    ):
        """
        Send a streaming chat completion request.

        Yields:
            Content chunks as strings.
        """
        use_model = model or self.model
        use_temp = temperature if temperature is not None else settings.llm_temperature
        use_max_tokens = max_tokens or settings.llm_max_tokens

        logger.info(f"LLM Stream Request | model={use_model}")

        stream = await self.client.chat.completions.create(
            model=use_model,
            messages=messages,
            temperature=use_temp,
            max_tokens=use_max_tokens,
            stream=True,
            **kwargs,
        )

        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


# Convenience function
def get_llm(model: Optional[str] = None) -> LLMProvider:
    """Get a LLM provider instance."""
    return LLMProvider(model=model)