"""Shared normalization for user-provided AI provider settings."""

from __future__ import annotations


def normalize_optional_string(value: str | None) -> str | None:
    """Trim surrounding whitespace while preserving None."""
    if value is None:
        return None
    return value.strip()


def normalize_api_base_url(base_url: str | None) -> str | None:
    """Normalize OpenAI-compatible base URLs before storing or using them."""
    url = normalize_optional_string(base_url)
    if not url:
        return url
    url = url.rstrip("/")
    if not url.endswith("/v1"):
        url = f"{url}/v1"
    return url


def normalize_capabilities(capabilities: str | None) -> str:
    """Normalize comma-separated provider capability names."""
    if not capabilities:
        return ""
    parts = [part.strip().lower() for part in capabilities.split(",")]
    return ",".join(part for part in parts if part)


def has_capability(capabilities: str | None, capability_type: str) -> bool:
    """Return whether a provider capability list includes a capability."""
    capability = (capability_type or "").strip().lower()
    if not capability:
        return False
    return capability in set(normalize_capabilities(capabilities).split(","))
