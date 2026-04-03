"""
DramaForge v2.0 — Billing ORM Models
======================================
Subscription plans, user subscriptions, credit balances, and transaction logs.
"""

from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Boolean, DateTime, Enum as SQLEnum, Float, ForeignKey,
    Integer, String, Text, func,
)
from sqlalchemy.orm import Mapped, backref, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


# ──────────── Enums ────────────────────────────────────────────────

class PlanInterval(str, enum.Enum):
    """Billing interval for subscription plans."""
    MONTHLY = "monthly"
    YEARLY = "yearly"


class SubscriptionStatus(str, enum.Enum):
    """Subscription lifecycle status."""
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class TransactionType(str, enum.Enum):
    """Credit transaction types."""
    # 消耗
    CHAT_DEFAULT = "chat_default"          # 普通对话
    CHAT_PREMIUM = "chat_premium"          # 高级模型对话
    IMAGE_DEFAULT = "image_default"        # 默认图片生成
    IMAGE_PREMIUM = "image_premium"        # MJ 等高级图片
    VIDEO_DEFAULT_5S = "video_default_5s"  # 默认视频 5s
    VIDEO_PREMIUM_5S = "video_premium_5s"  # 高质量视频 5s
    VIDEO_DEFAULT_10S = "video_default_10s"
    VIDEO_PREMIUM_10S = "video_premium_10s"
    TTS = "tts"                            # 语音合成
    SCRIPT_GEN = "script_gen"              # 剧本自动生成
    STORYBOARD_GEN = "storyboard_gen"      # 分镜自动生成
    # 充值 / 赠送
    DAILY_GIFT = "daily_gift"              # 免费用户每日赠送
    SUBSCRIPTION_GRANT = "subscription_grant"  # 订阅月度到账
    PURCHASE = "purchase"                  # 单独购买积分
    ADMIN_ADJUST = "admin_adjust"          # 管理员调整
    REFUND = "refund"                      # 退款


# ──────────── 积分消耗定价表 ────────────────────────────────────────

CREDIT_COSTS: dict[str, int] = {
    TransactionType.CHAT_DEFAULT.value: 1,
    TransactionType.CHAT_PREMIUM.value: 3,
    TransactionType.IMAGE_DEFAULT.value: 5,
    TransactionType.IMAGE_PREMIUM.value: 10,
    TransactionType.VIDEO_DEFAULT_5S.value: 20,
    TransactionType.VIDEO_PREMIUM_5S.value: 40,
    TransactionType.VIDEO_DEFAULT_10S.value: 40,
    TransactionType.VIDEO_PREMIUM_10S.value: 80,
    TransactionType.TTS.value: 2,
    TransactionType.SCRIPT_GEN.value: 10,
    TransactionType.STORYBOARD_GEN.value: 15,
}


# ──────────── Plan (套餐定义) ────────────────────────────────────

class Plan(Base):
    """Available subscription plans."""

    __tablename__ = "plans"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)          # "免费版" / "基础会员"
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)  # "free" / "basic_monthly" / "basic_yearly"
    interval: Mapped[Optional[PlanInterval]] = mapped_column(
        SQLEnum(PlanInterval), nullable=True
    )  # None for free plan
    price_cny: Mapped[float] = mapped_column(Float, default=0, nullable=False)          # 首次价格
    renewal_price_cny: Mapped[float] = mapped_column(Float, default=0, nullable=False)  # 续费价格
    monthly_credits: Mapped[int] = mapped_column(Integer, default=0, nullable=False)    # 每月到账积分
    daily_credits: Mapped[int] = mapped_column(Integer, default=0, nullable=False)      # 每日赠送 (仅免费版)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<Plan id={self.id} code={self.code} price={self.price_cny}>"


# ──────────── Subscription (用户订阅) ─────────────────────────────

class Subscription(Base):
    """User subscription records."""

    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    plan_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("plans.id", ondelete="RESTRICT"), nullable=False
    )
    status: Mapped[SubscriptionStatus] = mapped_column(
        SQLEnum(SubscriptionStatus), default=SubscriptionStatus.ACTIVE, nullable=False
    )
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)  # None = never (free)
    is_renewal: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", backref="subscriptions")
    plan: Mapped["Plan"] = relationship("Plan", lazy="joined")

    def __repr__(self) -> str:
        return f"<Subscription id={self.id} user={self.user_id} plan={self.plan_id} status={self.status.value}>"


# ──────────── CreditBalance (积分余额) ────────────────────────────

class CreditBalance(Base):
    """User credit balance — single row per user, updated atomically."""

    __tablename__ = "credit_balances"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"),
        unique=True, nullable=False, index=True
    )
    balance: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_earned: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # 累计获得
    total_spent: Mapped[int] = mapped_column(Integer, default=0, nullable=False)   # 累计消耗

    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", backref=backref("credit_balance", uselist=False))

    def __repr__(self) -> str:
        return f"<CreditBalance user={self.user_id} balance={self.balance}>"


# ──────────── CreditTransaction (积分流水) ────────────────────────

class CreditTransaction(Base):
    """Credit transaction log — every credit change is recorded."""

    __tablename__ = "credit_transactions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    type: Mapped[TransactionType] = mapped_column(
        SQLEnum(TransactionType), nullable=False, index=True
    )
    amount: Mapped[int] = mapped_column(Integer, nullable=False)              # 正数=收入, 负数=支出
    balance_after: Mapped[int] = mapped_column(Integer, nullable=False)       # 变动后余额
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    # 关联的业务 ID (如 conversation_id, message_id 等)
    ref_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False, index=True
    )

    # Relationships
    user: Mapped["User"] = relationship("User", backref="credit_transactions")

    def __repr__(self) -> str:
        return f"<CreditTransaction id={self.id} user={self.user_id} type={self.type.value} amount={self.amount}>"
