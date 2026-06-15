"""
DramaForge v2.0 — Built-in Model Catalog
==========================================
Pre-configured provider templates for quick setup.
Users can import these with one click in the Settings page.
"""

BUILTIN_CATALOG = [
    {
        "name": "laozhang.ai 中转站",
        "base_url": "https://api.laozhang.ai/v1",
        "capabilities": "chat,image,video,tts",
        "is_default": True,
        "models": [
            # Chat
            {"model_id": "gpt-4.1-mini", "display_name": "GPT-4.1 Mini", "capability_type": "chat", "is_default": True},
            {"model_id": "gpt-4o", "display_name": "GPT-4o", "capability_type": "chat"},
            {"model_id": "claude-sonnet-4-20250514", "display_name": "Claude Sonnet 4", "capability_type": "chat"},
            {"model_id": "deepseek-v3.1", "display_name": "DeepSeek V3.1", "capability_type": "chat"},
            {"model_id": "glm-4.5-flash", "display_name": "GLM-4.5 Flash", "capability_type": "chat"},
            # Image
            {"model_id": "gpt-image-1-mini", "display_name": "GPT Image Mini", "capability_type": "image", "is_default": True},
            {"model_id": "midjourney-imagine", "display_name": "Midjourney", "capability_type": "image"},
            {"model_id": "ideogram-v3", "display_name": "Ideogram V3", "capability_type": "image"},
            # Video
            {"model_id": "seedance-2.0", "display_name": "SeeDance 2.0", "capability_type": "video", "is_default": True},
            {"model_id": "kling-v2.1", "display_name": "Kling V2.1", "capability_type": "video"},
            {"model_id": "veo-3.1-fast", "display_name": "VEO 3.1 Fast", "capability_type": "video"},
            {"model_id": "wan-v2.1-i2v", "display_name": "Wan V2.1 图生视频", "capability_type": "video"},
            # TTS
            {"model_id": "tts-1-hd", "display_name": "TTS HD", "capability_type": "tts", "is_default": True},
        ],
    },
    {
        "name": "OpenAI 直连",
        "base_url": "https://api.openai.com/v1",
        "capabilities": "chat,image,tts",
        "is_default": False,
        "models": [
            {"model_id": "gpt-4o", "display_name": "GPT-4o", "capability_type": "chat", "is_default": True},
            {"model_id": "gpt-4o-mini", "display_name": "GPT-4o Mini", "capability_type": "chat"},
            {"model_id": "gpt-4.1", "display_name": "GPT-4.1", "capability_type": "chat"},
            {"model_id": "gpt-4.1-mini", "display_name": "GPT-4.1 Mini", "capability_type": "chat"},
            {"model_id": "dall-e-3", "display_name": "DALL-E 3", "capability_type": "image", "is_default": True},
            {"model_id": "tts-1-hd", "display_name": "TTS HD", "capability_type": "tts", "is_default": True},
            {"model_id": "tts-1", "display_name": "TTS Standard", "capability_type": "tts"},
        ],
    },
    {
        "name": "Anthropic 直连",
        "base_url": "https://api.anthropic.com/v1",
        "capabilities": "chat",
        "is_default": False,
        "models": [
            {"model_id": "claude-sonnet-4-20250514", "display_name": "Claude Sonnet 4", "capability_type": "chat", "is_default": True},
            {"model_id": "claude-3-5-sonnet-20241022", "display_name": "Claude 3.5 Sonnet", "capability_type": "chat"},
            {"model_id": "claude-3-5-haiku-20241022", "display_name": "Claude 3.5 Haiku", "capability_type": "chat"},
        ],
    },
    {
        "name": "OpenRouter",
        "base_url": "https://openrouter.ai/api/v1",
        "capabilities": "chat",
        "is_default": False,
        "models": [
            {"model_id": "openai/gpt-4o", "display_name": "GPT-4o", "capability_type": "chat", "is_default": True},
            {"model_id": "anthropic/claude-sonnet-4", "display_name": "Claude Sonnet 4", "capability_type": "chat"},
            {"model_id": "google/gemini-2.5-pro-preview", "display_name": "Gemini 2.5 Pro", "capability_type": "chat"},
            {"model_id": "deepseek/deepseek-chat", "display_name": "DeepSeek Chat", "capability_type": "chat"},
        ],
    },
]
