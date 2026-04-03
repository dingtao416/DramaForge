"""
DramaForge v2.0 — Payment Channel Adapters
=============================================
Native API adapters for WeChat Pay, Alipay, and Douyin Pay.
Each adapter implements: create_native_order, verify_callback, query_order.

Architecture:
  ┌──────────────────────┐
  │  PaymentGateway      │  ← Unified interface
  ├──────────────────────┤
  │  WeChatPayAdapter    │  ← 微信支付 Native API v3
  │  AlipayAdapter       │  ← 支付宝当面付 (precreate)
  │  DouyinPayAdapter    │  ← 抖音支付担保交易
  └──────────────────────┘

Configuration required in .env:
  WECHAT_MCH_ID, WECHAT_API_KEY_V3, WECHAT_APP_ID, WECHAT_SERIAL_NO, WECHAT_CERT_PATH
  ALIPAY_APP_ID, ALIPAY_PRIVATE_KEY_PATH, ALIPAY_PUBLIC_KEY_PATH
  DOUYIN_APP_ID, DOUYIN_APP_SECRET, DOUYIN_MERCHANT_ID, DOUYIN_SALT
"""

from __future__ import annotations

import abc
import base64
import hashlib
import hmac
import io
import json
import secrets
import time
import uuid
from datetime import datetime, timedelta
from typing import Any, Optional

import httpx
from loguru import logger

try:
    import qrcode
    HAS_QRCODE = True
except ImportError:
    HAS_QRCODE = False

from app.core.config import settings


# ═══════════════════════════════════════════════════════════════════
# QR Code Generation Helper
# ═══════════════════════════════════════════════════════════════════

def generate_qr_base64(data: str, box_size: int = 8, border: int = 2) -> str:
    """
    Generate a QR code PNG image as a base64 data URI.
    Falls back to returning the raw URL if qrcode lib is missing.
    """
    if not HAS_QRCODE:
        logger.warning("qrcode library not installed; returning raw URL")
        return data

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=box_size,
        border=border,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{b64}"


def generate_order_no() -> str:
    """Generate a unique order number: DF + timestamp + 6-char random."""
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    rand = secrets.token_hex(3).upper()
    return f"DF{ts}{rand}"


# ═══════════════════════════════════════════════════════════════════
# Abstract Base
# ═══════════════════════════════════════════════════════════════════

class PaymentAdapter(abc.ABC):
    """Abstract payment channel adapter."""

    channel_name: str = ""

    @abc.abstractmethod
    async def create_native_order(
        self,
        order_no: str,
        amount_fen: int,
        description: str,
        notify_url: str,
        expire_minutes: int = 30,
    ) -> dict[str, Any]:
        """
        Create a native payment order and return QR data.
        Returns:
            {
                "code_url": str,          # Provider payment URL (for QR)
                "qr_base64": str,         # Base64 PNG of QR code
                "trade_no": str | None,   # Provider pre-assigned trade number
                "raw_response": dict,     # Full provider response
            }
        """
        ...

    @abc.abstractmethod
    async def verify_callback(
        self,
        headers: dict[str, str],
        body: bytes,
    ) -> dict[str, Any] | None:
        """
        Verify and parse a payment callback notification.
        Returns parsed data if valid, None if verification failed.
        Result keys: order_no, trade_no, amount_fen, status, raw
        """
        ...

    @abc.abstractmethod
    async def query_order(self, order_no: str) -> dict[str, Any]:
        """
        Actively query order status from the provider.
        Returns: { status, trade_no, amount_fen, raw }
        """
        ...


# ═══════════════════════════════════════════════════════════════════
# WeChat Pay Native v3
# ═══════════════════════════════════════════════════════════════════

class WeChatPayAdapter(PaymentAdapter):
    """
    微信支付 Native 扫码付 API v3
    Docs: https://pay.weixin.qq.com/docs/merchant/apis/native-payment/direct/native-prepay.html
    """

    channel_name = "wechat"

    BASE_URL = "https://api.mch.weixin.qq.com"

    def __init__(self):
        self.mch_id: str = getattr(settings, "wechat_mch_id", "")
        self.api_key_v3: str = getattr(settings, "wechat_api_key_v3", "")
        self.app_id: str = getattr(settings, "wechat_app_id", "")
        self.serial_no: str = getattr(settings, "wechat_serial_no", "")
        self.cert_path: str = getattr(settings, "wechat_cert_path", "")

    def _is_configured(self) -> bool:
        return bool(self.mch_id and self.api_key_v3 and self.app_id)

    def _build_auth_header(self, method: str, url_path: str, body: str) -> str:
        """Build WeChat Pay APIv3 Authorization header (WECHATPAY2-SHA256-RSA2048)."""
        timestamp = str(int(time.time()))
        nonce = uuid.uuid4().hex
        sign_str = f"{method}\n{url_path}\n{timestamp}\n{nonce}\n{body}\n"

        # In production, sign with merchant RSA private key
        # For now, use HMAC-SHA256 as placeholder
        signature = hmac.new(
            self.api_key_v3.encode(),
            sign_str.encode(),
            hashlib.sha256,
        ).hexdigest()

        return (
            f'WECHATPAY2-SHA256-RSA2048 '
            f'mchid="{self.mch_id}",'
            f'nonce_str="{nonce}",'
            f'timestamp="{timestamp}",'
            f'serial_no="{self.serial_no}",'
            f'signature="{signature}"'
        )

    async def create_native_order(
        self,
        order_no: str,
        amount_fen: int,
        description: str,
        notify_url: str,
        expire_minutes: int = 30,
    ) -> dict[str, Any]:
        if not self._is_configured():
            # ── Mock mode: return simulated QR for development ──
            logger.warning("[WeChatPay] Not configured, using MOCK mode")
            mock_url = f"weixin://wxpay/bizpayurl?pr={order_no}"
            return {
                "code_url": mock_url,
                "qr_base64": generate_qr_base64(mock_url),
                "trade_no": None,
                "raw_response": {"mock": True},
            }

        url_path = "/v3/pay/transactions/native"
        expire_time = (datetime.utcnow() + timedelta(minutes=expire_minutes)).strftime(
            "%Y-%m-%dT%H:%M:%S+08:00"
        )

        payload = {
            "appid": self.app_id,
            "mchid": self.mch_id,
            "description": description[:127],
            "out_trade_no": order_no,
            "time_expire": expire_time,
            "notify_url": notify_url,
            "amount": {
                "total": amount_fen,
                "currency": "CNY",
            },
        }

        body_str = json.dumps(payload, ensure_ascii=False)
        auth = self._build_auth_header("POST", url_path, body_str)

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.BASE_URL}{url_path}",
                content=body_str,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": auth,
                    "Accept": "application/json",
                },
                timeout=15,
            )

        data = resp.json()
        if resp.status_code != 200:
            logger.error(f"[WeChatPay] create_native_order failed: {data}")
            raise PaymentProviderError(f"微信支付下单失败: {data.get('message', resp.status_code)}")

        code_url = data.get("code_url", "")
        return {
            "code_url": code_url,
            "qr_base64": generate_qr_base64(code_url),
            "trade_no": None,
            "raw_response": data,
        }

    async def verify_callback(self, headers: dict[str, str], body: bytes) -> dict[str, Any] | None:
        """
        Verify WeChat Pay v3 callback.
        In production: verify signature with platform certificate, then AES-256-GCM decrypt.
        """
        try:
            data = json.loads(body)
            resource = data.get("resource", {})

            # In production, decrypt resource.ciphertext with api_key_v3
            # For mock/dev, assume plaintext or skip verification
            if not self._is_configured():
                # Mock: treat body as-is
                inner = resource if "out_trade_no" in resource else data
                return {
                    "order_no": inner.get("out_trade_no"),
                    "trade_no": inner.get("transaction_id"),
                    "amount_fen": inner.get("amount", {}).get("total", 0),
                    "status": "paid" if inner.get("trade_state") == "SUCCESS" else "failed",
                    "raw": data,
                }

            # TODO: Real signature verification + AES-GCM decryption
            # nonce = resource.get("nonce")
            # ciphertext = resource.get("ciphertext")
            # associated_data = resource.get("associated_data")
            # plaintext = aes_gcm_decrypt(nonce, ciphertext, associated_data, self.api_key_v3)
            # inner = json.loads(plaintext)

            logger.info(f"[WeChatPay] callback received (needs real verification)")
            return None

        except Exception as e:
            logger.error(f"[WeChatPay] callback parse error: {e}")
            return None

    async def query_order(self, order_no: str) -> dict[str, Any]:
        if not self._is_configured():
            return {"status": "pending", "trade_no": None, "amount_fen": 0, "raw": {"mock": True}}

        url_path = f"/v3/pay/transactions/out-trade-no/{order_no}?mchid={self.mch_id}"
        auth = self._build_auth_header("GET", url_path, "")

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.BASE_URL}{url_path}",
                headers={"Authorization": auth, "Accept": "application/json"},
                timeout=10,
            )

        data = resp.json()
        state = data.get("trade_state", "").upper()
        status_map = {"SUCCESS": "paid", "CLOSED": "closed", "REFUND": "refunded"}
        return {
            "status": status_map.get(state, "pending"),
            "trade_no": data.get("transaction_id"),
            "amount_fen": data.get("amount", {}).get("total", 0),
            "raw": data,
        }


# ═══════════════════════════════════════════════════════════════════
# Alipay Precreate (当面付)
# ═══════════════════════════════════════════════════════════════════

class AlipayAdapter(PaymentAdapter):
    """
    支付宝当面付 (precreate) — 生成二维码让用户扫码支付
    Docs: https://opendocs.alipay.com/open/02ekfg
    """

    channel_name = "alipay"

    GATEWAY = "https://openapi.alipay.com/gateway.do"

    def __init__(self):
        self.app_id: str = getattr(settings, "alipay_app_id", "")
        self.private_key_path: str = getattr(settings, "alipay_private_key_path", "")
        self.public_key_path: str = getattr(settings, "alipay_public_key_path", "")

    def _is_configured(self) -> bool:
        return bool(self.app_id and self.private_key_path)

    def _sign(self, params: dict[str, str]) -> str:
        """
        RSA2 (SHA256WithRSA) signature for Alipay.
        In production, load PEM private key and sign.
        """
        # Sort params and build sign string
        sign_str = "&".join(f"{k}={params[k]}" for k in sorted(params) if params[k])

        # TODO: Real RSA2 signature with private key
        # from cryptography.hazmat.primitives import hashes, serialization
        # from cryptography.hazmat.primitives.asymmetric import padding
        # with open(self.private_key_path, "rb") as f:
        #     private_key = serialization.load_pem_private_key(f.read(), password=None)
        # signature = private_key.sign(sign_str.encode(), padding.PKCS1v15(), hashes.SHA256())
        # return base64.b64encode(signature).decode()

        return hashlib.sha256(sign_str.encode()).hexdigest()

    async def create_native_order(
        self,
        order_no: str,
        amount_fen: int,
        description: str,
        notify_url: str,
        expire_minutes: int = 30,
    ) -> dict[str, Any]:
        if not self._is_configured():
            logger.warning("[Alipay] Not configured, using MOCK mode")
            mock_url = f"https://qr.alipay.com/mock_{order_no}"
            return {
                "code_url": mock_url,
                "qr_base64": generate_qr_base64(mock_url),
                "trade_no": None,
                "raw_response": {"mock": True},
            }

        amount_yuan = f"{amount_fen / 100:.2f}"
        timeout = f"{expire_minutes}m"

        biz_content = json.dumps({
            "out_trade_no": order_no,
            "total_amount": amount_yuan,
            "subject": description[:256],
            "timeout_express": timeout,
        }, ensure_ascii=False)

        params = {
            "app_id": self.app_id,
            "method": "alipay.trade.precreate",
            "format": "JSON",
            "charset": "utf-8",
            "sign_type": "RSA2",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "version": "1.0",
            "notify_url": notify_url,
            "biz_content": biz_content,
        }

        params["sign"] = self._sign(params)

        async with httpx.AsyncClient() as client:
            resp = await client.post(self.GATEWAY, data=params, timeout=15)

        data = resp.json()
        result = data.get("alipay_trade_precreate_response", {})

        if result.get("code") != "10000":
            msg = result.get("sub_msg", result.get("msg", "未知错误"))
            logger.error(f"[Alipay] precreate failed: {msg}")
            raise PaymentProviderError(f"支付宝下单失败: {msg}")

        qr_code = result.get("qr_code", "")
        return {
            "code_url": qr_code,
            "qr_base64": generate_qr_base64(qr_code),
            "trade_no": None,
            "raw_response": data,
        }

    async def verify_callback(self, headers: dict[str, str], body: bytes) -> dict[str, Any] | None:
        """Verify Alipay async notification (RSA2 signature verification)."""
        try:
            from urllib.parse import parse_qs
            params = {k: v[0] for k, v in parse_qs(body.decode("utf-8")).items()}

            # TODO: Real RSA2 signature verification with Alipay public key
            # sign = params.pop("sign", "")
            # sign_type = params.pop("sign_type", "")
            # verify_str = "&".join(f"{k}={params[k]}" for k in sorted(params) if params[k])
            # ... verify with public key ...

            if not self._is_configured():
                # Mock mode
                trade_status = params.get("trade_status", "")
                return {
                    "order_no": params.get("out_trade_no"),
                    "trade_no": params.get("trade_no"),
                    "amount_fen": int(float(params.get("total_amount", "0")) * 100),
                    "status": "paid" if trade_status == "TRADE_SUCCESS" else "failed",
                    "raw": params,
                }

            logger.info(f"[Alipay] callback received (needs real verification)")
            return None

        except Exception as e:
            logger.error(f"[Alipay] callback parse error: {e}")
            return None

    async def query_order(self, order_no: str) -> dict[str, Any]:
        if not self._is_configured():
            return {"status": "pending", "trade_no": None, "amount_fen": 0, "raw": {"mock": True}}

        biz_content = json.dumps({"out_trade_no": order_no}, ensure_ascii=False)
        params = {
            "app_id": self.app_id,
            "method": "alipay.trade.query",
            "format": "JSON",
            "charset": "utf-8",
            "sign_type": "RSA2",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "version": "1.0",
            "biz_content": biz_content,
        }
        params["sign"] = self._sign(params)

        async with httpx.AsyncClient() as client:
            resp = await client.post(self.GATEWAY, data=params, timeout=10)

        data = resp.json()
        result = data.get("alipay_trade_query_response", {})
        status_map = {
            "TRADE_SUCCESS": "paid",
            "TRADE_CLOSED": "closed",
            "TRADE_FINISHED": "paid",
        }
        return {
            "status": status_map.get(result.get("trade_status", ""), "pending"),
            "trade_no": result.get("trade_no"),
            "amount_fen": int(float(result.get("total_amount", "0")) * 100),
            "raw": data,
        }


# ═══════════════════════════════════════════════════════════════════
# Douyin Pay (抖音支付)
# ═══════════════════════════════════════════════════════════════════

class DouyinPayAdapter(PaymentAdapter):
    """
    抖音支付担保交易 — H5/扫码下单
    Docs: https://developer.open-douyin.com/docs/resource/zh-CN/mini-app/develop/server/ecpay/
    """

    channel_name = "douyin"

    BASE_URL = "https://developer.toutiao.com/api/apps/ecpay/v1"

    def __init__(self):
        self.app_id: str = getattr(settings, "douyin_app_id", "")
        self.app_secret: str = getattr(settings, "douyin_app_secret", "")
        self.merchant_id: str = getattr(settings, "douyin_merchant_id", "")
        self.salt: str = getattr(settings, "douyin_salt", "")

    def _is_configured(self) -> bool:
        return bool(self.app_id and self.app_secret and self.salt)

    def _sign(self, params: list[str]) -> str:
        """
        Douyin pay signature: MD5 of sorted non-empty values joined.
        """
        sorted_vals = sorted(params)
        sign_str = "&".join(sorted_vals)
        return hashlib.md5(sign_str.encode()).hexdigest()

    async def create_native_order(
        self,
        order_no: str,
        amount_fen: int,
        description: str,
        notify_url: str,
        expire_minutes: int = 30,
    ) -> dict[str, Any]:
        if not self._is_configured():
            logger.warning("[DouyinPay] Not configured, using MOCK mode")
            mock_url = f"snssdk1128://ecpay?order={order_no}"
            return {
                "code_url": mock_url,
                "qr_base64": generate_qr_base64(mock_url),
                "trade_no": None,
                "raw_response": {"mock": True},
            }

        payload = {
            "app_id": self.app_id,
            "out_order_no": order_no,
            "total_amount": amount_fen,
            "subject": description[:128],
            "body": description[:256],
            "valid_time": expire_minutes * 60,
            "notify_url": notify_url,
            "thirdparty_id": self.merchant_id,
        }

        # Build sign
        sign_values = [str(v) for v in payload.values() if v] + [self.salt]
        payload["sign"] = self._sign(sign_values)

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.BASE_URL}/create_order",
                json=payload,
                timeout=15,
            )

        data = resp.json()
        if data.get("err_no") != 0:
            msg = data.get("err_tips", "未知错误")
            logger.error(f"[DouyinPay] create_order failed: {msg}")
            raise PaymentProviderError(f"抖音支付下单失败: {msg}")

        # Douyin returns order_id, and the payment page URL
        result_data = data.get("data", {})
        pay_url = result_data.get("sdk_params", result_data.get("desk_url", ""))
        return {
            "code_url": pay_url,
            "qr_base64": generate_qr_base64(pay_url) if pay_url else "",
            "trade_no": result_data.get("order_id"),
            "raw_response": data,
        }

    async def verify_callback(self, headers: dict[str, str], body: bytes) -> dict[str, Any] | None:
        try:
            data = json.loads(body)
            msg = json.loads(data.get("msg", "{}"))

            # Verify signature
            # sign_values = [sorted non-empty field values] + [salt]
            # expected_sign = md5(joined)
            # if data.get("msg_signature") != expected_sign: return None

            if not self._is_configured():
                return {
                    "order_no": msg.get("cp_orderno"),
                    "trade_no": msg.get("channel_no"),
                    "amount_fen": msg.get("total_amount", 0),
                    "status": "paid" if data.get("type") == "payment" else "refunded",
                    "raw": data,
                }

            logger.info(f"[DouyinPay] callback received (needs real verification)")
            return None

        except Exception as e:
            logger.error(f"[DouyinPay] callback parse error: {e}")
            return None

    async def query_order(self, order_no: str) -> dict[str, Any]:
        if not self._is_configured():
            return {"status": "pending", "trade_no": None, "amount_fen": 0, "raw": {"mock": True}}

        payload = {
            "app_id": self.app_id,
            "out_order_no": order_no,
            "thirdparty_id": self.merchant_id,
        }
        sign_values = [str(v) for v in payload.values() if v] + [self.salt]
        payload["sign"] = self._sign(sign_values)

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.BASE_URL}/query_order",
                json=payload,
                timeout=10,
            )

        data = resp.json()
        result = data.get("data", {}).get("payment_info", {})
        status_map = {"SUCCESS": "paid", "TIMEOUT": "closed"}
        return {
            "status": status_map.get(result.get("order_status", ""), "pending"),
            "trade_no": result.get("channel_no"),
            "amount_fen": result.get("total_amount", 0),
            "raw": data,
        }


# ═══════════════════════════════════════════════════════════════════
# Unified Gateway
# ═══════════════════════════════════════════════════════════════════

class PaymentProviderError(Exception):
    """Error from a payment provider API."""
    pass


class PaymentGateway:
    """
    Unified payment gateway that dispatches to the correct adapter.
    Usage:
        result = await payment_gateway.create_order("wechat", order_no, amount_fen, ...)
    """

    def __init__(self):
        self._adapters: dict[str, PaymentAdapter] = {
            "wechat": WeChatPayAdapter(),
            "alipay": AlipayAdapter(),
            "douyin": DouyinPayAdapter(),
        }

    def get_adapter(self, channel: str) -> PaymentAdapter:
        adapter = self._adapters.get(channel)
        if not adapter:
            raise ValueError(f"Unsupported payment channel: {channel}")
        return adapter

    async def create_order(
        self,
        channel: str,
        order_no: str,
        amount_fen: int,
        description: str,
        notify_url: str,
        expire_minutes: int = 30,
    ) -> dict[str, Any]:
        adapter = self.get_adapter(channel)
        return await adapter.create_native_order(
            order_no, amount_fen, description, notify_url, expire_minutes,
        )

    async def verify_callback(
        self,
        channel: str,
        headers: dict[str, str],
        body: bytes,
    ) -> dict[str, Any] | None:
        adapter = self.get_adapter(channel)
        return await adapter.verify_callback(headers, body)

    async def query_order(self, channel: str, order_no: str) -> dict[str, Any]:
        adapter = self.get_adapter(channel)
        return await adapter.query_order(order_no)


# Singleton
payment_gateway = PaymentGateway()
