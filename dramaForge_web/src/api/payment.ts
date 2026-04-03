/**
 * DramaForge — Payment API
 * =========================
 * Payment orders, QR code generation, agreement management.
 */
import apiClient from './client'

// ═══════════════════════════════════════════════════════════════════
// Types
// ═══════════════════════════════════════════════════════════════════

export interface CreateOrderRequest {
  order_type: 'subscription' | 'credit_pack'
  product_code: string
  channel: 'wechat' | 'alipay' | 'douyin'
  agreement_accepted: boolean
}

export interface PaymentOrder {
  order_no: string
  order_type: string
  product_code: string
  product_name: string
  channel: string
  amount_cny: number
  status: string
  qr_url: string | null
  qr_image_base64: string | null
  agreement_accepted: boolean
  agreement_version: string | null
  created_at: string
  expired_at: string | null
  paid_at: string | null
}

export interface OrderStatus {
  order_no: string
  status: string
  paid_at: string | null
  message: string
}

export interface CreditPack {
  code: string
  name: string
  credits: number
  price_cny: number
}

export interface PaymentChannelInfo {
  code: string
  name: string
  icon: string
  configured: boolean
  available: boolean
}

export interface AgreementContent {
  version: string
  content: string
  content_type: string
}

export interface AgreementStatus {
  accepted: boolean
  version: string
}

// ═══════════════════════════════════════════════════════════════════
// Agreement API
// ═══════════════════════════════════════════════════════════════════

/** Get the service agreement content */
export async function getAgreement(): Promise<AgreementContent> {
  const resp = await apiClient.get<AgreementContent>('/payment/agreement')
  return resp.data
}

/** Check if user has accepted the agreement */
export async function getAgreementStatus(): Promise<AgreementStatus> {
  const resp = await apiClient.get<AgreementStatus>('/payment/agreement/status')
  return resp.data
}

/** Accept the service agreement */
export async function acceptAgreement(
  type: string = 'payment_tos'
): Promise<AgreementStatus> {
  const resp = await apiClient.post<AgreementStatus>('/payment/agreement/accept', {
    agreement_type: type,
  })
  return resp.data
}

// ═══════════════════════════════════════════════════════════════════
// Product Listing
// ═══════════════════════════════════════════════════════════════════

/** List available credit packs */
export async function getCreditPacks(): Promise<CreditPack[]> {
  const resp = await apiClient.get<CreditPack[]>('/payment/credit-packs')
  return resp.data
}

/** List available payment channels */
export async function getPaymentChannels(): Promise<PaymentChannelInfo[]> {
  const resp = await apiClient.get<PaymentChannelInfo[]>('/payment/channels')
  return resp.data
}

// ═══════════════════════════════════════════════════════════════════
// Order API
// ═══════════════════════════════════════════════════════════════════

/** Create a payment order (returns QR code) */
export async function createPaymentOrder(
  request: CreateOrderRequest
): Promise<PaymentOrder> {
  const resp = await apiClient.post<PaymentOrder>('/payment/create-order', request)
  return resp.data
}

/** Get a specific order */
export async function getOrder(orderNo: string): Promise<PaymentOrder> {
  const resp = await apiClient.get<PaymentOrder>(`/payment/orders/${orderNo}`)
  return resp.data
}

/** List user orders */
export async function getOrders(
  page = 1,
  pageSize = 20
): Promise<PaymentOrder[]> {
  const resp = await apiClient.get<PaymentOrder[]>('/payment/orders', {
    params: { page, page_size: pageSize },
  })
  return resp.data
}

/** Poll order status (call every 3s while showing QR) */
export async function pollOrderStatus(orderNo: string): Promise<OrderStatus> {
  const resp = await apiClient.get<OrderStatus>(
    `/payment/orders/${orderNo}/status`
  )
  return resp.data
}

/** Close/cancel a pending order */
export async function closeOrder(
  orderNo: string
): Promise<{ order_no: string; status: string; message: string }> {
  const resp = await apiClient.post(`/payment/orders/${orderNo}/close`)
  return resp.data
}

// ═══════════════════════════════════════════════════════════════════
// Channel labels
// ═══════════════════════════════════════════════════════════════════

export const CHANNEL_LABELS: Record<string, string> = {
  wechat: '微信支付',
  alipay: '支付宝',
  douyin: '抖音支付',
}

export const ORDER_STATUS_LABELS: Record<string, string> = {
  pending: '待支付',
  paid: '已支付',
  closed: '已关闭',
  refunded: '已退款',
  refund_partial: '部分退款',
  failed: '支付失败',
}
