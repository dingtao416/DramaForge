/**
 * DramaForge — Payment Store (Pinia)
 * =====================================
 * Manages payment flow: agreement → channel → QR → polling → success.
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  getAgreement,
  getAgreementStatus,
  acceptAgreement,
  getCreditPacks,
  getPaymentChannels,
  createPaymentOrder,
  pollOrderStatus,
  closeOrder,
  getOrders,
} from '@/api/payment'
import type {
  AgreementContent,
  CreditPack,
  PaymentChannelInfo,
  PaymentOrder,
  CreateOrderRequest,
} from '@/api/payment'

export const usePaymentStore = defineStore('payment', () => {
  // ═══════ State ═══════
  const agreement = ref<AgreementContent | null>(null)
  const agreementAccepted = ref(false)
  const creditPacks = ref<CreditPack[]>([])
  const channels = ref<PaymentChannelInfo[]>([])
  const currentOrder = ref<PaymentOrder | null>(null)
  const orderHistory = ref<PaymentOrder[]>([])
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  // Polling
  const pollTimer = ref<ReturnType<typeof setInterval> | null>(null)
  const pollStatus = ref<string>('')  // pending | paid | closed | failed

  // ═══════ Getters ═══════
  const isPending = computed(() => pollStatus.value === 'pending')
  const isPaid = computed(() => pollStatus.value === 'paid')
  const isClosed = computed(() => ['closed', 'failed'].includes(pollStatus.value))
  const qrBase64 = computed(() => currentOrder.value?.qr_image_base64 || null)
  const qrUrl = computed(() => currentOrder.value?.qr_url || null)

  // ═══════ Agreement ═══════

  async function fetchAgreement(): Promise<void> {
    try {
      agreement.value = await getAgreement()
    } catch (e: any) {
      console.error('[Payment] fetch agreement error:', e)
    }
  }

  async function checkAgreementStatus(): Promise<boolean> {
    try {
      const result = await getAgreementStatus()
      agreementAccepted.value = result.accepted
      return result.accepted
    } catch {
      return false
    }
  }

  async function doAcceptAgreement(): Promise<boolean> {
    try {
      const result = await acceptAgreement()
      agreementAccepted.value = result.accepted
      return result.accepted
    } catch (e: any) {
      error.value = e.response?.data?.detail || '协议确认失败'
      return false
    }
  }

  // ═══════ Products ═══════

  async function fetchCreditPacks(): Promise<void> {
    try {
      creditPacks.value = await getCreditPacks()
    } catch (e: any) {
      console.error('[Payment] fetch packs error:', e)
    }
  }

  async function fetchChannels(): Promise<void> {
    try {
      channels.value = await getPaymentChannels()
    } catch (e: any) {
      console.error('[Payment] fetch channels error:', e)
    }
  }

  // ═══════ Order ═══════

  async function createOrder(request: CreateOrderRequest): Promise<boolean> {
    isLoading.value = true
    error.value = null
    try {
      currentOrder.value = await createPaymentOrder(request)
      pollStatus.value = 'pending'
      // Start polling automatically
      startPolling()
      return true
    } catch (e: any) {
      const detail = e.response?.data?.detail
      if (typeof detail === 'object' && detail?.code === 'AGREEMENT_NOT_ACCEPTED') {
        error.value = detail.message || '请先同意服务协议'
      } else {
        error.value = typeof detail === 'string' ? detail : (detail?.message || '创建订单失败')
      }
      return false
    } finally {
      isLoading.value = false
    }
  }

  function startPolling(): void {
    stopPolling()  // Clear any existing timer

    if (!currentOrder.value) return

    pollTimer.value = setInterval(async () => {
      if (!currentOrder.value) {
        stopPolling()
        return
      }

      try {
        const result = await pollOrderStatus(currentOrder.value.order_no)
        pollStatus.value = result.status

        if (result.status === 'paid') {
          currentOrder.value!.status = 'paid'
          currentOrder.value!.paid_at = result.paid_at
          stopPolling()
        } else if (['closed', 'failed'].includes(result.status)) {
          currentOrder.value!.status = result.status
          stopPolling()
        }
      } catch (e: any) {
        console.error('[Payment] poll error:', e)
      }
    }, 3000)  // Poll every 3 seconds
  }

  function stopPolling(): void {
    if (pollTimer.value) {
      clearInterval(pollTimer.value)
      pollTimer.value = null
    }
  }

  async function cancelOrder(): Promise<void> {
    if (!currentOrder.value || currentOrder.value.status !== 'pending') return

    try {
      await closeOrder(currentOrder.value.order_no)
      currentOrder.value.status = 'closed'
      pollStatus.value = 'closed'
      stopPolling()
    } catch (e: any) {
      console.error('[Payment] cancel error:', e)
    }
  }

  // ═══════ History ═══════

  async function fetchOrders(page = 1): Promise<void> {
    try {
      orderHistory.value = await getOrders(page)
    } catch (e: any) {
      console.error('[Payment] fetch orders error:', e)
    }
  }

  // ═══════ Initialize ═══════

  async function initialize(): Promise<void> {
    await Promise.all([
      fetchCreditPacks(),
      fetchChannels(),
      checkAgreementStatus(),
    ])
  }

  // ═══════ Reset ═══════

  function reset(): void {
    stopPolling()
    currentOrder.value = null
    pollStatus.value = ''
    error.value = null
  }

  function clearError(): void {
    error.value = null
  }

  return {
    // State
    agreement,
    agreementAccepted,
    creditPacks,
    channels,
    currentOrder,
    orderHistory,
    isLoading,
    error,
    pollStatus,
    // Getters
    isPending,
    isPaid,
    isClosed,
    qrBase64,
    qrUrl,
    // Actions
    fetchAgreement,
    checkAgreementStatus,
    doAcceptAgreement,
    fetchCreditPacks,
    fetchChannels,
    createOrder,
    startPolling,
    stopPolling,
    cancelOrder,
    fetchOrders,
    initialize,
    reset,
    clearError,
  }
})
