"""
DramaForge v2.0 — Payment ORM Models
======================================
Payment orders, payment channels, and agreement records.
Supports: WeChat Pay (Native), Alipay (Precreate), Douyin Pay.
"""

from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Boolean, DateTime, Enum as SQLEnum, Float, ForeignKey,
    Integer, String, Text, func, JSON,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.billing import Plan


# ──────────── Enums ────────────────────────────────────────────────

class PaymentChannel(str, enum.Enum):
    """Supported payment channels."""
    WECHAT = "wechat"          # 微信支付 (Native 扫码)
    ALIPAY = "alipay"          # 支付宝 (当面付 precreate)
    DOUYIN = "douyin"          # 抖音支付 (担保交易)


class OrderStatus(str, enum.Enum):
    """Payment order lifecycle."""
    PENDING = "pending"            # 待支付
    PAID = "paid"                  # 已支付
    CLOSED = "closed"             # 已关闭 (超时/手动)
    REFUNDED = "refunded"          # 已退款
    REFUND_PARTIAL = "refund_partial"  # 部分退款
    FAILED = "failed"              # 支付失败


class OrderType(str, enum.Enum):
    """What the user is paying for."""
    SUBSCRIPTION = "subscription"  # 订阅套餐
    CREDIT_PACK = "credit_pack"    # 积分包


# ──────────── 积分包定义 ────────────────────────────────────────────

CREDIT_PACKS: list[dict] = [
    {"code": "pack_50",   "name": "50 积分",   "credits": 50,   "price_cny": 9.9},
    {"code": "pack_200",  "name": "200 积分",  "credits": 200,  "price_cny": 29.9},
    {"code": "pack_500",  "name": "500 积分",  "credits": 500,  "price_cny": 59.9},
    {"code": "pack_1200", "name": "1200 积分", "credits": 1200, "price_cny": 99.9},
]


# ──────────── PaymentOrder (支付订单) ─────────────────────────────

class PaymentOrder(Base):
    """
    A single payment order.
    Created when user initiates checkout; updated via webhook callback.
    """

    __tablename__ = "payment_orders"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # ── Identifiers ──
    order_no: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True,
        comment="Internal order number: DF{timestamp}{random}",
    )
    trade_no: Mapped[Optional[str]] = mapped_column(
        String(128), nullable=True, index=True,
        comment="Third-party transaction ID (from WeChat/Alipay/Douyin)",
    )

    # ── User & Product ──
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    order_type: Mapped[OrderType] = mapped_column(
        SQLEnum(OrderType), nullable=False,
        comment="subscription | credit_pack",
    )
    product_code: Mapped[str] = mapped_column(
        String(50), nullable=False,
        comment="Plan code or credit pack code",
    )
    product_name: Mapped[str] = mapped_column(
        String(200), nullable=False,
        comment="Display name for the product",
    )

    # ── Payment ──
    channel: Mapped[PaymentChannel] = mapped_column(
        SQLEnum(PaymentChannel), nullable=False,
    )
    amount_cny: Mapped[float] = mapped_column(
        Float, nullable=False,
        comment="Total amount in CNY",
    )
    amount_fen: Mapped[int] = mapped_column(
        Integer, nullable=False,
        comment="Total amount in fen (cents) for API calls",
    )
    status: Mapped[OrderStatus] = mapped_column(
        SQLEnum(OrderStatus), default=OrderStatus.PENDING, nullable=False, index=True,
    )

    # ── QR Code ──
    qr_url: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True,
        comment="Payment QR code URL (code_url from provider)",
    )
    qr_image_base64: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        comment="Generated QR code image as base64 data URI",
    )

    # ── Agreement ──
    agreement_accepted: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False,
        comment="User has accepted the service agreement",
    )
    agreement_version: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True,
        comment="Agreement version user accepted, e.g. v1.0",
    )

    # ── Callback & Meta ──
    callback_raw: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        comment="Raw JSON from payment provider callback",
    )
    meta: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True,
        comment="Extra metadata (credits granted, plan details, etc.)",
    )

    # ── Refund ──
    refund_amount_fen: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False,
    )
    refund_reason: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True,
    )

    # ── Timestamps ──
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False, index=True,
    )
    paid_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True,
    )
    expired_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True,
        comment="Order auto-close time (typically +30min from creation)",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False,
    )

    # ── Relationships ──
    user: Mapped["User"] = relationship("User", backref="payment_orders")

    def __repr__(self) -> str:
        return f"<PaymentOrder {self.order_no} user={self.user_id} status={self.status.value} ¥{self.amount_cny}>"


# ──────────── UserAgreement (用户协议记录) ────────────────────────

class UserAgreement(Base):
    """
    Records when a user accepts a service/payment agreement.
    Required before payment can proceed.
    """

    __tablename__ = "user_agreements"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    agreement_type: Mapped[str] = mapped_column(
        String(50), nullable=False,
        comment="payment_tos | privacy_policy | subscription_auto_renew",
    )
    version: Mapped[str] = mapped_column(
        String(20), nullable=False, default="v1.0",
    )
    accepted: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False,
    )
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45), nullable=True,
    )
    user_agent: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False,
    )

    user: Mapped["User"] = relationship("User", backref="agreements")

    def __repr__(self) -> str:
        return f"<UserAgreement user={self.user_id} type={self.agreement_type} v={self.version}>"
