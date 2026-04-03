/**
 * DramaForge — Billing API
 * ========================
 * Credits, subscriptions, plans, and transaction history.
 */
import apiClient from './client'

// ═══════════════════════════════════════════════════════════════════
// Types
// ═══════════════════════════════════════════════════════════════════

export interface BalanceInfo {
  balance: number
  total_earned: number
  total_spent: number
  plan_code: string  // "free" | "basic_monthly" | "basic_yearly"
  plan_name: string
}

export interface PlanInfo {
  id: number
  code: string
  name: string
  interval: string | null
  price_cny: number
  renewal_price_cny: number
  monthly_credits: number
  daily_credits: number
  description: string | null
  sort_order: number
}

export interface SubscriptionInfo {
  id: number
  plan_code: string
  plan_name: string
  status: string
  started_at: string
  expires_at: string | null
  is_renewal: boolean
  created_at: string
}

export interface TransactionInfo {
  id: number
  type: string
  amount: number
  balance_after: number
  description: string | null
  ref_id: string | null
  created_at: string
}

export interface CreditCheckResult {
  sufficient: boolean
  balance: number
  required: number
  service_type: string
}

export interface PricingTable {
  services: Record<string, number>
}

// ═══════════════════════════════════════════════════════════════════
// API Functions
// ═══════════════════════════════════════════════════════════════════

/** Get current user's balance and plan info */
export async function getBalance(): Promise<BalanceInfo> {
  const response = await apiClient.get<BalanceInfo>('/billing/balance')
  return response.data
}

/** List all available plans */
export async function getPlans(): Promise<PlanInfo[]> {
  const response = await apiClient.get<PlanInfo[]>('/billing/plans')
  return response.data
}

/** Get current user's active subscription */
export async function getSubscription(): Promise<SubscriptionInfo | null> {
  const response = await apiClient.get<SubscriptionInfo | null>('/billing/subscription')
  return response.data
}

/** Subscribe to a plan (simulated payment) */
export async function subscribeToPlan(planCode: string): Promise<SubscriptionInfo> {
  const response = await apiClient.post<SubscriptionInfo>('/billing/subscribe', {
    plan_code: planCode,
  })
  return response.data
}

/** Get transaction history */
export async function getTransactions(page = 1, pageSize = 20): Promise<TransactionInfo[]> {
  const response = await apiClient.get<TransactionInfo[]>('/billing/transactions', {
    params: { page, page_size: pageSize },
  })
  return response.data
}

/** Get service pricing table */
export async function getPricing(): Promise<PricingTable> {
  const response = await apiClient.get<PricingTable>('/billing/pricing')
  return response.data
}

/** Check if user has enough credits for a service */
export async function checkCredits(serviceType: string): Promise<CreditCheckResult> {
  const response = await apiClient.get<CreditCheckResult>('/billing/check-credits', {
    params: { service_type: serviceType },
  })
  return response.data
}

// ═══════════════════════════════════════════════════════════════════
// Service type labels (for display)
// ═══════════════════════════════════════════════════════════════════

export const SERVICE_LABELS: Record<string, string> = {
  chat_default: 'AI 对话',
  chat_premium: 'AI 对话 (高级)',
  image_default: '图片生成',
  image_premium: '图片生成 (高级)',
  video_default_5s: '视频生成 5s',
  video_premium_5s: '视频生成 5s (高质量)',
  video_default_10s: '视频生成 10s',
  video_premium_10s: '视频生成 10s (高质量)',
  tts: '语音合成',
  script_gen: '剧本生成',
  storyboard_gen: '分镜生成',
}

export const TX_TYPE_LABELS: Record<string, string> = {
  chat_default: 'AI 对话',
  chat_premium: 'AI 对话 (高级)',
  image_default: '图片生成',
  image_premium: '图片生成 (MJ)',
  video_default_5s: '视频 5s',
  video_premium_5s: '视频 5s (高质量)',
  video_default_10s: '视频 10s',
  video_premium_10s: '视频 10s (高质量)',
  tts: '语音合成',
  script_gen: '剧本生成',
  storyboard_gen: '分镜生成',
  daily_gift: '每日赠送',
  subscription_grant: '订阅到账',
  purchase: '积分购买',
  admin_adjust: '管理员调整',
  refund: '退款',
}
