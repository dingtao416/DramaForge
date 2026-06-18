"""Built-in media provider templates."""

BUILTIN_CATALOG = [
    {
        "name": "laozhang.ai Relay",
        "provider_type": "openai_compatible",
        "auth_type": "bearer",
        "base_url": "https://api.laozhang.ai/v1",
        "priority": 10,
        "models": [
            {"model_id": "gpt-image-1-mini", "display_name": "GPT Image Mini", "capability": "image", "is_default": True},
            {"model_id": "sora_image", "display_name": "Sora Image", "capability": "image"},
            {"model_id": "veo-3.1-fast", "display_name": "Veo 3.1 Fast", "capability": "video", "is_default": True},
            {"model_id": "seedance-2.0", "display_name": "SeeDance 2.0", "capability": "video"},
        ],
    },
    {
        "name": "OpenAI Native",
        "provider_type": "openai_native",
        "auth_type": "bearer",
        "base_url": "https://api.openai.com/v1",
        "priority": 20,
        "models": [
            {
                "model_id": "gpt-image-1",
                "display_name": "GPT Image",
                "capability": "image",
                "is_default": True,
                "default_params_json": {"response_format": "b64_json"},
            },
            {
                "model_id": "sora-2",
                "display_name": "Sora 2",
                "capability": "video",
                "is_default": True,
                "default_params_json": {"seconds": "8", "size": "1280x720"},
            },
        ],
    },
    {
        "name": "Replicate",
        "provider_type": "replicate",
        "auth_type": "bearer",
        "base_url": "https://api.replicate.com/v1",
        "priority": 40,
        "models": [
            {"model_id": "black-forest-labs/flux-schnell", "display_name": "Flux Schnell", "capability": "image", "is_default": True},
            {"model_id": "kwaivgi/kling-v1.6-standard", "display_name": "Kling Video", "capability": "video", "is_default": True},
        ],
    },
    {
        "name": "fal.ai",
        "provider_type": "fal",
        "auth_type": "api-key",
        "base_url": "https://fal.run",
        "priority": 45,
        "config_json": {
            "api_key_header": "Authorization",
            "auth_prefix": "Key",
            "submit_path": "/fal-ai/flux/schnell",
        },
        "models": [
            {"model_id": "fal-ai/flux/schnell", "display_name": "Flux Schnell", "capability": "image", "is_default": True},
            {"model_id": "fal-ai/kling-video/v1.6/standard/image-to-video", "display_name": "Kling I2V", "capability": "video", "is_default": True},
        ],
    },
    {
        "name": "Runway",
        "provider_type": "runway",
        "auth_type": "bearer",
        "base_url": "https://api.dev.runwayml.com/v1",
        "priority": 50,
        "headers_json": {"X-Runway-Version": "2024-11-06"},
        "config_json": {"submit_path": "/image_to_video", "status_path": "/tasks/{id}"},
        "models": [
            {"model_id": "gen4_turbo", "display_name": "Gen-4 Turbo", "capability": "video", "is_default": True},
        ],
    },
    {
        "name": "Luma",
        "provider_type": "luma",
        "auth_type": "bearer",
        "base_url": "https://api.lumalabs.ai/dream-machine/v1",
        "priority": 55,
        "config_json": {"submit_path": "/generations", "status_path": "/generations/{id}"},
        "models": [
            {"model_id": "ray-2", "display_name": "Ray 2", "capability": "video", "is_default": True},
        ],
    },
    {
        "name": "Volcengine Ark",
        "provider_type": "volcengine_ark",
        "auth_type": "bearer",
        "base_url": "https://ark.cn-beijing.volces.com/api/v3",
        "priority": 60,
        "config_json": {"submit_path": "/contents/generations/tasks", "status_path": "/contents/generations/tasks/{id}"},
        "models": [
            {"model_id": "seedream-4-0", "display_name": "Seedream", "capability": "image", "is_default": True},
            {"model_id": "seedance-1-0-pro", "display_name": "Seedance", "capability": "video", "is_default": True},
        ],
    },
    {
        "name": "DashScope",
        "provider_type": "dashscope",
        "auth_type": "bearer",
        "base_url": "https://dashscope.aliyuncs.com/api/v1",
        "priority": 65,
        "headers_json": {"X-DashScope-Async": "enable"},
        "config_json": {"submit_path": "/services/aigc/text2image/image-synthesis", "status_path": "/tasks/{id}"},
        "models": [
            {"model_id": "wanx2.1-t2i-turbo", "display_name": "Wanx T2I Turbo", "capability": "image", "is_default": True},
            {"model_id": "wan2.1-t2v-turbo", "display_name": "Wan T2V Turbo", "capability": "video", "is_default": True},
        ],
    },
    {
        "name": "Google Vertex",
        "provider_type": "google_vertex",
        "auth_type": "bearer",
        "base_url": "",
        "priority": 70,
        "models": [
            {"model_id": "imagen-4.0-generate-preview-06-06", "display_name": "Imagen 4", "capability": "image", "is_default": True},
            {"model_id": "veo-3.0-generate-preview", "display_name": "Veo 3", "capability": "video", "is_default": True},
        ],
    },
]
