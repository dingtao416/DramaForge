"""
DramaForge v2.0 — Payment API
================================
Endpoints for creating payment orders, polling status,
receiving provider callbacks, and viewing order history.

Flow:
  1. User selects product + channel → POST /payment/create-order
  2. Frontend shows QR code → user scans and pays
  3. Frontend polls GET /payment/orders/{order_no}/status every 3s
  4. Provider sends callback POST /payment/callback/{channel}
  5. Order fulfilled → credits/subscription activated
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Request, Response, status
from pydantic import BaseModel, Field

from app.core.security import CurrentUser, DbSession
from app.models.payment import CREDIT_PACKS, OrderStatus, PaymentChannel
from app.services.payment_service import (
    AgreementNotAcceptedError,
    CURRENT_AGREEMENT_VERSION,
    check_agreement,
    accept_agreement,
    create_payment_order,
    get_order_by_no,
    get_user_orders,
    poll_order_status,
    process_callback,
)
from app.services.payment_gateway import PaymentProviderError

router = APIRouter(prefix="/payment", tags=["Payment"])


# ═══════════════════════════════════════════════════════════════════
# Schemas
# ═══════════════════════════════════════════════════════════════════

class CreateOrderRequest(BaseModel):
    """Request to create a payment order."""
    order_type: str = Field(
        ...,
        description="Type: 'subscription' or 'credit_pack'",
        pattern="^(subscription|credit_pack)$",
    )
    product_code: str = Field(
        ...,
        description="Plan code (basic_monthly/basic_yearly) or pack code (pack_50/pack_200/...)",
    )
    channel: str = Field(
        ...,
        description="Payment channel: wechat, alipay, or douyin",
        pattern="^(wechat|alipay|douyin)$",
    )
    agreement_accepted: bool = Field(
        False,
        description="User must accept the service agreement to proceed",
    )


class OrderResponse(BaseModel):
    """Payment order detail returned to frontend."""
    order_no: str
    order_type: str
    product_code: str
    product_name: str
    channel: str
    amount_cny: float
    status: str
    qr_url: Optional[str] = None
    qr_image_base64: Optional[str] = None
    agreement_accepted: bool
    agreement_version: Optional[str] = None
    created_at: datetime
    expired_at: Optional[datetime] = None
    paid_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class OrderStatusResponse(BaseModel):
    """Simplified status for polling."""
    order_no: str
    status: str
    paid_at: Optional[datetime] = None
    message: str = ""


class CreditPackInfo(BaseModel):
    """Credit pack product info."""
    code: str
    name: str
    credits: int
    price_cny: float


class AgreementStatusResponse(BaseModel):
    """Whether user has accepted current agreement."""
    accepted: bool
    version: str


class AcceptAgreementRequest(BaseModel):
    """Request to accept agreement."""
    agreement_type: str = Field(
        default="payment_tos",
        description="Agreement type: payment_tos, privacy_policy",
    )


# ═══════════════════════════════════════════════════════════════════
# Agreement Endpoints
# ═══════════════════════════════════════════════════════════════════

AGREEMENT_TEXT = """
# DramaForge 服务协议与支付条款

**版本：v1.0　生效日期：2024年1月1日**

## 一、服务说明

DramaForge 是一款 AI 驱动的短剧视频创作平台，提供以下付费服务：
- 订阅会员套餐（月付/年付）
- 积分包购买

## 二、积分说明

1. 积分为虚拟货币，用于平台内各项 AI 生成服务
2. 免费用户每日赠送 10 积分，当日清零
3. 付费用户每月到账对应额度积分
4. 已购买积分不可退换为现金
5. 账户注销后，未使用积分作废

## 三、支付条款

1. 支持微信支付、支付宝、抖音支付
2. 订单创建后 30 分钟内完成支付，超时自动关闭
3. 支付成功后，积分/会员即时到账
4. 首次订阅享受优惠价，续费恢复原价
5. 订阅周期内不支持退款，到期后可选择不再续费

## 四、自动续费说明

1. 开通自动续费后，系统将在到期前 1 天自动扣款
2. 您可随时在账户设置中取消自动续费
3. 取消后当前周期仍然有效

## 五、退款政策

1. 数字虚拟商品，支付完成后一般不予退款
2. 因系统原因导致重复扣款，可申请退款
3. 退款申请请联系客服：support@dramaforge.com

## 六、免责声明

1. AI 生成内容不代表平台立场
2. 用户对使用生成内容的行为负责
3. 平台保留在违反使用条款时终止服务的权利

---

勾选"我已阅读并同意"即表示您已完整阅读并同意以上全部条款。
"""


@router.get("/agreement")
async def get_agreement():
    """Get the current service agreement text."""
    return {
        "version": CURRENT_AGREEMENT_VERSION,
        "content": AGREEMENT_TEXT.strip(),
        "content_type": "markdown",
    }


@router.get("/agreement/status", response_model=AgreementStatusResponse)
async def get_agreement_status(user: CurrentUser, db: DbSession):
    """Check if current user has accepted the agreement."""
    accepted = await check_agreement(db, user.id)
    return AgreementStatusResponse(
        accepted=accepted,
        version=CURRENT_AGREEMENT_VERSION,
    )


@router.post("/agreement/accept", response_model=AgreementStatusResponse)
async def accept_agreement_endpoint(
    body: AcceptAgreementRequest,
    user: CurrentUser,
    db: DbSession,
    request: Request,
):
    """Accept the service agreement."""
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")

    await accept_agreement(db, user.id, body.agreement_type, ip, ua)
    await db.commit()

    return AgreementStatusResponse(
        accepted=True,
        version=CURRENT_AGREEMENT_VERSION,
    )


# ═══════════════════════════════════════════════════════════════════
# Product Listing
# ═══════════════════════════════════════════════════════════════════

@router.get("/credit-packs", response_model=list[CreditPackInfo])
async def list_credit_packs():
    """List available credit packs for purchase."""
    return [CreditPackInfo(**pack) for pack in CREDIT_PACKS]


@router.get("/channels")
async def list_channels():
    """List available payment channels and their status."""
    from app.services.payment_gateway import payment_gateway
    channels = []
    for name, adapter in payment_gateway._adapters.items():
        channels.append({
            "code": name,
            "name": {
                "wechat": "微信支付",
                "alipay": "支付宝",
                "douyin": "抖音支付",
            }.get(name, name),
            "icon": {
                "wechat": "wechat",
                "alipay": "alipay",
                "douyin": "douyin",
            }.get(name, ""),
            "configured": adapter._is_configured(),
            "available": True,  # Always available (mock mode if not configured)
        })
    return channels


# ═══════════════════════════════════════════════════════════════════
# Order CRUD
# ═══════════════════════════════════════════════════════════════════

@router.post("/create-order", response_model=OrderResponse)
async def create_order(
    body: CreateOrderRequest,
    user: CurrentUser,
    db: DbSession,
    request: Request,
):
    """
    Create a payment order.
    Returns QR code data for the user to scan.

    The user must have accepted the service agreement (agreement_accepted=true)
    or have previously accepted it.
    """
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")

    try:
        order = await create_payment_order(
            db=db,
            user_id=user.id,
            order_type=body.order_type,
            product_code=body.product_code,
            channel=body.channel,
            agreement_accepted=body.agreement_accepted,
            ip_address=ip,
            user_agent=ua,
        )
        await db.commit()
    except AgreementNotAcceptedError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "AGREEMENT_NOT_ACCEPTED",
                "message": str(e),
                "agreement_version": CURRENT_AGREEMENT_VERSION,
            },
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except PaymentProviderError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "code": "PAYMENT_PROVIDER_ERROR",
                "message": str(e),
            },
        )

    return _to_order_response(order)


@router.get("/orders", response_model=list[OrderResponse])
async def list_orders(
    user: CurrentUser,
    db: DbSession,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """List user's payment orders."""
    orders = await get_user_orders(db, user.id, page, page_size)
    return [_to_order_response(o) for o in orders]


@router.get("/orders/{order_no}", response_model=OrderResponse)
async def get_order(
    order_no: str,
    user: CurrentUser,
    db: DbSession,
):
    """Get a specific order by order number."""
    order = await get_order_by_no(db, order_no, user.id)
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    return _to_order_response(order)


@router.get("/orders/{order_no}/status", response_model=OrderStatusResponse)
async def poll_status(
    order_no: str,
    user: CurrentUser,
    db: DbSession,
):
    """
    Poll order payment status.
    Frontend should call this every 3 seconds while showing QR code.
    If status changes to 'paid', stop polling and show success.
    """
    order = await poll_order_status(db, order_no, user.id)
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    await db.commit()

    status_messages = {
        OrderStatus.PENDING.value: "等待支付，请扫描二维码完成付款",
        OrderStatus.PAID.value: "支付成功！积分/会员已到账",
        OrderStatus.CLOSED.value: "订单已关闭（超时或已取消）",
        OrderStatus.FAILED.value: "支付失败，请重试",
        OrderStatus.REFUNDED.value: "已退款",
    }

    return OrderStatusResponse(
        order_no=order.order_no,
        status=order.status.value,
        paid_at=order.paid_at,
        message=status_messages.get(order.status.value, ""),
    )


@router.post("/orders/{order_no}/close")
async def close_order(
    order_no: str,
    user: CurrentUser,
    db: DbSession,
):
    """Manually close/cancel a pending order."""
    order = await get_order_by_no(db, order_no, user.id)
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    if order.status != OrderStatus.PENDING:
        raise HTTPException(
            status_code=400,
            detail=f"只能关闭待支付订单，当前状态: {order.status.value}",
        )

    order.status = OrderStatus.CLOSED
    await db.commit()

    return {"order_no": order_no, "status": "closed", "message": "订单已关闭"}


# ═══════════════════════════════════════════════════════════════════
# Provider Callbacks (no auth — called by WeChat/Alipay/Douyin)
# ═══════════════════════════════════════════════════════════════════

@router.post("/callback/wechat")
async def wechat_callback(request: Request, db: DbSession):
    """WeChat Pay callback endpoint."""
    headers = dict(request.headers)
    body = await request.body()

    order = await process_callback(db, "wechat", headers, body)
    await db.commit()

    if order:
        # WeChat expects {"code": "SUCCESS", "message": "成功"}
        return {"code": "SUCCESS", "message": "成功"}
    return Response(status_code=500, content='{"code":"FAIL","message":"签名验证失败"}')


@router.post("/callback/alipay")
async def alipay_callback(request: Request, db: DbSession):
    """Alipay callback endpoint."""
    headers = dict(request.headers)
    body = await request.body()

    order = await process_callback(db, "alipay", headers, body)
    await db.commit()

    if order:
        return Response(content="success", media_type="text/plain")
    return Response(content="fail", media_type="text/plain")


@router.post("/callback/douyin")
async def douyin_callback(request: Request, db: DbSession):
    """Douyin Pay callback endpoint."""
    headers = dict(request.headers)
    body = await request.body()

    order = await process_callback(db, "douyin", headers, body)
    await db.commit()

    if order:
        return {"err_no": 0, "err_tips": "success"}
    return {"err_no": 1, "err_tips": "验证失败"}


# ═══════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════

def _to_order_response(order) -> OrderResponse:
    return OrderResponse(
        order_no=order.order_no,
        order_type=order.order_type.value,
        product_code=order.product_code,
        product_name=order.product_name,
        channel=order.channel.value,
        amount_cny=order.amount_cny,
        status=order.status.value,
        qr_url=order.qr_url,
        qr_image_base64=order.qr_image_base64,
        agreement_accepted=order.agreement_accepted,
        agreement_version=order.agreement_version,
        created_at=order.created_at,
        expired_at=order.expired_at,
        paid_at=order.paid_at,
    )
