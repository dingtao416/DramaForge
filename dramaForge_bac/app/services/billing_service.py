"""
DramaForge v2.0 — Billing Service
===================================
Core business logic for credit balance, transactions, subscriptions.
All balance mutations go through this module to ensure atomicity.
"""

from __future__ import annotations

from datetime import datetime, date, timedelta
from typing import Optional

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.billing import (
    CREDIT_COSTS,
    CreditBalance,
    CreditTransaction,
    Plan,
    Subscription,
    SubscriptionStatus,
    TransactionType,
)


# ═══════════════════════════════════════════════════════════════════
# Balance helpers
# ═══════════════════════════════════════════════════════════════════

async def get_or_create_balance(db: AsyncSession, user_id: int) -> CreditBalance:
    """Get existing balance row or create a new one with 0 credits."""
    result = await db.execute(
        select(CreditBalance).where(CreditBalance.user_id == user_id)
    )
    bal = result.scalar_one_or_none()
    if not bal:
        bal = CreditBalance(user_id=user_id, balance=0, total_earned=0, total_spent=0)
        db.add(bal)
        await db.flush()
    return bal


async def get_balance(db: AsyncSession, user_id: int) -> int:
    """Return the user's current credit balance (0 if none)."""
    bal = await get_or_create_balance(db, user_id)
    return bal.balance


async def add_credits(
    db: AsyncSession,
    user_id: int,
    amount: int,
    tx_type: TransactionType,
    description: str = "",
    ref_id: str | None = None,
) -> CreditBalance:
    """
    Add credits to user balance and record a transaction.
    ``amount`` should be a positive integer.
    """
    if amount <= 0:
        raise ValueError("add_credits amount must be > 0")

    bal = await get_or_create_balance(db, user_id)
    bal.balance += amount
    bal.total_earned += amount

    tx = CreditTransaction(
        user_id=user_id,
        type=tx_type,
        amount=amount,
        balance_after=bal.balance,
        description=description,
        ref_id=ref_id,
    )
    db.add(tx)
    await db.flush()

    logger.info(f"Credits +{amount} for user {user_id} ({tx_type.value}), balance={bal.balance}")
    return bal


async def consume_credits(
    db: AsyncSession,
    user_id: int,
    service_type: str,
    description: str = "",
    ref_id: str | None = None,
) -> CreditBalance:
    """
    Consume credits for a service. Raises ValueError if insufficient.
    The cost is looked up from ``CREDIT_COSTS``.
    """
    cost = CREDIT_COSTS.get(service_type)
    if cost is None:
        raise ValueError(f"Unknown service type: {service_type}")

    bal = await get_or_create_balance(db, user_id)

    if bal.balance < cost:
        raise InsufficientCreditsError(
            required=cost,
            available=bal.balance,
            service_type=service_type,
        )

    bal.balance -= cost
    bal.total_spent += cost

    tx = CreditTransaction(
        user_id=user_id,
        type=TransactionType(service_type),
        amount=-cost,
        balance_after=bal.balance,
        description=description or f"消耗 {cost} 积分: {service_type}",
        ref_id=ref_id,
    )
    db.add(tx)
    await db.flush()

    logger.info(f"Credits -{cost} for user {user_id} ({service_type}), balance={bal.balance}")
    return bal


async def check_credits(db: AsyncSession, user_id: int, service_type: str) -> bool:
    """Check if user has enough credits for a service (does NOT consume)."""
    cost = CREDIT_COSTS.get(service_type, 0)
    bal = await get_balance(db, user_id)
    return bal >= cost


# ═══════════════════════════════════════════════════════════════════
# Daily free credits
# ═══════════════════════════════════════════════════════════════════

async def grant_daily_credits_if_needed(db: AsyncSession, user_id: int) -> int:
    """
    Grant daily free credits to a free-tier user if they haven't received them today.
    Returns the number of credits granted (0 if already granted or not eligible).
    """
    # Check if the user has an active paid subscription
    sub = await get_active_subscription(db, user_id)
    if sub and sub.plan and sub.plan.code != "free":
        return 0  # Paid users don't get daily frees

    # Get the free plan daily credits amount
    free_plan = await db.execute(select(Plan).where(Plan.code == "free"))
    plan = free_plan.scalar_one_or_none()
    daily_amount = plan.daily_credits if plan else 10

    today = date.today().isoformat()

    # Check if already granted today via recent transaction
    result = await db.execute(
        select(CreditTransaction).where(
            CreditTransaction.user_id == user_id,
            CreditTransaction.type == TransactionType.DAILY_GIFT,
            CreditTransaction.ref_id == today,
        )
    )
    if result.scalar_one_or_none():
        return 0  # Already granted today

    # Grant daily credits
    await add_credits(
        db,
        user_id,
        daily_amount,
        TransactionType.DAILY_GIFT,
        description=f"每日赠送 {daily_amount} 积分",
        ref_id=today,
    )
    return daily_amount


# ═══════════════════════════════════════════════════════════════════
# Subscription management
# ═══════════════════════════════════════════════════════════════════

async def get_active_subscription(db: AsyncSession, user_id: int) -> Optional[Subscription]:
    """
    Get the user's currently active subscription (if any).
    Automatically expires subscriptions that have passed their expiry date.
    """
    result = await db.execute(
        select(Subscription)
        .where(
            Subscription.user_id == user_id,
            Subscription.status == SubscriptionStatus.ACTIVE,
        )
        .order_by(Subscription.created_at.desc())
        .limit(1)
    )
    sub = result.scalar_one_or_none()

    # Auto-expire if past expiry date
    if sub and sub.expires_at and sub.expires_at < datetime.utcnow():
        sub.status = SubscriptionStatus.EXPIRED
        await db.flush()
        logger.info(f"Subscription {sub.id} for user {user_id} auto-expired")
        return None

    return sub


async def subscribe(
    db: AsyncSession,
    user_id: int,
    plan_code: str,
) -> Subscription:
    """
    Subscribe a user to a plan. Simulates payment (no real payment gateway).
    Creates the subscription and grants the first month's credits.
    """
    # Find the plan
    result = await db.execute(select(Plan).where(Plan.code == plan_code, Plan.is_active == True))
    plan = result.scalar_one_or_none()
    if not plan:
        raise ValueError(f"Plan not found or inactive: {plan_code}")

    if plan.code == "free":
        raise ValueError("Cannot subscribe to free plan explicitly")

    # Check if user had a previous subscription to this plan (for renewal pricing)
    prev_result = await db.execute(
        select(Subscription).where(
            Subscription.user_id == user_id,
            Subscription.plan_id == plan.id,
        ).limit(1)
    )
    is_renewal = prev_result.scalar_one_or_none() is not None

    # Cancel any existing active subscription
    existing = await get_active_subscription(db, user_id)
    if existing:
        existing.status = SubscriptionStatus.CANCELLED

    # Create new subscription
    now = datetime.utcnow()
    if plan.interval and plan.interval.value == "yearly":
        expires = now + timedelta(days=365)
    else:
        expires = now + timedelta(days=30)

    sub = Subscription(
        user_id=user_id,
        plan_id=plan.id,
        status=SubscriptionStatus.ACTIVE,
        started_at=now,
        expires_at=expires,
        is_renewal=is_renewal,
    )
    db.add(sub)
    await db.flush()

    # Grant monthly credits
    if plan.monthly_credits > 0:
        await add_credits(
            db,
            user_id,
            plan.monthly_credits,
            TransactionType.SUBSCRIPTION_GRANT,
            description=f"订阅到账: {plan.name} — {plan.monthly_credits} 积分",
            ref_id=f"sub_{sub.id}",
        )

    logger.info(f"User {user_id} subscribed to {plan_code}, renewal={is_renewal}")
    return sub


async def get_user_plan_code(db: AsyncSession, user_id: int) -> str:
    """Get the user's current plan code. Returns 'free' if no active subscription."""
    sub = await get_active_subscription(db, user_id)
    if sub and sub.plan:
        return sub.plan.code
    return "free"


# ═══════════════════════════════════════════════════════════════════
# Plan seeding
# ═══════════════════════════════════════════════════════════════════

async def seed_plans(db: AsyncSession) -> None:
    """Insert default plans if they don't exist."""
    from app.models.billing import PlanInterval

    plans_data = [
        {
            "code": "free",
            "name": "免费版",
            "interval": None,
            "price_cny": 0,
            "renewal_price_cny": 0,
            "monthly_credits": 0,
            "daily_credits": 10,
            "description": "每日赠送 10 积分，当日清零",
            "sort_order": 0,
        },
        {
            "code": "basic_monthly",
            "name": "基础会员 · 月付",
            "interval": PlanInterval.MONTHLY,
            "price_cny": 39,
            "renewal_price_cny": 79,
            "monthly_credits": 1200,
            "daily_credits": 0,
            "description": "每月 1200 积分，首月 ¥39，续费 ¥79/月",
            "sort_order": 1,
        },
        {
            "code": "basic_yearly",
            "name": "基础会员 · 年付",
            "interval": PlanInterval.YEARLY,
            "price_cny": 379,
            "renewal_price_cny": 759,
            "monthly_credits": 1200,
            "daily_credits": 0,
            "description": "每月 1200 积分，首年 ¥379，续费 ¥759/年",
            "sort_order": 2,
        },
    ]

    for data in plans_data:
        result = await db.execute(select(Plan).where(Plan.code == data["code"]))
        if not result.scalar_one_or_none():
            plan = Plan(**data)
            db.add(plan)
            logger.info(f"Seeded plan: {data['code']}")

    await db.commit()


# ═══════════════════════════════════════════════════════════════════
# Transaction history
# ═══════════════════════════════════════════════════════════════════

async def get_transactions(
    db: AsyncSession,
    user_id: int,
    page: int = 1,
    page_size: int = 20,
) -> list[CreditTransaction]:
    """Get paginated transaction history for a user."""
    result = await db.execute(
        select(CreditTransaction)
        .where(CreditTransaction.user_id == user_id)
        .order_by(CreditTransaction.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return list(result.scalars().all())


# ═══════════════════════════════════════════════════════════════════
# Error classes
# ═══════════════════════════════════════════════════════════════════

class InsufficientCreditsError(Exception):
    """Raised when user doesn't have enough credits for a service."""

    def __init__(self, required: int, available: int, service_type: str):
        self.required = required
        self.available = available
        self.service_type = service_type
        super().__init__(
            f"积分不足: 需要 {required}，当前 {available} (服务: {service_type})"
        )
