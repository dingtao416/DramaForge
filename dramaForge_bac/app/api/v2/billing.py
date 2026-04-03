"""
DramaForge v2.0 — Billing API
================================
Endpoints for credits, subscriptions, plans, and transactions.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.core.security import CurrentUser, DbSession
from app.models.billing import CREDIT_COSTS, Plan, TransactionType
from app.services.billing_service import (
    InsufficientCreditsError,
    add_credits,
    get_active_subscription,
    get_balance,
    get_or_create_balance,
    get_transactions,
    get_user_plan_code,
    grant_daily_credits_if_needed,
    subscribe,
)
from sqlalchemy import select

router = APIRouter(prefix="/billing", tags=["Billing"])


# ═══════════════════════════════════════════════════════════════════
# Schemas
# ═══════════════════════════════════════════════════════════════════

class BalanceResponse(BaseModel):
    balance: int
    total_earned: int
    total_spent: int
    plan_code: str  # "free" / "basic_monthly" / "basic_yearly"
    plan_name: str

class PlanResponse(BaseModel):
    id: int
    code: str
    name: str
    interval: str | None
    price_cny: float
    renewal_price_cny: float
    monthly_credits: int
    daily_credits: int
    description: str | None
    sort_order: int

    model_config = {"from_attributes": True}


class SubscriptionResponse(BaseModel):
    id: int
    plan_code: str
    plan_name: str
    status: str
    started_at: datetime
    expires_at: datetime | None
    is_renewal: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class TransactionResponse(BaseModel):
    id: int
    type: str
    amount: int
    balance_after: int
    description: str | None
    ref_id: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class SubscribeRequest(BaseModel):
    plan_code: str = Field(..., description="Plan code: basic_monthly or basic_yearly")


class PricingResponse(BaseModel):
    """Service pricing table."""
    services: dict[str, int]  # service_type -> cost


class CreditCheckResponse(BaseModel):
    """Result of a credit sufficiency check."""
    sufficient: bool
    balance: int
    required: int
    service_type: str


# ═══════════════════════════════════════════════════════════════════
# Endpoints
# ═══════════════════════════════════════════════════════════════════

@router.get("/balance", response_model=BalanceResponse)
async def get_my_balance(user: CurrentUser, db: DbSession):
    """
    Get current user's credit balance and plan info.
    Also triggers daily free credit grant if applicable.
    """
    # Auto-grant daily credits for free users
    await grant_daily_credits_if_needed(db, user.id)
    await db.commit()

    bal = await get_or_create_balance(db, user.id)
    plan_code = await get_user_plan_code(db, user.id)

    # Get plan name
    result = await db.execute(select(Plan).where(Plan.code == plan_code))
    plan = result.scalar_one_or_none()
    plan_name = plan.name if plan else "免费版"

    return BalanceResponse(
        balance=bal.balance,
        total_earned=bal.total_earned,
        total_spent=bal.total_spent,
        plan_code=plan_code,
        plan_name=plan_name,
    )


@router.get("/plans", response_model=list[PlanResponse])
async def list_plans(db: DbSession):
    """List all available subscription plans (public endpoint)."""
    result = await db.execute(
        select(Plan).where(Plan.is_active == True).order_by(Plan.sort_order)
    )
    plans = result.scalars().all()
    return [
        PlanResponse(
            id=p.id,
            code=p.code,
            name=p.name,
            interval=p.interval.value if p.interval else None,
            price_cny=p.price_cny,
            renewal_price_cny=p.renewal_price_cny,
            monthly_credits=p.monthly_credits,
            daily_credits=p.daily_credits,
            description=p.description,
            sort_order=p.sort_order,
        )
        for p in plans
    ]


@router.get("/subscription", response_model=SubscriptionResponse | None)
async def get_my_subscription(user: CurrentUser, db: DbSession):
    """Get current user's active subscription."""
    sub = await get_active_subscription(db, user.id)
    if not sub:
        return None
    return SubscriptionResponse(
        id=sub.id,
        plan_code=sub.plan.code if sub.plan else "free",
        plan_name=sub.plan.name if sub.plan else "免费版",
        status=sub.status.value,
        started_at=sub.started_at,
        expires_at=sub.expires_at,
        is_renewal=sub.is_renewal,
        created_at=sub.created_at,
    )


@router.post("/subscribe", response_model=SubscriptionResponse)
async def subscribe_to_plan(
    request: SubscribeRequest,
    user: CurrentUser,
    db: DbSession,
):
    """
    Subscribe to a plan (simulated payment).
    In production, this would integrate with a payment gateway.
    """
    try:
        sub = await subscribe(db, user.id, request.plan_code)
        await db.commit()
        return SubscriptionResponse(
            id=sub.id,
            plan_code=sub.plan.code if sub.plan else request.plan_code,
            plan_name=sub.plan.name if sub.plan else "",
            status=sub.status.value,
            started_at=sub.started_at,
            expires_at=sub.expires_at,
            is_renewal=sub.is_renewal,
            created_at=sub.created_at,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/transactions", response_model=list[TransactionResponse])
async def list_transactions(
    user: CurrentUser,
    db: DbSession,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """Get paginated credit transaction history."""
    txs = await get_transactions(db, user.id, page, page_size)
    return [
        TransactionResponse(
            id=tx.id,
            type=tx.type.value,
            amount=tx.amount,
            balance_after=tx.balance_after,
            description=tx.description,
            ref_id=tx.ref_id,
            created_at=tx.created_at,
        )
        for tx in txs
    ]


@router.get("/pricing", response_model=PricingResponse)
async def get_pricing():
    """Get the service pricing table (public endpoint)."""
    return PricingResponse(services=CREDIT_COSTS)


class FeaturesResponse(BaseModel):
    """User feature access based on plan."""
    plan_code: str
    plan_name: str
    watermark_free: bool
    fast_generation: bool
    premium_models: bool
    unlimited_assets: bool
    all_ai_features: bool


@router.get("/features", response_model=FeaturesResponse)
async def get_features(user: CurrentUser, db: DbSession):
    """Get the feature access flags for the current user's plan."""
    from app.core.billing_deps import FREE_TIER_RESTRICTIONS, PAID_TIER_FEATURES
    plan_code = await get_user_plan_code(db, user.id)

    result = await db.execute(select(Plan).where(Plan.code == plan_code))
    plan = result.scalar_one_or_none()
    plan_name = plan.name if plan else "免费版"

    features = PAID_TIER_FEATURES if plan_code != "free" else FREE_TIER_RESTRICTIONS
    return FeaturesResponse(
        plan_code=plan_code,
        plan_name=plan_name,
        **features,
    )


@router.get("/check-credits", response_model=CreditCheckResponse)
async def check_credits_endpoint(
    user: CurrentUser,
    db: DbSession,
    service_type: str = Query(..., description="Service type to check"),
):
    """Check if user has enough credits for a given service."""
    cost = CREDIT_COSTS.get(service_type, 0)
    balance = await get_balance(db, user.id)
    return CreditCheckResponse(
        sufficient=balance >= cost,
        balance=balance,
        required=cost,
        service_type=service_type,
    )
