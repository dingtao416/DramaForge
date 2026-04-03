"""
DramaForge v2.0 — Payment Service
====================================
Business logic for payment order lifecycle:
  create → poll/callback → fulfill (subscribe + grant credits)
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Optional

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.billing import Plan, TransactionType
from app.models.payment import (
    CREDIT_PACKS,
    OrderStatus,
    OrderType,
    PaymentChannel,
    PaymentOrder,
    UserAgreement,
)
from app.services.billing_service import add_credits, subscribe
from app.services.payment_gateway import (
    PaymentProviderError,
    generate_order_no,
    payment_gateway,
)

# Agreement version
CURRENT_AGREEMENT_VERSION = "v1.0"

# Notify URL base (override in .env or config)
NOTIFY_URL_BASE = "https://api.dramaforge.com"  # Will use settings in production


# ═══════════════════════════════════════════════════════════════════
# Agreement
# ═══════════════════════════════════════════════════════════════════

async def check_agreement(
    db: AsyncSession,
    user_id: int,
    agreement_type: str = "payment_tos",
) -> bool:
    """Check if user has accepted the current version of the agreement."""
    result = await db.execute(
        select(UserAgreement).where(
            UserAgreement.user_id == user_id,
            UserAgreement.agreement_type == agreement_type,
            UserAgreement.version == CURRENT_AGREEMENT_VERSION,
            UserAgreement.accepted == True,
        )
    )
    return result.scalar_one_or_none() is not None


async def accept_agreement(
    db: AsyncSession,
    user_id: int,
    agreement_type: str = "payment_tos",
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> UserAgreement:
    """Record that a user has accepted the agreement."""
    agreement = UserAgreement(
        user_id=user_id,
        agreement_type=agreement_type,
        version=CURRENT_AGREEMENT_VERSION,
        accepted=True,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(agreement)
    await db.flush()
    logger.info(f"User {user_id} accepted {agreement_type} {CURRENT_AGREEMENT_VERSION}")
    return agreement


# ═══════════════════════════════════════════════════════════════════
# Order creation
# ═══════════════════════════════════════════════════════════════════

def _resolve_product(order_type: str, product_code: str) -> dict:
    """
    Look up product details from code.
    Returns: { name, price_cny, credits (if pack), plan_code (if sub) }
    """
    if order_type == OrderType.CREDIT_PACK.value:
        for pack in CREDIT_PACKS:
            if pack["code"] == product_code:
                return {
                    "name": f"DramaForge {pack['name']}",
                    "price_cny": pack["price_cny"],
                    "credits": pack["credits"],
                }
        raise ValueError(f"Unknown credit pack: {product_code}")

    # Subscription — price resolved from DB later
    return {"name": "", "price_cny": 0, "plan_code": product_code}


async def create_payment_order(
    db: AsyncSession,
    user_id: int,
    order_type: str,
    product_code: str,
    channel: str,
    agreement_accepted: bool = False,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> PaymentOrder:
    """
    Create a payment order and call the payment provider to get a QR code.

    Args:
        order_type: "subscription" or "credit_pack"
        product_code: plan code ("basic_monthly") or pack code ("pack_200")
        channel: "wechat" | "alipay" | "douyin"
        agreement_accepted: must be True or raises error

    Returns:
        PaymentOrder with qr_url and qr_image_base64 populated
    """

    # ── 1. Verify agreement ──
    if not agreement_accepted:
        # Check if user previously accepted
        has_agreed = await check_agreement(db, user_id)
        if not has_agreed:
            raise AgreementNotAcceptedError(
                "请先阅读并同意《DramaForge 服务协议》和《支付协议》"
            )
    else:
        # Record fresh acceptance
        await accept_agreement(db, user_id, "payment_tos", ip_address, user_agent)

    # ── 2. Resolve product & amount ──
    if order_type == OrderType.SUBSCRIPTION.value:
        result = await db.execute(
            select(Plan).where(Plan.code == product_code, Plan.is_active == True)
        )
        plan = result.scalar_one_or_none()
        if not plan:
            raise ValueError(f"套餐不存在或已下架: {product_code}")
        if plan.code == "free":
            raise ValueError("免费套餐无需支付")

        # Check if renewal
        from app.services.billing_service import get_active_subscription
        existing_sub = await get_active_subscription(db, user_id)
        is_renewal = existing_sub is not None

        amount_cny = plan.renewal_price_cny if is_renewal else plan.price_cny
        product_name = f"DramaForge {plan.name}"
        meta = {"plan_id": plan.id, "plan_code": plan.code, "is_renewal": is_renewal,
                "monthly_credits": plan.monthly_credits}
    else:
        product_info = _resolve_product(order_type, product_code)
        amount_cny = product_info["price_cny"]
        product_name = product_info["name"]
        meta = {"credits": product_info["credits"], "pack_code": product_code}

    amount_fen = int(round(amount_cny * 100))

    # ── 3. Generate order number ──
    order_no = generate_order_no()

    # ── 4. Build notify URL ──
    from app.core.config import settings
    base_url = getattr(settings, "payment_notify_base_url", NOTIFY_URL_BASE)
    notify_url = f"{base_url}/api/v2/payment/callback/{channel}"

    # ── 5. Call payment provider ──
    try:
        provider_result = await payment_gateway.create_order(
            channel=channel,
            order_no=order_no,
            amount_fen=amount_fen,
            description=product_name,
            notify_url=notify_url,
            expire_minutes=30,
        )
    except PaymentProviderError as e:
        logger.error(f"Payment provider error: {e}")
        raise

    # ── 6. Persist order ──
    order = PaymentOrder(
        order_no=order_no,
        trade_no=provider_result.get("trade_no"),
        user_id=user_id,
        order_type=OrderType(order_type),
        product_code=product_code,
        product_name=product_name,
        channel=PaymentChannel(channel),
        amount_cny=amount_cny,
        amount_fen=amount_fen,
        status=OrderStatus.PENDING,
        qr_url=provider_result.get("code_url"),
        qr_image_base64=provider_result.get("qr_base64"),
        agreement_accepted=True,
        agreement_version=CURRENT_AGREEMENT_VERSION,
        meta=meta,
        expired_at=datetime.utcnow() + timedelta(minutes=30),
    )
    db.add(order)
    await db.flush()

    logger.info(f"Created payment order {order_no} for user {user_id}: ¥{amount_cny} via {channel}")
    return order


# ═══════════════════════════════════════════════════════════════════
# Fulfillment (after successful payment)
# ═══════════════════════════════════════════════════════════════════

async def fulfill_order(db: AsyncSession, order: PaymentOrder) -> None:
    """
    Grant the user their purchase after successful payment.
    - Subscription: call subscribe() which handles plan switch + credit grant
    - Credit pack: add credits directly

    Idempotent: uses meta.fulfilled flag to prevent double-granting.
    """
    if order.status != OrderStatus.PAID:
        logger.warning(f"Attempted to fulfill non-paid order {order.order_no}")
        return

    meta = order.meta or {}

    # Idempotency guard: check if already fulfilled
    if meta.get("fulfilled"):
        logger.info(f"Order {order.order_no} already fulfilled, skipping")
        return

    if order.order_type == OrderType.SUBSCRIPTION:
        plan_code = meta.get("plan_code", order.product_code)
        try:
            await subscribe(db, order.user_id, plan_code)
            logger.info(f"Fulfilled subscription for user {order.user_id}: {plan_code}")
        except ValueError as e:
            logger.error(f"Subscription fulfillment failed: {e}")
            raise

    elif order.order_type == OrderType.CREDIT_PACK:
        credits = meta.get("credits", 0)
        if credits > 0:
            await add_credits(
                db,
                order.user_id,
                credits,
                TransactionType.PURCHASE,
                description=f"购买积分包: {order.product_name}",
                ref_id=f"order_{order.order_no}",
            )
            logger.info(f"Fulfilled credit pack for user {order.user_id}: +{credits}")

    # Mark as fulfilled to prevent double-granting
    if order.meta is None:
        order.meta = {}
    order.meta["fulfilled"] = True
    order.meta["fulfilled_at"] = datetime.utcnow().isoformat()
    # Force SQLAlchemy to detect JSON mutation
    from sqlalchemy.orm.attributes import flag_modified
    flag_modified(order, "meta")

    await db.flush()


# ═══════════════════════════════════════════════════════════════════
# Callback processing
# ═══════════════════════════════════════════════════════════════════

async def process_callback(
    db: AsyncSession,
    channel: str,
    headers: dict[str, str],
    body: bytes,
) -> PaymentOrder | None:
    """
    Process a payment callback from a provider.
    Verifies signature, finds order, updates status, and fulfills if paid.
    Returns the updated order or None if verification failed.

    Security checks:
    - Signature verification (via adapter)
    - Amount verification (callback amount must match order amount)
    - Status transition validation (only PENDING → PAID allowed)
    - Idempotency (already-paid orders are skipped)
    """
    from app.core.config import settings as app_settings

    # ── Security: Block mock-mode callbacks in production ──
    is_production = not app_settings.debug
    adapter = payment_gateway.get_adapter(channel)
    is_mock = not adapter._is_configured()

    if is_production and is_mock:
        logger.critical(
            f"[SECURITY] Callback received for unconfigured channel '{channel}' "
            f"in production mode — REJECTING. This may be a forgery attempt."
        )
        return None

    # Verify callback with the provider adapter
    result = await payment_gateway.verify_callback(channel, headers, body)
    if not result:
        logger.warning(f"[Payment] Callback verification failed for {channel}")
        return None

    order_no = result.get("order_no")
    if not order_no:
        logger.error(f"[Payment] Callback missing order_no")
        return None

    # Find order
    db_result = await db.execute(
        select(PaymentOrder).where(PaymentOrder.order_no == order_no)
    )
    order = db_result.scalar_one_or_none()
    if not order:
        logger.error(f"[Payment] Order not found: {order_no}")
        return None

    # ── Security: Verify channel matches ──
    if order.channel.value != channel:
        logger.critical(
            f"[SECURITY] Channel mismatch for order {order_no}: "
            f"expected={order.channel.value}, received={channel}"
        )
        return None

    # Already processed?
    if order.status in (OrderStatus.PAID, OrderStatus.REFUNDED):
        logger.info(f"[Payment] Order {order_no} already processed: {order.status.value}")
        return order

    # ── Security: Only PENDING orders can transition to PAID ──
    if order.status != OrderStatus.PENDING:
        logger.warning(
            f"[SECURITY] Callback for non-pending order {order_no}: "
            f"status={order.status.value}"
        )
        return order

    # ── Security: Verify callback amount matches order amount ──
    callback_amount_fen = result.get("amount_fen", 0)
    callback_status = result.get("status", "")

    if callback_status == "paid" and callback_amount_fen > 0:
        if callback_amount_fen != order.amount_fen:
            logger.critical(
                f"[SECURITY] Amount mismatch for order {order_no}: "
                f"expected={order.amount_fen}fen, callback={callback_amount_fen}fen. "
                f"Possible tampering — REJECTING."
            )
            order.status = OrderStatus.FAILED
            order.callback_raw = _sanitize_callback_raw(result.get("raw", {}))
            await db.flush()
            return None

    # Update order
    order.trade_no = result.get("trade_no") or order.trade_no
    order.callback_raw = _sanitize_callback_raw(result.get("raw", {}))

    if callback_status == "paid":
        order.status = OrderStatus.PAID
        order.paid_at = datetime.utcnow()
        await db.flush()

        # Fulfill the purchase
        await fulfill_order(db, order)
        logger.info(f"[Payment] Order {order_no} paid and fulfilled")
    elif callback_status in ("closed", "failed"):
        order.status = OrderStatus.CLOSED if callback_status == "closed" else OrderStatus.FAILED
        await db.flush()
        logger.info(f"[Payment] Order {order_no} status: {callback_status}")
    else:
        logger.info(f"[Payment] Order {order_no} callback status: {callback_status} (no action)")

    return order


def _sanitize_callback_raw(raw: dict) -> str:
    """
    Sanitize callback raw data before storing — remove sensitive fields
    that could leak payment credentials if the DB is compromised.
    """
    SENSITIVE_KEYS = {
        "sign", "signature", "sign_type", "msg_signature",
        "ciphertext", "nonce", "key", "secret", "token",
        "openid", "buyer_id", "buyer_logon_id",
    }
    sanitized = {}
    for k, v in raw.items():
        if k.lower() in SENSITIVE_KEYS:
            sanitized[k] = "***REDACTED***"
        elif isinstance(v, dict):
            sanitized[k] = {
                ik: "***REDACTED***" if ik.lower() in SENSITIVE_KEYS else iv
                for ik, iv in v.items()
            }
        else:
            sanitized[k] = v
    return json.dumps(sanitized, ensure_ascii=False)


# ═══════════════════════════════════════════════════════════════════
# Order polling (for frontend to check status)
# ═══════════════════════════════════════════════════════════════════

async def poll_order_status(
    db: AsyncSession,
    order_no: str,
    user_id: int,
) -> PaymentOrder | None:
    """
    Check order status. If still pending, query the provider.
    Returns updated order.
    """
    result = await db.execute(
        select(PaymentOrder).where(
            PaymentOrder.order_no == order_no,
            PaymentOrder.user_id == user_id,
        )
    )
    order = result.scalar_one_or_none()
    if not order:
        return None

    # Already terminal?
    if order.status in (OrderStatus.PAID, OrderStatus.CLOSED, OrderStatus.REFUNDED, OrderStatus.FAILED):
        return order

    # Check expiration
    if order.expired_at and order.expired_at < datetime.utcnow():
        order.status = OrderStatus.CLOSED
        await db.flush()
        return order

    # Query provider
    try:
        provider_result = await payment_gateway.query_order(
            order.channel.value, order.order_no
        )
        provider_status = provider_result.get("status", "pending")

        if provider_status == "paid":
            order.status = OrderStatus.PAID
            order.paid_at = datetime.utcnow()
            order.trade_no = provider_result.get("trade_no") or order.trade_no
            await db.flush()
            await fulfill_order(db, order)
        elif provider_status in ("closed", "failed"):
            order.status = OrderStatus.CLOSED
            await db.flush()

    except Exception as e:
        logger.error(f"[Payment] Error polling order {order_no}: {e}")

    return order


# ═══════════════════════════════════════════════════════════════════
# Order queries
# ═══════════════════════════════════════════════════════════════════

async def get_user_orders(
    db: AsyncSession,
    user_id: int,
    page: int = 1,
    page_size: int = 20,
) -> list[PaymentOrder]:
    """Get paginated order history for a user."""
    result = await db.execute(
        select(PaymentOrder)
        .where(PaymentOrder.user_id == user_id)
        .order_by(PaymentOrder.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return list(result.scalars().all())


async def get_order_by_no(
    db: AsyncSession,
    order_no: str,
    user_id: int | None = None,
) -> PaymentOrder | None:
    """Get an order by order number, optionally filtered by user."""
    stmt = select(PaymentOrder).where(PaymentOrder.order_no == order_no)
    if user_id is not None:
        stmt = stmt.where(PaymentOrder.user_id == user_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


# ═══════════════════════════════════════════════════════════════════
# Errors
# ═══════════════════════════════════════════════════════════════════

class AgreementNotAcceptedError(Exception):
    """Raised when user hasn't accepted the required agreement."""
    pass
