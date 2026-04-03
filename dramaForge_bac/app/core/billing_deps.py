"""
DramaForge v2.0 — Billing Dependencies
========================================
FastAPI dependency helpers for credit consumption and plan gating.
Use these in route handlers to enforce billing rules.
"""

from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.billing_service import (
    InsufficientCreditsError,
    consume_credits,
    get_user_plan_code,
    grant_daily_credits_if_needed,
)


async def require_credits(
    db: AsyncSession,
    user_id: int,
    service_type: str,
    description: str = "",
    ref_id: str | None = None,
) -> None:
    """
    Consume credits for a service. Raises HTTP 402 if insufficient.
    Call this at the top of any endpoint that costs credits.
    """
    # Auto-grant daily credits first
    await grant_daily_credits_if_needed(db, user_id)

    try:
        await consume_credits(db, user_id, service_type, description, ref_id)
    except InsufficientCreditsError as e:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "code": "INSUFFICIENT_CREDITS",
                "message": str(e),
                "required": e.required,
                "available": e.available,
                "service_type": e.service_type,
            },
        )


async def require_paid_plan(
    db: AsyncSession,
    user_id: int,
    feature_name: str = "",
) -> str:
    """
    Ensure the user has an active paid subscription.
    Returns the plan code. Raises HTTP 403 if free.
    """
    plan_code = await get_user_plan_code(db, user_id)
    if plan_code == "free":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "PAID_PLAN_REQUIRED",
                "message": f"此功能需要付费会员: {feature_name}" if feature_name else "此功能需要付费会员",
                "feature": feature_name,
                "current_plan": "free",
            },
        )
    return plan_code


async def require_premium_model_access(
    db: AsyncSession,
    user_id: int,
    model_id: str,
) -> None:
    """
    Block free-tier users from using premium/expensive models.
    Premium models: claude-*, gpt-4o, midjourney-*, kling-*, etc.
    """
    PREMIUM_MODEL_PREFIXES = [
        "claude", "gpt-4o", "gpt-4.1", "midjourney",
        "kling", "runway", "sora", "veo-3",
    ]
    model_lower = (model_id or "").lower()

    # Check if the requested model is premium
    is_premium_model = any(
        model_lower.startswith(prefix) for prefix in PREMIUM_MODEL_PREFIXES
    ) and "mini" not in model_lower

    if not is_premium_model:
        return  # Non-premium models are always accessible

    plan_code = await get_user_plan_code(db, user_id)
    if plan_code == "free":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "PREMIUM_MODEL_RESTRICTED",
                "message": f"高阶模型 {model_id} 需要付费会员才能使用",
                "model": model_id,
                "current_plan": "free",
            },
        )


# Free-tier feature restrictions
FREE_TIER_RESTRICTIONS: dict[str, bool] = {
    "watermark_free": False,       # 免费版有水印
    "fast_generation": False,      # 免费版无快速通道
    "premium_models": False,       # 免费版无高阶模型
    "unlimited_assets": False,     # 免费版资产库有限
    "all_ai_features": True,       # 所有 AI 功能都可用（需要积分）
}

PAID_TIER_FEATURES: dict[str, bool] = {
    "watermark_free": True,
    "fast_generation": True,
    "premium_models": True,
    "unlimited_assets": True,
    "all_ai_features": True,
}


# Service type labels (Chinese) for generating descriptions
SERVICE_LABELS: dict[str, str] = {
    "chat_default": "AI 对话",
    "chat_premium": "AI 对话 (高级模型)",
    "image_default": "图片生成",
    "image_premium": "图片生成 (高级)",
    "video_default_5s": "视频生成 5s",
    "video_premium_5s": "视频生成 5s (高质量)",
    "video_default_10s": "视频生成 10s",
    "video_premium_10s": "视频生成 10s (高质量)",
    "tts": "语音合成",
    "script_gen": "剧本生成",
    "storyboard_gen": "分镜生成",
}
