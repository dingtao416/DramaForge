"""
DramaForge - LLM Module
Legacy compatibility layer — new code should use `from app.ai_hub import ai_hub` directly.
"""

from app.ai_hub import ai_hub

# Backward compatibility aliases
def get_llm(model=None):
    """Legacy: returns ai_hub.chat service. New code should use ai_hub.chat directly."""
    return ai_hub.chat

__all__ = ["ai_hub", "get_llm"]