"""
DramaForge AI Hub - Base Client
Low-level HTTP client shared by all AI services.
Handles: authentication, retries with exponential backoff,
         timeout, error mapping, request/response logging.

No caller outside ai_hub should import this module.
"""

from __future__ import annotations

import asyncio
from typing import Any

import httpx
from loguru import logger
from openai import AsyncOpenAI

from app.core.ai_config import normalize_api_base_url, normalize_optional_string
from app.core.config import settings


class HubClientError(Exception):
    """Base exception for all AI Hub errors."""

    def __init__(self, message: str, status_code: int = 0, raw: Any = None):
        self.status_code = status_code
        self.raw = raw
        super().__init__(message)


class RateLimitError(HubClientError):
    """429 - Rate limit exceeded."""
    pass


class AuthError(HubClientError):
    """401/403 - Invalid API key."""
    pass


class QuotaError(HubClientError):
    """402 - Insufficient balance."""
    pass


class ModelError(HubClientError):
    """Model not found or not supported."""
    pass


# ─────────────── Error code mapping ───────────────

_ERROR_MAP = {
    401: AuthError,
    403: AuthError,
    402: QuotaError,
    429: RateLimitError,
}


class BaseClient:
    """
    Shared async HTTP + OpenAI SDK client for laozhang.ai.

    Features:
    - Single AsyncOpenAI instance (connection pooling)
    - Single httpx.AsyncClient for raw HTTP calls
    - Auto retry with exponential backoff (3 attempts)
    - Unified error classification
    - Request/response debug logging
    - Support for custom user-provided API keys and base URLs
    """

    _openai: AsyncOpenAI | None = None
    _http: httpx.AsyncClient | None = None

    # Custom client cache: {(api_key, base_url): AsyncOpenAI}
    _custom_openai: dict[tuple[str, str], AsyncOpenAI] = {}

    # Retry config
    MAX_RETRIES = 3
    RETRY_BASE_DELAY = 1.0    # seconds
    RETRY_MAX_DELAY = 30.0
    DEFAULT_TIMEOUT = 600      # seconds (script/video gen can take several minutes)

    # ──────────── Singleton accessors ────────────

    @classmethod
    def openai(cls, api_key: str = None, base_url: str = None) -> AsyncOpenAI:
        """
        Get an AsyncOpenAI client.

        If api_key and base_url are provided, returns a cached custom client.
        Otherwise returns the system-default client from config.py.
        """
        api_key = normalize_optional_string(api_key)
        base_url = normalize_api_base_url(base_url)

        if api_key and base_url:
            cache_key = (api_key, base_url)
            if cache_key not in cls._custom_openai:
                cls._custom_openai[cache_key] = AsyncOpenAI(
                    api_key=api_key,
                    base_url=base_url,
                    timeout=cls.DEFAULT_TIMEOUT,
                    max_retries=0,
                )
                logger.info(f"Custom OpenAI client created | base_url={base_url}")
            return cls._custom_openai[cache_key]

        # System default
        if cls._openai is None:
            default_base_url = normalize_api_base_url(settings.laozhang_base_url)
            cls._openai = AsyncOpenAI(
                api_key=normalize_optional_string(settings.laozhang_api_key),
                base_url=default_base_url,
                timeout=cls.DEFAULT_TIMEOUT,
                max_retries=0,
            )
            logger.info(
                f"AI Hub OpenAI client created | "
                f"base_url={default_base_url}"
            )
        return cls._openai

    @classmethod
    def http(cls, api_key: str = None, base_url: str = None) -> httpx.AsyncClient:
        """
        Get an httpx client.

        If api_key and base_url are provided, creates a new client.
        Otherwise returns the system-default client from config.py.
        """
        api_key = normalize_optional_string(api_key)
        base_url = normalize_api_base_url(base_url)

        if api_key and base_url:
            return httpx.AsyncClient(
                base_url=base_url,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                timeout=cls.DEFAULT_TIMEOUT,
            )

        # System default
        if cls._http is None:
            default_base_url = normalize_api_base_url(settings.laozhang_base_url)
            cls._http = httpx.AsyncClient(
                base_url=default_base_url,
                headers={
                    "Authorization": (
                        f"Bearer {normalize_optional_string(settings.laozhang_api_key)}"
                    ),
                    "Content-Type": "application/json",
                },
                timeout=cls.DEFAULT_TIMEOUT,
            )
            logger.info("AI Hub HTTP client created")
        return cls._http

    # ──────────── Lifecycle ────────────

    @classmethod
    async def close(cls):
        """Gracefully close all clients. Call on app shutdown."""
        if cls._openai is not None:
            await cls._openai.close()
            cls._openai = None
        if cls._http is not None:
            await cls._http.aclose()
            cls._http = None
        for key, client in cls._custom_openai.items():
            await client.close()
        cls._custom_openai.clear()
        logger.info("AI Hub clients closed")

    # ──────────── Retry wrapper ────────────

    @classmethod
    async def with_retry(cls, coro_factory, *, retries: int = None, label: str = ""):
        """
        Execute an async callable with exponential-backoff retries.

        Args:
            coro_factory: A zero-arg async callable (lambda or functools.partial).
            retries: Max retry count (default MAX_RETRIES).
            label: Label for logging (e.g. "chat" / "image").

        Returns:
            The result of the coroutine.

        Raises:
            HubClientError subclass on final failure.
        """
        max_attempts = (retries or cls.MAX_RETRIES) + 1
        last_exc = None

        for attempt in range(1, max_attempts + 1):
            try:
                result = await coro_factory()
                if attempt > 1:
                    logger.info(f"[{label}] succeeded on attempt {attempt}")
                return result

            except Exception as exc:
                last_exc = exc
                status = _extract_status(exc)
                mapped = _ERROR_MAP.get(status)

                # Don't retry auth / quota / not-found errors
                if mapped in (AuthError, QuotaError) or status == 404:
                    err_cls = mapped if mapped else HubClientError
                    raise err_cls(str(exc), status_code=status, raw=exc) from exc

                if attempt < max_attempts:
                    delay = min(
                        cls.RETRY_BASE_DELAY * (2 ** (attempt - 1)),
                        cls.RETRY_MAX_DELAY,
                    )
                    logger.warning(
                        f"[{label}] attempt {attempt} failed: {exc} "
                        f"→ retrying in {delay:.1f}s"
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        f"[{label}] all {max_attempts} attempts exhausted: {exc}"
                    )

        # Convert to typed error on final failure
        status = _extract_status(last_exc)
        error_cls = _ERROR_MAP.get(status, HubClientError)
        raise error_cls(str(last_exc), status_code=status, raw=last_exc) from last_exc


def _extract_status(exc: Exception) -> int:
    """Try to pull an HTTP status code out of various exception types."""
    # openai lib
    if hasattr(exc, "status_code"):
        return exc.status_code
    # httpx
    if hasattr(exc, "response") and hasattr(exc.response, "status_code"):
        return exc.response.status_code
    return 0
