/**
 * DramaForge — Billing Store (Pinia)
 * ====================================
 * Credits, subscription, and plan state management.
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  getBalance,
  getPlans,
  getSubscription,
  subscribeToPlan,
  getTransactions,
  getPricing,
  checkCredits,
} from '@/api/billing'
import type {
  BalanceInfo,
  PlanInfo,
  SubscriptionInfo,
  TransactionInfo,
  PricingTable,
} from '@/api/billing'

export const useBillingStore = defineStore('billing', () => {
  // ═══════ State ═══════
  const balance = ref<BalanceInfo | null>(null)
  const plans = ref<PlanInfo[]>([])
  const subscription = ref<SubscriptionInfo | null>(null)
  const transactions = ref<TransactionInfo[]>([])
  const pricing = ref<PricingTable | null>(null)
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  // ═══════ Getters ═══════
  const credits = computed(() => balance.value?.balance ?? 0)
  const planCode = computed(() => balance.value?.plan_code ?? 'free')
  const planName = computed(() => balance.value?.plan_name ?? '免费版')
  const isPaid = computed(() => planCode.value !== 'free')

  // ═══════ Actions ═══════

  /** Fetch balance and plan info */
  async function fetchBalance(): Promise<void> {
    try {
      balance.value = await getBalance()
    } catch (e: any) {
      console.error('[Billing] Failed to fetch balance:', e)
    }
  }

  /** Fetch all available plans */
  async function fetchPlans(): Promise<void> {
    try {
      plans.value = await getPlans()
    } catch (e: any) {
      console.error('[Billing] Failed to fetch plans:', e)
    }
  }

  /** Fetch current subscription */
  async function fetchSubscription(): Promise<void> {
    try {
      subscription.value = await getSubscription()
    } catch (e: any) {
      console.error('[Billing] Failed to fetch subscription:', e)
    }
  }

  /** Subscribe to a plan */
  async function doSubscribe(planCode: string): Promise<boolean> {
    isLoading.value = true
    error.value = null
    try {
      subscription.value = await subscribeToPlan(planCode)
      // Refresh balance after subscription
      await fetchBalance()
      return true
    } catch (e: any) {
      error.value = e.response?.data?.detail || e.message || '订阅失败'
      return false
    } finally {
      isLoading.value = false
    }
  }

  /** Fetch transaction history */
  async function fetchTransactions(page = 1, pageSize = 20): Promise<void> {
    try {
      transactions.value = await getTransactions(page, pageSize)
    } catch (e: any) {
      console.error('[Billing] Failed to fetch transactions:', e)
    }
  }

  /** Fetch pricing table */
  async function fetchPricing(): Promise<void> {
    try {
      pricing.value = await getPricing()
    } catch (e: any) {
      console.error('[Billing] Failed to fetch pricing:', e)
    }
  }

  /** Check credit sufficiency for a service */
  async function hasSufficientCredits(serviceType: string): Promise<boolean> {
    try {
      const result = await checkCredits(serviceType)
      return result.sufficient
    } catch {
      return false
    }
  }

  /** Initialize billing state */
  async function initialize(): Promise<void> {
    await Promise.all([
      fetchBalance(),
      fetchPlans(),
      fetchSubscription(),
    ])
  }

  /** Refresh balance after credit consumption */
  async function refreshAfterConsume(): Promise<void> {
    await fetchBalance()
  }

  function clearError(): void {
    error.value = null
  }

  return {
    // State
    balance,
    plans,
    subscription,
    transactions,
    pricing,
    isLoading,
    error,
    // Getters
    credits,
    planCode,
    planName,
    isPaid,
    // Actions
    fetchBalance,
    fetchPlans,
    fetchSubscription,
    doSubscribe,
    fetchTransactions,
    fetchPricing,
    hasSufficientCredits,
    initialize,
    refreshAfterConsume,
    clearError,
  }
})
