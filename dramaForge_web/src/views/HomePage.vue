<script setup lang="ts">
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Icon } from '@iconify/vue'
import { projectsApi } from '@/api/projects'
import { scriptsApi } from '@/api/scripts'
import { VideoStyle } from '@/types/enums'
import type { Conversation } from '@/api/chat'
import type { ProjectList } from '@/types/project'
import { useAuthStore } from '@/stores/auth'
import { useChatStore } from '@/stores/chat'
import { useBillingStore } from '@/stores/billing'
import { useUserAIConfigStore } from '@/stores/user-ai-config'
import BottomSheet from '@/components/common/BottomSheet.vue'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'
import ModalOverlay from '@/components/common/ModalOverlay.vue'
import TopbarActions from '@/components/common/TopbarActions.vue'
import ImageGenerationCard from '@/components/chat/ImageGenerationCard.vue'
import ImageTaskCenter from '@/components/chat/ImageTaskCenter.vue'
import type { MediaJobPayload } from '@/api/chat'
import type { MediaJob, MediaJobStatus } from '@/types/user-ai-config'

const router = useRouter()
const authStore = useAuthStore()
const chatStore = useChatStore()
const billingStore = useBillingStore()
const aiStore = useUserAIConfigStore()
const userInput = ref('')
const loading = ref(false)
const recentProjects = ref<ProjectList[]>([])
const sidebarCollapsed = ref(false)
const messagesEndRef = ref<HTMLElement | null>(null)

// ── Sheet / Panel states ──
const showSubscribeSheet = ref(false)
const showFeedbackSheet = ref(false)
const showNotificationSheet = ref(false)
const showMessageSheet = ref(false)
const showImageTaskSheet = ref(false)
const imageTaskFilter = ref<'all' | MediaJobStatus>('all')
const feedbackText = ref('')
const feedbackType = ref('bug')
const showDeleteConversationConfirm = ref(false)
const deleteTargetConversation = ref<Conversation | null>(null)
const deletingConversation = ref(false)

/* ─── Mode definitions ─── */
type Mode = 'agent' | 'drama'

interface ModeOption {
  key: Mode
  label: string
  tag?: string
  desc: string
  placeholder: string
}

const modes: ModeOption[] = [
  { key: 'agent', label: '创作 Agent', desc: '全能创作助手，对话探索创意、管理项目、解答问题', placeholder: '想做视频？做图片？还是来点灵感探索？' },
  { key: 'drama', label: '短剧 Agent', tag: 'New', desc: '一键进入短剧创作工作台，快速开始分镜与剧情生成', placeholder: '' },
]

const currentMode = ref<Mode>('agent')
const showModeMenu = ref(false)

const currentModeOption = computed(() => modes.find(m => m.key === currentMode.value)!)

/** Map frontend mode to backend agent mode for chat */
const modeAgentMap: Record<Mode, string> = {
  agent: 'general',
  drama: 'scriptwriter',
}

function selectMode(mode: Mode) {
  // 短剧 Agent 模式：跳转到独立创作工作台
  if (mode === 'drama') {
    router.push('/drama-workbench')
    return
  }
  currentMode.value = mode
  closeAllMenus()
}

// ── 优化提示词 ──
const optimizing = ref(false)
let optimizeAbortController: AbortController | null = null

async function optimizePrompt() {
  const raw = userInput.value.trim()
  if (!raw || optimizing.value) return

  optimizing.value = true
  userInput.value = ''

  const modeLabel = currentModeOption.value?.label || '通用'
  const fullMessage = `你是一位专业的 AI 提示词优化专家。用户正在使用「${modeLabel}」模式。
请将用户输入的原始提示词优化为更详细、更专业、更能产出高质量结果的提示词。
要求：
1. 保留用户的核心意图
2. 补充细节（风格、场景、情绪、镜头语言等）
3. 使措辞更精准
4. 直接输出优化后的提示词，不要解释
5. 使用中文回复

原始提示词：
${raw}`

  optimizeAbortController = new AbortController()

  try {
    const { sendMessageStream } = await import('@/api/chat')
    let accumulated = ''

    await sendMessageStream(
      {
        content: fullMessage,
        mode: 'general',
        model: selectedModel.value || undefined,
      },
      {
        onContent: (chunk: string) => {
          accumulated += chunk
          userInput.value = accumulated
        },
        onDone: () => {
          userInput.value = accumulated.trim()
        },
        onError: (errMsg: string) => {
          userInput.value = raw
        },
      },
      optimizeAbortController.signal,
    )
  } catch (e: any) {
    if (e.name !== 'AbortError') {
      userInput.value = raw
    }
  } finally {
    optimizing.value = false
    optimizeAbortController = null
  }
}

/* ─── Dropdown states ─── */
const showUploadMenu = ref(false)
const showModelMenu = ref(false)
const showRatioMenu = ref(false)
const showPresetMenu = ref(false)

const modelAuto = ref(true)
type ModelCapability = 'chat' | 'image' | 'video'

const modelTab = ref<ModelCapability>('chat')
const selectedRatio = ref('auto')
const presetSearch = ref('')
const selectedModel = ref('')  // '' means auto
const selectedModelCapability = ref<ModelCapability | ''>('')

interface ModelOption {
  id: string
  name: string
  desc: string
  tag?: string                                       // '推荐' / '高质量' / '极速' 等
  modes: Mode[]                                      // 哪些前端模式下显示
  premium?: boolean                                  // 是否需要付费会员
}

// ── 用户已配置的模型（从 AI 配置 Store 读取）──
const userChatModels = computed<ModelOption[]>(() =>
  aiStore.modelsByType.chat.map(m => ({
    id: m.model_id,
    name: m.display_name,
    desc: `来自 ${m.provider_name}`,
    tag: m.is_default ? '默认' : undefined,
    modes: ['agent', 'drama', 'clip', 'longvideo2', 'image', 'longvideo'] as Mode[],
  }))
)

const userVideoModels = computed<ModelOption[]>(() =>
  aiStore.modelsByType.video.map(m => ({
    id: m.model_id,
    name: m.display_name,
    desc: `来自 ${m.provider_name}`,
    tag: m.is_default ? '默认' : undefined,
    modes: ['agent', 'clip', 'longvideo2', 'drama', 'longvideo'] as Mode[],
  }))
)

const userImageModels = computed<ModelOption[]>(() =>
  aiStore.modelsByType.image.map(m => ({
    id: m.model_id,
    name: m.display_name,
    desc: `来自 ${m.provider_name}`,
    tag: m.is_default ? '默认' : undefined,
    modes: ['agent', 'image', 'drama'] as Mode[],
  }))
)

/** Get user-configured models (no mode filtering — user models available for all modes) */
const filteredChatModels = computed(() => userChatModels.value)
const filteredVideoModels = computed(() => userVideoModels.value)
const filteredImageModels = computed(() => userImageModels.value)

/** Whether user has any models configured at all */
const hasAnyUserModels = computed(() =>
  filteredChatModels.value.length > 0 ||
  filteredVideoModels.value.length > 0 ||
  filteredImageModels.value.length > 0
)

/** Current model display name */
const selectedModelName = computed(() => {
  if (!selectedModel.value) return '自动'
  const modelGroups: Record<ModelCapability, ModelOption[]> = {
    chat: userChatModels.value,
    image: userImageModels.value,
    video: userVideoModels.value,
  }
  const models = selectedModelCapability.value
    ? modelGroups[selectedModelCapability.value]
    : [...userChatModels.value, ...userVideoModels.value, ...userImageModels.value]
  return models.find(m => m.id === selectedModel.value)?.name || selectedModel.value
})

function selectModel(id: string, capability: ModelCapability) {
  selectedModel.value = id
  selectedModelCapability.value = capability
  modelAuto.value = false
  closeAllMenus()
}

function toggleModelAuto() {
  modelAuto.value = !modelAuto.value
  if (modelAuto.value) {
    selectedModel.value = ''
    selectedModelCapability.value = ''
  }
}

/** Auto-select appropriate default model tab based on mode */
watch(currentMode, () => {
  // Only agent mode uses chat models; drama mode routes to workbench
  modelTab.value = 'chat'
  selectedModel.value = ''
  selectedModelCapability.value = ''
  modelAuto.value = true
})
const ratioOptions = [
  { value: 'auto', label: '自动', icon: '⊞' },
  { value: '16:9', label: '16:9 (横屏)', icon: '▭' },
  { value: '9:16', label: '9:16 (竖屏)', icon: '▯' },
  { value: '4:3', label: '4:3', icon: '▭' },
  { value: '3:4', label: '3:4', icon: '▯' },
]

function closeAllMenus() {
  showUploadMenu.value = false
  showModelMenu.value = false
  showRatioMenu.value = false
  showPresetMenu.value = false
  showModeMenu.value = false
}

function toggleMenu(menu: 'upload' | 'model' | 'ratio' | 'preset' | 'mode') {
  const wasOpen = {
    upload: showUploadMenu.value,
    model: showModelMenu.value,
    ratio: showRatioMenu.value,
    preset: showPresetMenu.value,
    mode: showModeMenu.value,
  }[menu]
  closeAllMenus()
  if (!wasOpen) {
    if (menu === 'upload') showUploadMenu.value = true
    else if (menu === 'model') showModelMenu.value = true
    else if (menu === 'ratio') showRatioMenu.value = true
    else if (menu === 'preset') showPresetMenu.value = true
    else if (menu === 'mode') showModeMenu.value = true
  }
}

const quickTags = ['香港电影 · 996', '漫剧：超绝人物特写', '潮汕功夫茶宣传片', '爆款手办生成']

const featureCards = [
  { title: '短剧 Agent', desc: 'AI 驱动三步流水线：剧本→资产→成片', isNew: true, bg: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', route: '/drama-workbench' },
  { title: '资产库', desc: '角色与场景资产统一管理复用', isNew: false, bg: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)', route: '/assets' },
  { title: '项目管理', desc: '多项目并行，分步审核推进', isNew: false, bg: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)', route: '/projects' },
  { title: '模型配置', desc: '多模型接入，灵活切换与成本控制', isNew: false, bg: 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)', route: '/settings' },
]

// Load chat conversations, billing, recent projects, and AI config on mount
onMounted(async () => {
  if (authStore.isLoggedIn) {
    // Fetch recent projects (was previously an IIFE running before auth)
    try {
      const { data } = await projectsApi.list({ limit: 10 })
      recentProjects.value = data
    } catch {}
    await Promise.all([
      chatStore.fetchConversations(),
      billingStore.initialize(),
      aiStore.fetchKeys(),
      aiStore.fetchDefaults(),
    ])
  }
})

// Auto-scroll when new messages arrive
watch(() => chatStore.messages.length, () => {
  nextTick(() => {
    messagesEndRef.value?.scrollIntoView({ behavior: 'smooth' })
  })
})

// Also scroll during streaming content updates (typewriter-paced)
watch(() => chatStore.displayContent, () => {
  nextTick(() => {
    messagesEndRef.value?.scrollIntoView({ behavior: 'smooth' })
  })
})

const showInsufficientCredits = ref(false)

async function startCreation() {
  if (!userInput.value.trim() || chatStore.isStreaming) return

  const input = userInput.value
  const agentMode = modeAgentMap[currentMode.value] || 'general'
  const model = modelAuto.value ? undefined : (selectedModel.value || undefined)
  const modelCapability = modelAuto.value ? undefined : (selectedModelCapability.value || undefined)
  userInput.value = ''
  await chatStore.sendMessage(input, { mode: agentMode, model, model_capability: modelCapability })

  // Check if the error was insufficient credits
  if (chatStore.error === 'INSUFFICIENT_CREDITS') {
    userInput.value = input // Restore user input
    showInsufficientCredits.value = true
    chatStore.error = null
  } else {
    // Refresh balance after successful sending (credits consumed)
    billingStore.fetchBalance()
  }
}

function fillTag(tag: string) {
  userInput.value = tag
}

function handleNewChat() {
  chatStore.newConversation()
  userInput.value = ''
}

function handleCreateAgentEntry() {
  currentMode.value = 'agent'
  closeAllMenus()
  handleNewChat()
}

function handleDramaAgentEntry() {
  closeAllMenus()
  router.push('/drama-workbench')
}

async function handleLoadConversation(convId: number) {
  await chatStore.loadConversation(convId)
}

function confirmDeleteConversation(conv: Conversation) {
  deleteTargetConversation.value = conv
  showDeleteConversationConfirm.value = true
}

function cancelDeleteConversation() {
  if (deletingConversation.value) return
  showDeleteConversationConfirm.value = false
  deleteTargetConversation.value = null
}

async function handleDeleteConversation() {
  if (!deleteTargetConversation.value) return
  deletingConversation.value = true
  try {
    await chatStore.deleteConversation(deleteTargetConversation.value.id)
    showDeleteConversationConfirm.value = false
    deleteTargetConversation.value = null
  } finally {
    deletingConversation.value = false
  }
}

function handleLogout() {
  authStore.doLogout()
  router.push('/login')
}

/**
 * Handle subscription — now opens the payment QR flow
 * instead of bypassing payment directly.
 */
async function handleSubscribe(planCode: string) {
  // Store selected plan for the payment flow
  pendingPaymentPlan.value = planCode
  showSubscribeSheet.value = false
  showPaymentModal.value = true
}

// ── Payment flow state ──
const showPaymentModal = ref(false)
const pendingPaymentPlan = ref('')
const selectedChannel = ref<'wechat' | 'alipay' | 'douyin'>('wechat')
const agreementChecked = ref(false)
const paymentStep = ref<'select' | 'qr' | 'success' | 'error'>('select')
const paymentError = ref('')
const selectedCreditPack = ref('')

import { usePaymentStore } from '@/stores/payment'
const paymentStore = usePaymentStore()

async function startPayment() {
  if (!agreementChecked.value) {
    paymentError.value = '请先阅读并同意服务协议'
    return
  }
  paymentError.value = ''
  const ok = await paymentStore.createOrder({
    order_type: 'subscription',
    product_code: pendingPaymentPlan.value,
    channel: selectedChannel.value,
    agreement_accepted: true,
  })
  if (ok) {
    paymentStep.value = 'qr'
    // Watch for payment completion
    const unwatch = watch(() => paymentStore.pollStatus, (status) => {
      if (status === 'paid') {
        paymentStep.value = 'success'
        billingStore.fetchBalance()
        billingStore.fetchSubscription()
        unwatch()
      } else if (['closed', 'failed'].includes(status)) {
        paymentStep.value = 'error'
        paymentError.value = '支付未完成'
        unwatch()
      }
    })
  } else {
    paymentError.value = paymentStore.error || '创建订单失败'
  }
}

function closePaymentModal() {
  paymentStore.stopPolling()
  paymentStore.reset()
  showPaymentModal.value = false
  paymentStep.value = 'select'
  agreementChecked.value = false
  paymentError.value = ''
}

/** Buy a credit pack */
const showCreditPackModal = ref(false)
async function buyCreditPack(packCode: string) {
  if (!agreementChecked.value) {
    paymentError.value = '请先阅读并同意服务协议'
    return
  }
  paymentError.value = ''
  const ok = await paymentStore.createOrder({
    order_type: 'credit_pack',
    product_code: packCode,
    channel: selectedChannel.value,
    agreement_accepted: true,
  })
  if (ok) {
    paymentStep.value = 'qr'
    showCreditPackModal.value = false
    showPaymentModal.value = true
    const unwatch = watch(() => paymentStore.pollStatus, (status) => {
      if (status === 'paid') {
        paymentStep.value = 'success'
        billingStore.fetchBalance()
        unwatch()
      } else if (['closed', 'failed'].includes(status)) {
        paymentStep.value = 'error'
        paymentError.value = '支付未完成'
        unwatch()
      }
    })
  } else {
    paymentError.value = paymentStore.error || '创建订单失败'
  }
}

/** Group conversations by today / earlier */
const todayConversations = computed(() => {
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  return chatStore.conversations.filter(c => new Date(c.created_at) >= today)
})

const earlierConversations = computed(() => {
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  return chatStore.conversations.filter(c => new Date(c.created_at) < today)
})

/** Get display label for agent mode */
function getModeLabel(mode: string | null): string {
  const map: Record<string, string> = {
    general: '全能创作Agent',
    scriptwriter: '短剧Agent',
    director: '导演助手',
  }
  return map[mode || ''] || '全能创作Agent'
}

/** Format ISO timestamp → "2026/4/3 10:49:29" style */
function formatTime(isoStr: string): string {
  try {
    const d = new Date(isoStr)
    return `${d.getFullYear()}/${d.getMonth() + 1}/${d.getDate()} ${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}:${d.getSeconds().toString().padStart(2, '0')}`
  } catch {
    return ''
  }
}

function mediaJobTypeLabel(job: any): string {
  return job?.capability === 'image' ? '图片生成' : '视频生成'
}

function mediaJobStatusLabel(status: string): string {
  const map: Record<string, string> = {
    created: '已创建',
    queued: '排队中',
    running: '生成中',
    succeeded: '已完成',
    failed: '失败',
    cancelled: '已取消',
  }
  return map[status] || status || '未知'
}

function mediaJobAssetUrl(job: any): string {
  const asset = job?.result_assets_json?.[0]
  const url = asset?.url || asset?.provider_url || ''
  if (!url) return ''
  if (/^https?:\/\//.test(url)) return url
  const apiBase = import.meta.env.VITE_API_BASE_URL || ''
  const backendBase = apiBase.replace(/\/api\/v\d+\/?$/, '')
  return url.startsWith('/') ? `${backendBase}${url}` : url
}

function isImageMediaJob(job: any): job is MediaJobPayload {
  return job?.capability === 'image'
}

async function handleCancelImageJob(jobId: number) {
  await chatStore.cancelMediaJob(jobId)
  await aiStore.fetchJobs().catch(() => undefined)
}

async function handleRetryImageJob(job: MediaJobPayload | MediaJob) {
  showImageTaskSheet.value = false
  await chatStore.retryImageJob({
    id: job.id,
    capability: 'image',
    provider_id: job.provider_id,
    model_id: job.model_id,
    provider_job_id: job.provider_job_id,
    status: job.status,
    progress: job.progress,
    request_json: job.request_json || {},
    result_assets_json: job.result_assets_json || [],
    error: job.error,
  })
}

/** Handle image load error — hide broken img, show fallback */
function onMediaImageError(e: Event): void {
  const img = e.target as HTMLImageElement
  img.style.display = 'none'
  const fallback = img.nextElementSibling as HTMLElement | null
  if (fallback) fallback.style.display = 'flex'
}
</script>

<template>
  <div class="h-screen flex">
    <!-- ═══ Left Sidebar ═══ -->
    <aside
      class="border-r-2 border-[#D4C898] flex flex-col shrink-0 transition-all duration-200"
      style="background: #FDF5D6;"
      :class="sidebarCollapsed ? 'w-0 overflow-hidden border-r-0' : 'w-[272px]'"
    >
      <!-- Top: Logo + collapse -->
      <div class="sidebar-section sidebar-header flex items-center justify-between h-[56px] shrink-0">
        <div class="flex items-center gap-2.5">
          <div class="w-7 h-7 rounded-[2px] flex items-center justify-center text-white text-[11px] font-bold" style="background: #E8A317;">D</div>
          <span class="text-[15px] font-semibold text-gray-900 whitespace-nowrap">DramaForge</span>
        </div>
        <button
          class="w-7 h-7 rounded-[2px] flex items-center justify-center text-gray-500 hover:bg-black/5 hover:text-gray-600 cursor-pointer transition-colors"
          @click="sidebarCollapsed = true"
        >
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><rect x="2" y="2" width="12" height="12" rx="2" stroke="currentColor" stroke-width="1.5"/><line x1="6" y1="2" x2="6" y2="14" stroke="currentColor" stroke-width="1.5"/></svg>
        </button>
      </div>

      <!-- + 新对话 -->
      <div class="sidebar-section sidebar-new-chat">
        <button
          class="new-chat-btn rounded-[2px] border-2 border-[#D4C898] bg-transparent text-gray-600 flex items-center hover:bg-black/5 cursor-pointer transition-colors"
          @click="handleNewChat"
        >
          <svg width="14" height="14" viewBox="0 0 16 16" fill="none"><line x1="8" y1="3" x2="8" y2="13" stroke="currentColor" stroke-width="2" stroke-linecap="round"/><line x1="3" y1="8" x2="13" y2="8" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
          <span>新对话</span>
        </button>
      </div>

      <!-- 资产库 -->
      <div class="sidebar-section">
        <div
          class="sidebar-item rounded-[2px] text-gray-600 flex items-center hover:bg-black/5 cursor-pointer transition-colors"
          @click="router.push('/assets')"
        >
          <svg width="18" height="18" viewBox="0 0 18 18" fill="none"><path d="M2.5 5.5C2.5 4.4 3.4 3.5 4.5 3.5H7L8.75 5.25H13.5C14.6 5.25 15.5 6.15 15.5 7.25V12.5C15.5 13.6 14.6 14.5 13.5 14.5H4.5C3.4 14.5 2.5 13.6 2.5 12.5V5.5Z" stroke="currentColor" stroke-width="1.4"/></svg>
          资产库
        </div>
      </div>

      <!-- 历史记录 -->
      <div class="sidebar-section sidebar-history flex items-center justify-between">
        <span class="text-[12px] text-gray-500 font-medium">历史记录</span>
        <span class="text-[12px] text-gray-500 cursor-pointer hover:text-[#E8A317] transition-colors">全部</span>
      </div>

      <!-- Conversation + Project list -->
      <div class="sidebar-section flex-1 overflow-y-auto">
        <!-- Today's conversations -->
        <template v-if="todayConversations.length">
          <div class="text-[11px] text-gray-500 px-3 mb-2">今天</div>
          <div
            v-for="conv in todayConversations"
            :key="'conv-' + conv.id"
            class="sidebar-conv-item"
            :class="chatStore.currentConversationId === conv.id ? 'sidebar-conv-active' : ''"
            @click="handleLoadConversation(conv.id)"
          >
            <div class="sidebar-conv-icon">
              <svg width="18" height="18" viewBox="0 0 18 18" fill="none"><path d="M3 4.5C3 3.67 3.67 3 4.5 3h9c.83 0 1.5.67 1.5 1.5v7c0 .83-.67 1.5-1.5 1.5H7l-2.5 2V13H4.5C3.67 13 3 12.33 3 11.5v-7z" stroke="currentColor" stroke-width="1.3"/></svg>
            </div>
            <div class="min-w-0 flex-1">
              <div class="text-[13px] text-gray-700 truncate leading-tight">{{ conv.title || '新对话' }}</div>
              <div class="text-[11px] text-gray-500 truncate mt-0.5">{{ getModeLabel(conv.mode) }}</div>
            </div>
            <button
              class="sidebar-conv-delete"
              type="button"
              title="删除对话"
              aria-label="删除对话"
              @click.stop="confirmDeleteConversation(conv)"
            >
              <Icon icon="lucide:trash-2" width="16" height="16" />
            </button>
          </div>
        </template>
        <!-- Earlier conversations -->
        <template v-if="earlierConversations.length">
          <div class="text-[11px] text-gray-400 px-3 mb-2" :class="todayConversations.length ? 'mt-4' : ''">更早</div>
          <div
            v-for="conv in earlierConversations"
            :key="'conv-e-' + conv.id"
            class="sidebar-conv-item"
            :class="chatStore.currentConversationId === conv.id ? 'sidebar-conv-active' : ''"
            @click="handleLoadConversation(conv.id)"
          >
            <div class="sidebar-conv-icon">
              <svg width="18" height="18" viewBox="0 0 18 18" fill="none"><path d="M3 4.5C3 3.67 3.67 3 4.5 3h9c.83 0 1.5.67 1.5 1.5v7c0 .83-.67 1.5-1.5 1.5H7l-2.5 2V13H4.5C3.67 13 3 12.33 3 11.5v-7z" stroke="currentColor" stroke-width="1.3"/></svg>
            </div>
            <div class="min-w-0 flex-1">
              <div class="text-[13px] text-gray-700 truncate leading-tight">{{ conv.title || '新对话' }}</div>
              <div class="text-[11px] text-gray-500 truncate mt-0.5">{{ getModeLabel(conv.mode) }}</div>
            </div>
            <button
              class="sidebar-conv-delete"
              type="button"
              title="删除对话"
              aria-label="删除对话"
              @click.stop="confirmDeleteConversation(conv)"
            >
              <Icon icon="lucide:trash-2" width="16" height="16" />
            </button>
          </div>
        </template>
        <div v-if="!chatStore.conversations.length" class="text-center text-[13px] text-gray-500 py-10">暂无记录</div>
      </div>
    </aside>

    <!-- Sidebar expand button -->
    <button
      v-if="sidebarCollapsed"
      class="absolute left-3 top-4 z-20 w-8 h-8 rounded-[2px] bg-[#FEF9E7] border-2 border-[#D4C898] flex items-center justify-center text-gray-500 hover:text-gray-600 hover:bg-black/5 cursor-pointer transition-colors"
      @click="sidebarCollapsed = false"
    >
      <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><rect x="2" y="2" width="12" height="12" rx="2" stroke="currentColor" stroke-width="1.5"/><line x1="6" y1="2" x2="6" y2="14" stroke="currentColor" stroke-width="1.5"/></svg>
    </button>

    <!-- ═══ Main Content ═══ -->
    <div class="flex-1 flex flex-col min-w-0">
      <!-- Top bar -->
      <div class="topbar">
        <TopbarActions
          @subscribe="showSubscribeSheet = true"
          @feedback="showFeedbackSheet = true"
          @notification="showNotificationSheet = true"
          @image-tasks="showImageTaskSheet = true; aiStore.fetchJobs()"
          @message="showMessageSheet = true"
        />
      </div>

      <!-- Center content (takes remaining height) -->
      <div class="flex-1 flex flex-col overflow-hidden">

        <!-- ═══ Chat Messages (any mode, after first message) ═══ -->
        <template v-if="chatStore.hasMessages">
          <!-- Messages area (scrollable, takes all available space) -->
          <div class="flex-1 overflow-y-auto flex justify-center">
            <div class="w-full max-w-[860px] px-10 py-4" style="margin: 0 auto;">
              <div v-for="(msg, idx) in chatStore.messages" :key="idx" class="chat-message" :class="'chat-' + msg.role">

                <!-- ── User message (right-aligned) ── -->
                <div v-if="msg.role === 'user'" class="chat-row-user">
                  <div class="chat-user-content">{{ msg.content }}</div>
                  <div class="chat-time">{{ formatTime(msg.created_at) }}</div>
                </div>

                <!-- ── Assistant message (left-aligned, with thinking/typing animation) ── -->
                <div v-else class="chat-row-assistant">
                  <!-- Thinking dots: streaming but no content yet -->
                  <div v-if="msg.isStreaming && !msg.content" class="chat-thinking">
                    <span class="thinking-dot" />
                    <span class="thinking-dot" />
                    <span class="thinking-dot" />
                  </div>
                  <!-- Streaming content with cursor -->
                  <div class="chat-assistant-text whitespace-pre-wrap">
                    {{ msg.content }}<span v-if="msg.isStreaming && msg.content" class="streaming-cursor">|</span>
                  </div>
                  <ImageGenerationCard
                    v-if="isImageMediaJob(msg.meta_json?.media_job)"
                    :job="msg.meta_json.media_job"
                    :cancelling="chatStore.cancellingMediaJobIds.has(msg.meta_json.media_job.id)"
                    :cancel-error="chatStore.mediaCancelErrors[msg.meta_json.media_job.id]"
                    @cancel="handleCancelImageJob"
                    @retry="handleRetryImageJob"
                  />
                  <div v-else-if="msg.meta_json?.media_job" class="chat-media-job-card">
                    <div class="chat-media-job-main">
                      <div class="chat-media-job-title">{{ mediaJobTypeLabel(msg.meta_json.media_job) }}</div>
                      <div class="chat-media-job-meta">
                        #{{ msg.meta_json.media_job.id }} · {{ mediaJobStatusLabel(msg.meta_json.media_job.status) }} · {{ msg.meta_json.media_job.model_id }}
                      </div>
                    </div>

                    <!-- 生成中 — 进度条 -->
                    <div
                      v-if="['queued', 'running', 'created'].includes(msg.meta_json.media_job.status)"
                      class="chat-media-job-progress"
                    >
                      <span :style="{ width: `${msg.meta_json.media_job.progress || 0}%` }" />
                    </div>

                    <!-- 生成成功 — 图片/视频回显 -->
                    <div
                      v-else-if="msg.meta_json.media_job.status === 'succeeded' && mediaJobAssetUrl(msg.meta_json.media_job)"
                      class="chat-media-result"
                    >
                      <template v-if="msg.meta_json.media_job.capability === 'image'">
                        <img
                          :src="mediaJobAssetUrl(msg.meta_json.media_job)"
                          :alt="'生成图片 #' + msg.meta_json.media_job.id"
                          loading="lazy"
                          class="chat-media-result-img"
                          @error="onMediaImageError"
                        />
                        <div class="chat-media-result-fallback" style="display:none;">
                          <span>🖼️ 图片加载失败</span>
                        </div>
                      </template>
                      <video
                        v-else
                        :src="mediaJobAssetUrl(msg.meta_json.media_job)"
                        controls
                        preload="metadata"
                        class="chat-media-result-video"
                      />
                      <a
                        class="chat-media-result-link"
                        :href="mediaJobAssetUrl(msg.meta_json.media_job)"
                        target="_blank"
                        rel="noreferrer"
                      >
                        查看原图
                      </a>
                    </div>

                    <!-- 生成失败 — 错误信息 -->
                    <div
                      v-else-if="msg.meta_json.media_job.status === 'failed'"
                      class="chat-media-error"
                    >
                      <span>❌ 生成失败：{{ msg.meta_json.media_job.error || '未知错误' }}</span>
                    </div>

                    <!-- 兜底 — 无结果链接时仍然保留进度条 -->
                    <div v-else class="chat-media-job-progress">
                      <span :style="{ width: `${msg.meta_json.media_job.progress || 0}%` }" />
                    </div>
                  </div>
                </div>
              </div>
              <div ref="messagesEndRef" />
            </div>
          </div>

          <!-- ── Bottom input bar (fixed to bottom) ── -->
          <div class="chat-input-bar flex justify-center">
            <div class="w-full max-w-[860px] px-10" style="margin: 0 auto;">
              <div class="chat-input-card">
                <textarea
                  v-model="userInput"
                  rows="1"
                  class="chat-input-textarea"
                  placeholder="与综合助手对话，支持多种能力..."
                  @keydown.enter.exact.prevent="startCreation"
                />
                <div class="chat-input-toolbar">
                  <!-- + upload -->
                  <button
                    class="chat-tool-btn"
                    title="上传参考素材"
                  >
                    <svg width="18" height="18" viewBox="0 0 18 18" fill="none"><line x1="9" y1="4" x2="9" y2="14" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/><line x1="4" y1="9" x2="14" y2="9" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>
                  </button>
                  <!-- Mode indicator -->
                  <button v-show="false" class="chat-mode-btn" @click="toggleMenu('mode')">
                    <svg width="14" height="14" viewBox="0 0 16 16" fill="none"><rect x="2" y="2" width="12" height="12" rx="2" stroke="currentColor" stroke-width="1.2"/><path d="M6 6h4M6 10h4" stroke="currentColor" stroke-width="1" stroke-linecap="round"/></svg>
                    <span>{{ currentModeOption.label }}</span>
                  </button>

                  <div class="flex-1" />

                  <!-- 优化提示词 -->
                  <button
                    class="chat-tool-btn"
                    :class="{ 'chat-optimize-active': optimizing }"
                    :disabled="!userInput.trim() || optimizing"
                    title="一键优化提示词"
                    @click="optimizePrompt"
                  >
                    <svg v-if="optimizing" class="animate-spin" width="16" height="16" viewBox="0 0 16 16" fill="none"><circle cx="8" cy="8" r="6" stroke="currentColor" stroke-width="1.5" stroke-dasharray="26 12" stroke-linecap="round"/></svg>
                    <svg v-else width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M8 1.5l1 3.2L12.5 6l-3.5 1.3L8 10.5l-1-3.2L3.5 6l3.5-1.3L8 1.5z" stroke="currentColor" stroke-width="1" stroke-linejoin="round"/><path d="M12.5 10.5l.4 1.3 1.4.4-1.4.4-.4 1.4-.4-1.4-1.4-.4 1.4-.4z" fill="currentColor"/></svg>
                  </button>

                  <!-- Stop / Send -->
                  <button
                    v-if="chatStore.isStreaming"
                    class="chat-send-btn chat-stop-btn"
                    @click="chatStore.stopStreaming"
                    title="停止生成"
                  >
                    <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><rect x="3" y="3" width="8" height="8" rx="1.5" fill="currentColor"/></svg>
                  </button>
                  <button
                    v-else
                    class="chat-send-btn"
                    :class="userInput.trim() ? 'chat-send-active' : ''"
                    :disabled="!userInput.trim()"
                    @click="startCreation"
                  >
                    <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M8 13V3M8 3L4 7M8 3L12 7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </template>

        <!-- ═══ Welcome Page (default / no messages) ═══ -->
        <template v-else>
        <div class="flex-1 flex flex-col items-center justify-center py-10">
        <div class="w-full max-w-[880px] px-10 flex flex-col items-center">

          <!-- Logo Avatar -->
          <div class="home-avatar">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
              <rect x="4" y="4" width="16" height="16" rx="4" fill="white"/>
              <rect x="8" y="8" width="4" height="4" rx="1" fill="#1a1a1a"/>
            </svg>
          </div>

          <!-- Greeting -->
          <h1 class="greeting-title text-[28px] text-gray-900 text-center leading-[1.4] mb-0"
            style="font-family: 'Press Start 2P', monospace; letter-spacing: 2px; text-shadow: -2px -2px 0 rgba(0,0,0,0.08), 2px -2px 0 rgba(0,0,0,0.08), -2px 2px 0 rgba(0,0,0,0.08), 2px 2px 0 rgba(0,0,0,0.08), 0 4px 0 rgba(229,37,33,0.3);">
            Hi，DramaForge 助你爆款写剧一键成片
          </h1>

          <div class="home-entry-switch" role="group" aria-label="创作入口">
            <button
              type="button"
              class="home-entry-btn"
              :class="currentMode === 'agent' ? 'home-entry-btn-active' : ''"
              @click="handleCreateAgentEntry"
            >
              创作 Agent+
            </button>
            <button
              type="button"
              class="home-entry-btn"
              @click="handleDramaAgentEntry"
            >
              短剧 Agent
            </button>
          </div>

          <!-- ─── Input card ─── -->
          <div class="input-card w-full max-w-[777px] rounded-[2px] border-2 border-[#D4C898] transition-all"
            style="margin-top: 35px; background: #FDF5D6; box-shadow: 4px 4px 0 0 rgba(0,0,0,0.4);"
            :style="showModeMenu || showModelMenu ? { borderColor: '#F5C34B', boxShadow: '0 0 0 3px rgba(241,196,15,0.25), 4px 4px 0 0 rgba(0,0,0,0.4)' } : {}">
            <!-- Top hint bar (mode-specific) -->
            <!-- Textarea -->
            <textarea
              v-model="userInput"
              rows="1"
              class="input-textarea w-full pr-7 resize-none border-none outline-none text-[16px] text-gray-900 placeholder-[#8B7A5A] bg-transparent leading-[1.8]"
              :placeholder="currentModeOption.placeholder"
              @keydown.enter.exact.prevent="startCreation"
            />

            <!-- Toolbar -->
            <div class="input-toolbar flex items-center pr-6">
              <!-- ① + 上传参考素材（所有模式） -->
              <div class="dropdown-wrapper">
                <button
                  class="w-[36px] h-[36px] rounded-[2px] border-2 border-[#D4C898] flex items-center justify-center text-gray-500 hover:bg-black/5 hover:text-gray-600 cursor-pointer transition-colors bg-transparent"
                  @click="toggleMenu('upload')"
                  title="上传参考素材"
                >
                  <!-- + 加号 -->
                  <svg width="18" height="18" viewBox="0 0 18 18" fill="none"><line x1="9" y1="4" x2="9" y2="14" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/><line x1="4" y1="9" x2="14" y2="9" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>
                </button>
                <div v-if="showUploadMenu" class="dropdown-menu dropdown-sm">
                  <div class="dropdown-item" @click="closeAllMenus()">
                    <!-- 上传箭头 -->
                    <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M8 10V3" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/><path d="M5 5.5L8 2.5l3 3" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/><path d="M2.5 10.5v2a1.5 1.5 0 001.5 1.5h8a1.5 1.5 0 001.5-1.5v-2" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/></svg>
                    <span>本地上传</span>
                  </div>
                  <div class="dropdown-item" @click="closeAllMenus()">
                    <!-- 文件夹 -->
                    <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M2 5a2 2 0 012-2h2.5l1.5 2H12a2 2 0 012 2v4a2 2 0 01-2 2H4a2 2 0 01-2-2V5z" stroke="currentColor" stroke-width="1.3"/></svg>
                    <span>从资产库选择</span>
                  </div>
                </div>
              </div>

              <!-- ② 模式切换按钮（所有模式） -->
              <div v-show="false" class="dropdown-wrapper">
                <button
                  class="toolbar-btn-text rounded-[2px] flex items-center text-gray-600 hover:bg-black/5 cursor-pointer transition-colors border-2 border-[#D4C898] bg-transparent"
                  @click="toggleMenu('mode')"
                >
                  <svg v-if="currentMode === 'agent'" width="14" height="14" viewBox="0 0 16 16" fill="none"><circle cx="8" cy="8" r="6" stroke="currentColor" stroke-width="1.2"/><ellipse cx="8" cy="8" rx="3" ry="6" stroke="currentColor" stroke-width="1"/><path d="M2 8h12" stroke="currentColor" stroke-width="1"/><path d="M2.8 5h10.4M2.8 11h10.4" stroke="currentColor" stroke-width="0.8"/></svg>
                  <svg v-else width="14" height="14" viewBox="0 0 16 16" fill="none"><rect x="2" y="4" width="12" height="8" rx="1.5" stroke="currentColor" stroke-width="1.2"/><path d="M5.5 7h5M5.5 9.5H9" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/></svg>
                  <span>{{ currentModeOption.label }}</span>
                  <!-- 下拉箭头 -->
                  <svg width="12" height="12" viewBox="0 0 12 12" fill="none" class="text-gray-400"><path d="M3.5 4.5L6 7L8.5 4.5" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/></svg>
                </button>
                <!-- 模式选择浮层 -->
                <div v-if="showModeMenu" class="dropdown-menu dropdown-mode">
                  <div
                    v-for="m in modes"
                    :key="m.key"
                    class="mode-item"
                    :class="currentMode === m.key ? 'mode-item-active' : ''"
                    @click="selectMode(m.key)"
                  >
                    <div class="mode-item-content">
                      <div class="mode-item-header">
                        <span class="mode-item-label">{{ m.label }}</span>
                        <span v-if="m.tag" class="mode-tag">{{ m.tag }}</span>
                      </div>
                      <div class="mode-item-desc">{{ m.desc }}</div>
                    </div>
                    <!-- 选中勾 -->
                    <svg v-if="currentMode === m.key" width="16" height="16" viewBox="0 0 16 16" fill="none" class="mode-check"><path d="M3.5 8l3 3 6-7" stroke="#7C3AED" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
                  </div>
                </div>
              </div>


              <!-- ④ 模型偏好（所有模式均可用） -->
              <div class="dropdown-wrapper">
                <button
                  class="toolbar-btn-icon-text rounded-[2px] flex items-center text-gray-600 hover:bg-black/5 cursor-pointer transition-colors border-2 border-[#D4C898] bg-transparent"
                  @click="toggleMenu('model')"
                  title="模型偏好"
                >
                  <svg width="14" height="14" viewBox="0 0 16 16" fill="none"><path d="M2 4h4M10 4h4M2 8h8M12 8h2M2 12h2M6 12h8" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/><circle cx="8" cy="4" r="1.5" stroke="currentColor" stroke-width="1.2"/><circle cx="11" cy="8" r="1.5" stroke="currentColor" stroke-width="1.2"/><circle cx="5" cy="12" r="1.5" stroke="currentColor" stroke-width="1.2"/></svg>
                  <span v-if="!modelAuto" class="text-[12px] text-primary-600 font-medium ml-0.5">{{ selectedModelName }}</span>
                  <svg width="12" height="12" viewBox="0 0 12 12" fill="none" class="text-gray-400"><path d="M3.5 4.5L6 7L8.5 4.5" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/></svg>
                </button>
                <div v-if="showModelMenu" class="dropdown-menu dropdown-lg">
                  <div class="dropdown-header">
                    <span class="dropdown-header-title">模型偏好</span>
                    <div class="auto-toggle" @click="toggleModelAuto">
                      <span class="auto-toggle-label">自动</span>
                      <div class="toggle-switch" :class="modelAuto ? 'toggle-on' : ''">
                        <div class="toggle-dot" />
                      </div>
                    </div>
                  </div>
                  <!-- Tabs: 对话 / 视频 / 图片 -->
                  <div class="model-tabs">
                    <button class="model-tab" :class="modelTab === 'chat' ? 'model-tab-active' : ''" @click="modelTab = 'chat'">对话</button>
                    <button class="model-tab" :class="modelTab === 'video' ? 'model-tab-active' : ''" @click="modelTab = 'video'">视频</button>
                    <button class="model-tab" :class="modelTab === 'image' ? 'model-tab-active' : ''" @click="modelTab = 'image'">图片</button>
                  </div>
                  <!-- Chat models -->
                  <template v-if="modelTab === 'chat'">
                    <div class="model-section-label">对话模型 · 用户已配置</div>
                    <div v-if="!filteredChatModels.length" class="text-center text-[13px] text-gray-400 py-6">
                      <div class="text-[28px] mb-2">💬</div>
                      暂未配置对话模型<br/>
                      <span class="text-gray-300 text-[11px]">前往 设置 → AI 模型配置 添加</span>
                    </div>
                    <div
                      v-for="m in filteredChatModels"
                      :key="m.id"
                      class="model-item"
                      :class="selectedModel === m.id && selectedModelCapability === 'chat' ? 'model-item-active' : ''"
                      @click="selectModel(m.id, 'chat')"
                    >
                      <svg width="18" height="18" viewBox="0 0 18 18" fill="none" class="model-icon"><circle cx="9" cy="9" r="6" stroke="currentColor" stroke-width="1.3"/><path d="M9 6v6M6 9h6" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/></svg>
                      <div class="flex-1 min-w-0">
                        <div class="flex items-center gap-2">
                          <span class="model-name">{{ m.name }}</span>
                          <span v-if="m.tag" class="model-tag model-tag-rec">{{ m.tag }}</span>
                        </div>
                        <div class="model-desc">{{ m.desc }}</div>
                      </div>
                      <svg v-if="selectedModel === m.id && selectedModelCapability === 'chat'" width="14" height="14" viewBox="0 0 14 14" fill="none" class="shrink-0"><path d="M3 7l3 3 5-6" stroke="#7C3AED" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>
                    </div>
                  </template>
                  <!-- Video models -->
                  <template v-if="modelTab === 'video'">
                    <div class="model-section-label">视频模型 · 用户已配置</div>
                    <div v-if="!filteredVideoModels.length" class="text-center text-[13px] text-gray-400 py-6">
                      <div class="text-[28px] mb-2">🎬</div>
                      暂未配置视频模型<br/>
                      <span class="text-gray-300 text-[11px]">前往 设置 → AI 模型配置 添加</span>
                    </div>
                    <div
                      v-for="m in filteredVideoModels"
                      :key="m.id"
                      class="model-item"
                      :class="selectedModel === m.id && selectedModelCapability === 'video' ? 'model-item-active' : ''"
                      @click="selectModel(m.id, 'video')"
                    >
                      <svg width="18" height="18" viewBox="0 0 18 18" fill="none" class="model-icon"><rect x="3" y="4" width="12" height="10" rx="2" stroke="currentColor" stroke-width="1.3"/><path d="M7 7.5l4 2.5-4 2.5z" fill="currentColor"/></svg>
                      <div class="flex-1 min-w-0">
                        <div class="flex items-center gap-2">
                          <span class="model-name">{{ m.name }}</span>
                          <span v-if="m.tag" class="model-tag model-tag-rec">{{ m.tag }}</span>
                        </div>
                        <div class="model-desc">{{ m.desc }}</div>
                      </div>
                      <svg v-if="selectedModel === m.id && selectedModelCapability === 'video'" width="14" height="14" viewBox="0 0 14 14" fill="none" class="shrink-0"><path d="M3 7l3 3 5-6" stroke="#7C3AED" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>
                    </div>
                  </template>
                  <!-- Image models -->
                  <template v-if="modelTab === 'image'">
                    <div class="model-section-label">图片模型 · 用户已配置</div>
                    <div v-if="!filteredImageModels.length" class="text-center text-[13px] text-gray-400 py-6">
                      <div class="text-[28px] mb-2">🎨</div>
                      暂未配置图片模型<br/>
                      <span class="text-gray-300 text-[11px]">前往 设置 → AI 模型配置 添加</span>
                    </div>
                    <div
                      v-for="m in filteredImageModels"
                      :key="m.id"
                      class="model-item"
                      :class="selectedModel === m.id && selectedModelCapability === 'image' ? 'model-item-active' : ''"
                      @click="selectModel(m.id, 'image')"
                    >
                      <svg width="18" height="18" viewBox="0 0 18 18" fill="none" class="model-icon"><rect x="3" y="3" width="12" height="12" rx="2" stroke="currentColor" stroke-width="1.3"/><circle cx="7" cy="7.5" r="1.5" stroke="currentColor" stroke-width="1"/><path d="M3 13l3-4 2 2 3-3 4 5" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/></svg>
                      <div class="flex-1 min-w-0">
                        <div class="flex items-center gap-2">
                          <span class="model-name">{{ m.name }}</span>
                          <span v-if="m.tag" class="model-tag model-tag-rec">{{ m.tag }}</span>
                        </div>
                        <div class="model-desc">{{ m.desc }}</div>
                      </div>
                      <svg v-if="selectedModel === m.id && selectedModelCapability === 'image'" width="14" height="14" viewBox="0 0 14 14" fill="none" class="shrink-0"><path d="M3 7l3 3 5-6" stroke="#7C3AED" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>
                    </div>
                  </template>
                </div>
              </div>

              <!-- ⑤ 画幅比例 -->
              <div class="dropdown-wrapper">
                <button
                  class="toolbar-btn-circle rounded-[2px] flex items-center justify-center text-gray-600 hover:bg-black/5 cursor-pointer transition-colors border-2 border-[#D4C898] bg-transparent"
                  @click="toggleMenu('ratio')"
                  title="画幅比例"
                >
                  <!-- 画幅/比例图标 -->
                  <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><rect x="2" y="3" width="12" height="10" rx="1.5" stroke="currentColor" stroke-width="1.3"/><path d="M2 6h12" stroke="currentColor" stroke-width="1" stroke-dasharray="2 1.5"/><path d="M6 3v10" stroke="currentColor" stroke-width="1" stroke-dasharray="2 1.5"/></svg>
                </button>
                <div v-if="showRatioMenu" class="dropdown-menu dropdown-sm">
                  <div
                    v-for="opt in ratioOptions"
                    :key="opt.value"
                    class="dropdown-item"
                    :class="selectedRatio === opt.value ? 'dropdown-item-active' : ''"
                    @click="selectedRatio = opt.value; closeAllMenus()"
                  >
                    <span class="ratio-icon">{{ opt.icon }}</span>
                    <span>{{ opt.label }}</span>
                    <svg v-if="selectedRatio === opt.value" width="14" height="14" viewBox="0 0 14 14" fill="none" class="check-icon"><path d="M3 7l3 3 5-6" stroke="#7C3AED" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>
                  </div>
                </div>
              </div>

              <div class="flex-1" />

              <!-- 一键优化提示词 -->
              <button
                class="w-[36px] h-[36px] rounded-[8px] flex items-center justify-center transition-all cursor-pointer"
                :class="optimizing ? 'text-purple-500 bg-purple-50 animate-pulse' : userInput.trim() ? 'text-gray-500 hover:bg-purple-50 hover:text-purple-500' : 'text-gray-300 cursor-not-allowed'"
                :disabled="!userInput.trim() || optimizing"
                title="一键优化提示词"
                @click="optimizePrompt"
              >
                <svg v-if="optimizing" class="animate-spin" width="18" height="18" viewBox="0 0 18 18" fill="none"><circle cx="9" cy="9" r="7" stroke="currentColor" stroke-width="1.5" stroke-dasharray="30 14" stroke-linecap="round"/></svg>
                <svg v-else width="18" height="18" viewBox="0 0 18 18" fill="none"><path d="M9 2l1.2 3.6L14 7l-3.8 1.4L9 12l-1.2-3.6L4 7l3.8-1.4L9 2z" stroke="currentColor" stroke-width="1.1" stroke-linejoin="round"/><path d="M14 12l.5 1.5L16 14l-1.5.5L14 16l-.5-1.5L12 14l1.5-.5z" fill="currentColor"/><path d="M3 13l.4 1L4.5 14.5l-1.1.5-.4 1-.4-1-1.1-.5 1.1-.5z" fill="currentColor"/></svg>
              </button>
              <!-- 发送 -->
              <button
                class="home-send-btn"
                :class="{ active: userInput.trim() }"
                :disabled="!userInput.trim() || loading"
                @click="startCreation"
              >
                <span v-if="loading" class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                <svg v-else width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M8 13V3M8 3L4 7M8 3L12 7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
              </button>
            </div>
          </div>

          <!-- ─── Quick tags ─── -->
          <div class="quick-tags flex items-center justify-center flex-wrap">
            <button
              v-for="tag in quickTags"
              :key="tag"
              class="tag-pill"
              @click="fillTag(tag)"
            >
              {{ tag }}
            </button>
          </div>

          <!-- ─── Feature cards ─── -->
          <div class="feature-section w-full">
            <h2 class="feature-section-title font-semibold text-gray-900">常用功能</h2>
            <div class="feature-cards-grid">
              <div
                v-for="card in featureCards"
                :key="card.title"
                class="feature-card rounded-[14px] overflow-hidden relative cursor-pointer group hover:shadow-lg transition-shadow"
                :style="{ background: card.bg }"
                @click="card.route ? router.push(card.route) : undefined"
              >
                <div class="absolute inset-0 bg-gradient-to-t from-black/60 via-black/10 to-transparent" />
                <span
                  v-if="card.isNew"
                  class="new-badge absolute z-10"
                >New</span>
                <div class="absolute bottom-3 left-3.5 z-10">
                  <div class="card-title text-white font-semibold leading-tight">{{ card.title }}</div>
                  <div class="card-desc text-white/70 leading-snug">{{ card.desc }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
        </div>
        </template>
        <!-- end welcome / chat switch -->

      </div>
    </div>
  </div>

  <!-- ═══════════════════════════════════════════════════════ -->
  <!-- Bottom Sheet Modals                                     -->
  <!-- ═══════════════════════════════════════════════════════ -->

  <!-- 订阅 / 积分 -->
  <ModalOverlay :visible="showSubscribeSheet" title="选择合适的计划，助力业务提升" @close="showSubscribeSheet = false">
    <template #icon>
      <div class="plan-logo">D</div>
    </template>
    <div class="plan-grid">
      <!-- 免费版 -->
      <div class="plan-card">
        <h4 class="plan-card-title">免费版</h4>
        <div class="plan-price-row">
          <span class="plan-price-big">永久免费</span>
        </div>
        <button
          class="plan-action-btn"
          :class="billingStore.planCode === 'free' ? 'plan-action-disabled' : 'plan-action-dark'"
          :disabled="billingStore.planCode === 'free'"
        >{{ billingStore.planCode === 'free' ? '当前计划' : '降级' }}</button>

        <div class="plan-section-label">积分</div>
        <ul class="plan-list">
          <li class="plan-check">每天赠送积分，当日清零</li>
          <li class="plan-cross">购买更多积分</li>
        </ul>

        <div class="plan-section-label">可用功能：</div>
        <ul class="plan-list">
          <li class="plan-check">智能生视频（需要积分）</li>
          <li class="plan-check">AI 图片设计（需要积分）</li>
          <li class="plan-check">复刻爆款视频（需要积分）</li>
        </ul>
      </div>

      <!-- 基础会员 - 包年 -->
      <div class="plan-card plan-card-featured">
        <div class="plan-card-header">
          <svg width="18" height="18" viewBox="0 0 18 18" fill="none"><path d="M9 2l2.3 4.6L16 7.5l-3.5 3.4L13.4 16 9 13.6 4.6 16l.9-5.1L2 7.5l4.7-.9L9 2z" fill="#E8A317" stroke="#E8A317" stroke-width="1"/></svg>
          <span>基础会员-包年</span>
        </div>
        <div class="plan-price-row">
          <span class="plan-price-symbol">¥</span>
          <span class="plan-price-big">379</span>
          <span class="plan-price-unit">/年</span>
          <span class="plan-discount-tag">首年优惠</span>
        </div>
        <div class="plan-price-note">首年¥379，次年续费金额¥759，自动续订，可随时取消。</div>
        <button
          class="plan-action-btn plan-action-primary"
          :disabled="billingStore.isLoading"
          @click="handleSubscribe('basic_yearly')"
        >{{ billingStore.planCode === 'basic_yearly' ? '当前计划' : '订阅包年套餐' }}</button>

        <div class="plan-section-label">积分</div>
        <ul class="plan-list">
          <li class="plan-check">每月 1200 积分，首次支付后生效<br/><span class="plan-sub">每日赠送积分，当日清零</span></li>
          <li class="plan-check">可充值积分</li>
        </ul>

        <div class="plan-section-label">免费版的所有功能，更有：</div>
        <ul class="plan-list">
          <li class="plan-check">去除品牌水印</li>
          <li class="plan-check">快速生成</li>
          <li class="plan-check">高阶模型</li>
          <li class="plan-check">可使用全部AI功能</li>
          <li class="plan-check">资产库无限量</li>
        </ul>
      </div>

      <!-- 基础会员 - 包月 -->
      <div class="plan-card plan-card-featured">
        <div class="plan-card-header">
          <svg width="18" height="18" viewBox="0 0 18 18" fill="none"><path d="M9 2l2.3 4.6L16 7.5l-3.5 3.4L13.4 16 9 13.6 4.6 16l.9-5.1L2 7.5l4.7-.9L9 2z" fill="#E8A317" stroke="#E8A317" stroke-width="1"/></svg>
          <span>基础会员-包月</span>
        </div>
        <div class="plan-price-row">
          <span class="plan-price-symbol">¥</span>
          <span class="plan-price-big">39</span>
          <span class="plan-price-unit">/月</span>
          <span class="plan-discount-tag">首月优惠</span>
        </div>
        <div class="plan-price-note">首月¥39，下月续费金额¥79，自动续订，可随时取消。</div>
        <button
          class="plan-action-btn plan-action-dark"
          :disabled="billingStore.isLoading"
          @click="handleSubscribe('basic_monthly')"
        >{{ billingStore.planCode === 'basic_monthly' ? '当前计划' : '订阅包月套餐' }}</button>

        <div class="plan-section-label">积分</div>
        <ul class="plan-list">
          <li class="plan-check">每月 1200 积分，首次支付后生效<br/><span class="plan-sub">每日赠送积分，当日清零</span></li>
          <li class="plan-check">可充值积分</li>
        </ul>

        <div class="plan-section-label">免费版的所有功能，更有：</div>
        <ul class="plan-list">
          <li class="plan-check">去除品牌水印</li>
          <li class="plan-check">快速生成</li>
          <li class="plan-check">高阶模型</li>
          <li class="plan-check">可使用全部AI功能</li>
          <li class="plan-check">资产库无限量</li>
        </ul>
      </div>
    </div>
  </ModalOverlay>

  <!-- 反馈 -->
  <BottomSheet :visible="showFeedbackSheet" title="意见反馈" height="60vh" @close="showFeedbackSheet = false">
    <div class="feedback-types">
      <button v-for="t in [{id:'bug',label:'🐛 Bug'},{id:'feature',label:'💡 建议'},{id:'other',label:'💬 其他'}]" :key="t.id"
        class="feedback-type-btn" :class="feedbackType === t.id ? 'feedback-type-active' : ''"
        @click="feedbackType = t.id">{{ t.label }}</button>
    </div>
    <textarea v-model="feedbackText" class="feedback-textarea" rows="5" placeholder="请描述你遇到的问题或建议..." />
    <button class="feedback-submit" :disabled="!feedbackText.trim()" @click="feedbackText = ''; showFeedbackSheet = false">
      提交反馈
    </button>
  </BottomSheet>

  <!-- 通知 -->
  <BottomSheet :visible="showNotificationSheet" title="通知" height="60vh" @close="showNotificationSheet = false">
    <div class="empty-sheet">
      <div class="empty-sheet-icon">🔔</div>
      <p>暂无通知</p>
      <span>新的系统通知和项目动态将显示在这里</span>
    </div>
  </BottomSheet>

  <!-- 图片任务中心 -->
  <BottomSheet :visible="showImageTaskSheet" title="图片任务" height="72vh" @close="showImageTaskSheet = false">
    <ImageTaskCenter v-model="imageTaskFilter" @retry="handleRetryImageJob" />
  </BottomSheet>

  <!-- 消息 -->
  <BottomSheet :visible="showMessageSheet" title="消息" height="60vh" @close="showMessageSheet = false">
    <div class="empty-sheet">
      <div class="empty-sheet-icon">✉️</div>
      <p>暂无消息</p>
      <span>收到的私信和系统消息将显示在这里</span>
    </div>
  </BottomSheet>

  <ConfirmDialog
    :visible="showDeleteConversationConfirm"
    title="删除对话"
    :message="`将永久删除「${deleteTargetConversation?.title || '新对话'}」。删除后无法恢复。`"
    confirm-text="确认删除"
    cancel-text="取消"
    danger
    :loading="deletingConversation"
    @confirm="handleDeleteConversation"
    @cancel="cancelDeleteConversation"
  />

  <!-- 积分不足弹窗 -->
  <ModalOverlay :visible="showInsufficientCredits" title="积分不足" subtitle="当前积分余额不足以完成此操作" width="480px" @close="showInsufficientCredits = false">
    <template #icon>
      <div style="width:48px;height:48px;border-radius:50%;background:rgba(245, 195, 75, 0.15);display:flex;align-items:center;justify-content:center;margin:0 auto 12px;font-size:24px;">⚡</div>
    </template>
    <div style="text-align:center;padding:0 20px;">
      <div style="display:flex;justify-content:center;align-items:baseline;gap:4px;margin-bottom:8px;">
        <span style="font-size:14px;color:#999;">当前余额</span>
        <span style="font-size:28px;font-weight:800;color:#E8A317;">{{ billingStore.credits }}</span>
        <span style="font-size:14px;color:#999;">积分</span>
      </div>
      <p style="font-size:13px;color:#999;margin:0 0 24px;">每次 AI 对话消耗 1-3 积分，升级会员可获得每月 1200 积分</p>
      <div style="display:flex;gap:10px;justify-content:center;">
        <button
          style="flex:1;height:44px;border-radius:12px;border:1px solid #e5e5e5;background:#fff;color:#333;font-size:13px;font-weight:600;cursor:pointer;"
          @click="showInsufficientCredits = false"
        >稍后再说</button>
        <button
          style="flex:1;height:44px;border-radius:12px;border:1px solid #E8A317;background:rgba(232, 163, 23, 0.1);color:#E8A317;font-size:13px;font-weight:600;cursor:pointer;"
          @click="showInsufficientCredits = false; showCreditPackModal = true"
        >充值积分</button>
        <button
          style="flex:1;height:44px;border-radius:12px;border:none;background:#E8A317;color:#1A1508;font-size:13px;font-weight:600;cursor:pointer;"
          @click="showInsufficientCredits = false; showSubscribeSheet = true"
        >升级套餐</button>
      </div>
    </div>
  </ModalOverlay>

  <!-- ═══════ 积分包购买弹窗 ═══════ -->
  <ModalOverlay :visible="showCreditPackModal" title="充值积分" subtitle="选择积分包，支付后即时到账" width="480px" @close="showCreditPackModal = false">
    <template #icon>
      <div style="width:48px;height:48px;border-radius:50%;background:#F3F0FF;display:flex;align-items:center;justify-content:center;margin:0 auto 8px;font-size:24px;">⚡</div>
    </template>
    <div style="padding:0 24px 24px;">
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:20px;">
        <button v-for="pack in [{code:'pack_50',name:'50 积分',price:'¥9.9',credits:50},{code:'pack_200',name:'200 积分',price:'¥29.9',credits:200},{code:'pack_500',name:'500 积分',price:'¥59.9',credits:500},{code:'pack_1200',name:'1200 积分',price:'¥99.9',credits:1200}]"
          :key="pack.code"
          style="padding:16px;border-radius:14px;border:2px solid #e5e5e5;background:#fff;cursor:pointer;text-align:center;transition:all 0.2s;"
          @click="selectedCreditPack = pack.code"
          :style="selectedCreditPack === pack.code ? { borderColor: '#E8A317', background: 'rgba(232, 163, 23, 0.1)' } : {}">
          <div style="font-size:20px;font-weight:700;color:#333;">{{ pack.credits }}</div>
          <div style="font-size:12px;color:#999;margin:4px 0;">积分</div>
          <div style="font-size:16px;font-weight:700;color:#E8A317;">{{ pack.price }}</div>
        </button>
      </div>

      <!-- 渠道选择 -->
      <div style="display:flex;gap:8px;margin-bottom:16px;">
        <button v-for="ch in [{code:'wechat',name:'微信'},{code:'alipay',name:'支付宝'},{code:'douyin',name:'抖音'}]"
          :key="ch.code"
          style="flex:1;padding:8px;border-radius:8px;border:1.5px solid #e5e5e5;background:#fff;cursor:pointer;font-size:12px;color:#666;"
          :style="selectedChannel === ch.code ? { borderColor: '#E8A317', color: '#E8A317', fontWeight: 600 } : {}"
          @click="selectedChannel = ch.code as any">
          {{ ch.name }}
        </button>
      </div>

      <!-- 协议 -->
      <label style="display:flex;align-items:flex-start;gap:8px;margin-bottom:16px;cursor:pointer;">
        <input type="checkbox" v-model="agreementChecked" style="margin-top:3px;accent-color:#E8A317;" />
        <span style="font-size:12px;color:#999;">我已阅读并同意 <a href="javascript:void(0)" style="color:#E8A317;">服务协议</a></span>
      </label>

      <div v-if="paymentError" style="color:#ef4444;font-size:13px;text-align:center;margin-bottom:12px;">{{ paymentError }}</div>

      <button
        style="width:100%;height:48px;border-radius:12px;border:none;background:#E8A317;color:#1A1508;font-size:15px;font-weight:600;cursor:pointer;"
        :disabled="!selectedCreditPack || paymentStore.isLoading"
        :style="{ opacity: !selectedCreditPack || paymentStore.isLoading ? 0.5 : 1 }"
        @click="buyCreditPack(selectedCreditPack)">
        {{ paymentStore.isLoading ? '处理中...' : '立即充值' }}
      </button>
    </div>
  </ModalOverlay>

  <!-- ═══════ 支付二维码弹窗 ═══════ -->
  <ModalOverlay :visible="showPaymentModal" :title="paymentStep === 'success' ? '支付成功' : paymentStep === 'qr' ? '扫码支付' : '选择支付方式'" width="460px" @close="closePaymentModal">
    <template #icon>
      <div style="width:48px;height:48px;border-radius:50%;display:flex;align-items:center;justify-content:center;margin:0 auto 8px;font-size:24px;"
        :style="{ background: paymentStep === 'success' ? 'rgba(46, 204, 113, 0.15)' : '#F3F0FF' }">
        {{ paymentStep === 'success' ? '✅' : paymentStep === 'error' ? '❌' : '💳' }}
      </div>
    </template>

    <div style="padding:0 24px 24px;">
      <!-- Step 1: 选择渠道 + 协议 -->
      <template v-if="paymentStep === 'select'">
        <div style="text-align:center;margin-bottom:16px;">
          <div style="font-size:22px;font-weight:700;color:#333;">
            ¥{{ pendingPaymentPlan === 'basic_yearly' ? '379' : '39' }}
          </div>
          <div style="font-size:13px;color:#999;margin-top:4px;">
            {{ pendingPaymentPlan === 'basic_yearly' ? '基础会员 · 年付' : '基础会员 · 月付' }}
          </div>
        </div>

        <!-- 支付渠道 -->
        <div style="display:flex;gap:10px;margin-bottom:20px;">
          <button v-for="ch in [{code:'wechat',name:'微信支付',icon:'💚'},{code:'alipay',name:'支付宝',icon:'🔵'},{code:'douyin',name:'抖音支付',icon:'🎵'}]"
            :key="ch.code"
            style="flex:1;padding:12px 8px;border-radius:12px;border:2px solid #e5e5e5;background:#fff;cursor:pointer;text-align:center;transition:all 0.2s;"
            :style="selectedChannel === ch.code ? { borderColor: '#E8A317', background: 'rgba(232, 163, 23, 0.1)' } : {}"
            @click="selectedChannel = ch.code as any">
            <div style="font-size:20px;">{{ ch.icon }}</div>
            <div style="font-size:12px;color:#666;margin-top:4px;">{{ ch.name }}</div>
          </button>
        </div>

        <!-- 协议勾选 -->
        <label style="display:flex;align-items:flex-start;gap:8px;margin-bottom:20px;cursor:pointer;">
          <input type="checkbox" v-model="agreementChecked" style="margin-top:3px;accent-color:#E8A317;" />
          <span style="font-size:12px;color:#999;line-height:1.5;">
            我已阅读并同意
            <a href="javascript:void(0)" style="color:#E8A317;text-decoration:underline;">《DramaForge 服务协议》</a>
            和
            <a href="javascript:void(0)" style="color:#E8A317;text-decoration:underline;">《支付协议》</a>
          </span>
        </label>

        <div v-if="paymentError" style="color:#ef4444;font-size:13px;text-align:center;margin-bottom:12px;">{{ paymentError }}</div>

        <button
          style="width:100%;height:48px;border-radius:12px;border:none;background:#E8A317;color:#1A1508;font-size:15px;font-weight:600;cursor:pointer;transition:opacity 0.2s;"
          :style="{ opacity: paymentStore.isLoading ? 0.6 : 1 }"
          :disabled="paymentStore.isLoading"
          @click="startPayment">
          {{ paymentStore.isLoading ? '创建订单中...' : '确认支付' }}
        </button>
      </template>

      <!-- Step 2: QR 码 -->
      <template v-if="paymentStep === 'qr'">
        <div style="text-align:center;">
          <div style="font-size:14px;color:#666;margin-bottom:12px;">
            请使用 <b>{{ selectedChannel === 'wechat' ? '微信' : selectedChannel === 'alipay' ? '支付宝' : '抖音' }}</b> 扫描下方二维码
          </div>

          <!-- QR Code Image -->
          <div style="display:inline-block;padding:16px;background:#fff;border-radius:16px;border:1px solid #eee;margin-bottom:16px;">
            <img v-if="paymentStore.qrBase64" :src="paymentStore.qrBase64" alt="支付二维码" style="width:200px;height:200px;" />
            <div v-else style="width:200px;height:200px;display:flex;align-items:center;justify-content:center;background:#f5f5f5;border-radius:8px;color:#999;font-size:13px;">
              二维码加载中...
            </div>
          </div>

          <div style="font-size:22px;font-weight:700;color:#E8A317;margin-bottom:4px;">
            ¥{{ paymentStore.currentOrder?.amount_cny }}
          </div>
          <div style="font-size:12px;color:#999;margin-bottom:16px;">
            {{ paymentStore.currentOrder?.product_name }}
          </div>

          <!-- Polling indicator -->
          <div style="display:flex;align-items:center;justify-content:center;gap:8px;margin-bottom:16px;">
            <div style="width:8px;height:8px;border-radius:50%;background:#F59E0B;animation:pulse 1.5s infinite;"></div>
            <span style="font-size:13px;color:#999;">等待支付...</span>
          </div>

          <button
            style="width:100%;height:44px;border-radius:12px;border:1px solid #e5e5e5;background:#fff;color:#666;font-size:14px;cursor:pointer;"
            @click="closePaymentModal">
            取消支付
          </button>
        </div>
      </template>

      <!-- Step 3: 支付成功 -->
      <template v-if="paymentStep === 'success'">
        <div style="text-align:center;">
          <div style="font-size:48px;margin-bottom:12px;">🎉</div>
          <div style="font-size:18px;font-weight:700;color:#333;margin-bottom:8px;">支付成功！</div>
          <div style="font-size:14px;color:#666;margin-bottom:24px;">
            {{ paymentStore.currentOrder?.product_name }} 已到账
          </div>
          <button
            style="width:100%;height:48px;border-radius:12px;border:none;background:#E8A317;color:#1A1508;font-size:15px;font-weight:600;cursor:pointer;"
            @click="closePaymentModal">
            完成
          </button>
        </div>
      </template>

      <!-- Step 4: 支付失败/超时 -->
      <template v-if="paymentStep === 'error'">
        <div style="text-align:center;">
          <div style="font-size:48px;margin-bottom:12px;">😔</div>
          <div style="font-size:18px;font-weight:700;color:#333;margin-bottom:8px;">支付未完成</div>
          <div style="font-size:14px;color:#999;margin-bottom:24px;">{{ paymentError || '订单已关闭或支付超时' }}</div>
          <div style="display:flex;gap:12px;">
            <button
              style="flex:1;height:44px;border-radius:12px;border:1px solid #e5e5e5;background:#fff;color:#333;font-size:14px;font-weight:600;cursor:pointer;"
              @click="closePaymentModal">
              关闭
            </button>
            <button
              style="flex:1;height:44px;border-radius:12px;border:none;background:#E8A317;color:#1A1508;font-size:14px;font-weight:600;cursor:pointer;"
              @click="paymentStep = 'select'; paymentError = ''">
              重新支付
            </button>
          </div>
        </div>
      </template>
    </div>
  </ModalOverlay>
</template>

<style scoped>
.scrollbar-hide::-webkit-scrollbar { display: none; }
.scrollbar-hide { -ms-overflow-style: none; scrollbar-width: none; }

/* ─── Sidebar ─── */
.sidebar-section {
  padding-left: 15px;
  padding-right: 15px;
}

.sidebar-header {
  padding-right: 12px;
}

.sidebar-new-chat {
  margin-top: 12px;
  margin-bottom: 6px;
}

.sidebar-history {
  margin-top: 25px;
  margin-bottom: 12px;
}

.new-chat-btn {
  width: 100%;
  height: 45px;
  padding: 0 16px;
  gap: 8px;
  font-size: 13px;
}

.sidebar-item {
  height: 45px;
  padding: 0 16px;
  gap: 8px;
  font-size: 13px;
}

/* ─── Greeting ─── */
.home-avatar {
  width: 56px;
  height: 56px;
  border-radius: 2px;
  background: #E8A317;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 18px;
  border: 3px solid #B87D08;
  box-shadow: 4px 4px 0 0 #B87D08;
}

.greeting-title {
  font-family: 'Press Start 2P', monospace;
}

.home-entry-switch {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  margin-top: 26px;
  padding: 5px;
  border: 2px solid #D4C898;
  border-radius: 999px;
  background: rgba(253, 245, 214, 0.92);
  box-shadow: 3px 3px 0 0 rgba(0, 0, 0, 0.35);
}

.home-entry-btn {
  height: 34px;
  min-width: 96px;
  padding: 0 16px;
  border: 0;
  border-radius: 999px;
  background: transparent;
  color: #1A1508;
  font-size: 13px;
  font-weight: 700;
  line-height: 1;
  cursor: pointer;
  transition: background 0.15s ease, color 0.15s ease, transform 0.15s ease;
  white-space: nowrap;
}

.home-entry-btn:hover {
  background: rgba(0, 0, 0, 0.06);
}

.home-entry-btn-active {
  background: #111111;
  color: #FFFFFF;
  box-shadow: 2px 2px 0 0 rgba(0, 0, 0, 0.3);
}

.home-entry-btn-active:hover {
  background: #111111;
  transform: translate(1px, 1px);
}

/* ─── Input card ─── */
.input-textarea {
  padding: 15px 28px 64px 20px;
}

.input-toolbar {
  padding: 0 24px 15px 15px;
  gap: 12px;
}

/* ─── Toolbar buttons ─── */
.toolbar-btn-text {
  height: 42px;
  padding: 0 18px;
  gap: 8px;
  font-size: 12px;
}

.toolbar-btn-icon-text {
  height: 42px;
  padding: 0 14px;
  gap: 6px;
}

.toolbar-btn-circle {
  width: 42px;
  height: 42px;
}

.toolbar-icon-text {
  font-size: 12px;
  font-weight: 600;
  color: currentColor;
}

/* ─── Quick tags ─── */
.quick-tags {
  margin-top: 10px;
  gap: 14px;
}

.tag-pill {
  height: 40px;
  min-width: 115px;
  padding: 0 20px;
  border-radius: 2px;
  font-size: 13px;
  color: #6B5D40;
  background: transparent;
  border: 2px solid #D4C898;
  cursor: pointer;
  transition: all 0.1s ease;
  white-space: nowrap;
  letter-spacing: 0.3px;
}

.tag-pill:hover {
  border-color: #F5C34B;
  color: #F5C34B;
  background: rgba(245, 195, 75, 0.08);
  box-shadow: 2px 2px 0 0 rgba(245, 195, 75, 0.3);
}

/* ─── Feature cards ─── */
.feature-section {
  margin-top: 100px;
}

.feature-section-title {
  font-size: 13px;
  margin-bottom: 12px;
  font-family: 'Press Start 2P', monospace;
  color: #F5C34B;
  letter-spacing: 1px;
}

.feature-cards-grid {
  display: flex;
  gap: 16px;
}

.feature-card {
  width: 235px;
  height: 115px;
  border-radius: 2px;
  border: 2px solid #D4C898;
}

.feature-card .new-badge {
  top: 8px;
  left: 10px;
  background: #E8A317;
  color: #fff;
  font-size: 10px;
  font-family: 'Press Start 2P', monospace;
  padding: 3px 8px;
  border-radius: 2px;
  letter-spacing: 1px;
  line-height: 1.4;
  border: 2px solid #B87D08;
}

.feature-card .card-title {
  font-size: 13px;
}

.feature-card .card-desc {
  font-size: 11px;
  margin-top: 3px;
}

/* ─── Dropdown menus ─── */
.dropdown-wrapper {
  position: relative;
}

.dropdown-menu {
  position: absolute;
  top: calc(100% + 8px);
  left: 0;
  background: #FEF9E7;
  border: 2px solid #D4C898;
  border-radius: 2px;
  box-shadow: 4px 4px 0 0 rgba(0, 0, 0, 0.4);
  z-index: 100;
  overflow: hidden;
  animation: dropdownFadeIn 0.15s ease;
}

@keyframes dropdownFadeIn {
  from { opacity: 0; transform: translateY(-4px); }
  to { opacity: 1; transform: translateY(0); }
}

/* ─── Top hint bar ─── */
.top-hint-bar {
  padding: 8px 20px;
  font-size: 12px;
  color: #6B5D40;
  background: #FDF4D8;
  border-bottom: 2px solid #D4C898;
  border-radius: 2px 2px 0 0;
}

/* ─── Model version tag ─── */
.model-version-tag {
  font-size: 11px;
  color: #888;
  background: #F5F5F5;
  padding: 4px 10px;
  border-radius: 12px;
  white-space: nowrap;
}

/* ─── Mode selector dropdown ─── */
.dropdown-mode {
  width: 380px;
  padding: 6px;
}

.mode-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  border-radius: 2px;
  cursor: pointer;
  transition: background 0.15s;
}

.mode-item:hover {
  background: rgba(0,0,0,0.04);
}

.mode-item-active {
  background: rgba(232, 163, 23, 0.1) !important;
}

.mode-item-content {
  flex: 1;
  min-width: 0;
}

.mode-item-header {
  display: flex;
  align-items: center;
  gap: 6px;
}

.mode-item-label {
  font-size: 14px;
  font-weight: 500;
  color: #111111;
}

.mode-tag {
  font-size: 10px;
  font-weight: 600;
  color: #fff;
  background: #E8A317;
  padding: 1px 6px;
  border-radius: 2px;
  letter-spacing: 0.3px;
}

.mode-item-desc {
  font-size: 12px;
  color: #6B5D40;
  margin-top: 2px;
  line-height: 1.4;
}

.mode-check {
  flex-shrink: 0;
}

.dropdown-sm {
  width: 200px;
  padding: 6px;
}

.dropdown-lg {
  width: 320px;
  padding: 0;
}

.dropdown-preset {
  width: 360px;
  padding: 0;
}

.dropdown-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  font-size: 13px;
  color: #2D2515;
  border-radius: 2px;
  cursor: pointer;
  transition: background 0.15s;
}

.dropdown-item:hover {
  background: rgba(0,0,0,0.04);
}

.dropdown-item-active {
  color: #F5C34B;
  background: rgba(245, 195, 75, 0.1);
}

.dropdown-item .check-icon {
  margin-left: auto;
}

.dropdown-item .ratio-icon {
  font-size: 14px;
  color: #888;
  width: 18px;
  text-align: center;
}

/* ─── Dropdown header ─── */
.dropdown-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px 10px;
}

.dropdown-header-title {
  font-size: 14px;
  font-weight: 600;
  color: #111111;
}

/* ─── Auto toggle ─── */
.auto-toggle {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.auto-toggle-label {
  font-size: 13px;
  color: #6B5D40;
}

.toggle-switch {
  width: 40px;
  height: 22px;
  border-radius: 2px;
  background: #555;
  position: relative;
  transition: background 0.2s;
  border: 2px solid #333;
}

.toggle-switch.toggle-on {
  background: #2ECC71;
  border-color: #1E8449;
}

.toggle-dot {
  width: 16px;
  height: 14px;
  border-radius: 2px;
  background: #E74C3C;
  position: absolute;
  top: 2px;
  left: 2px;
  transition: left 0.15s ease, background 0.15s ease;
  border: 2px solid #C0392B;
  box-shadow: inset -2px -2px 0 rgba(0,0,0,0.2);
}

.toggle-on .toggle-dot {
  left: 20px;
  background: #27AE60;
  border-color: #1E8449;
}

/* ─── Model tabs ─── */
.model-tabs {
  display: flex;
  gap: 0;
  padding: 0 16px;
  border-bottom: 2px solid #D4C898;
}

.model-tab {
  padding: 8px 16px;
  font-size: 13px;
  color: #8B7A5A;
  border-bottom: 2px solid transparent;
  cursor: pointer;
  transition: all 0.15s;
  background: none;
  border-top: none;
  border-left: none;
  border-right: none;
}

.model-tab:hover {
  color: #6B5D40;
}

.model-tab-active {
  color: #F5C34B;
  font-weight: 600;
  border-bottom-color: #F5C34B;
}

.model-section-label {
  font-size: 11px;
  color: #8B7A5A;
  padding: 12px 16px 4px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.model-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 10px 14px;
  cursor: pointer;
  transition: background 0.15s;
  border-radius: 2px;
  margin: 2px 6px;
}

.model-item:hover {
  background: rgba(0,0,0,0.04);
}

.model-item-active {
  background: rgba(232, 163, 23, 0.1) !important;
}

.model-item:last-child {
  border-radius: 2px;
}

.model-icon {
  color: #6B5D40;
  margin-top: 2px;
  flex-shrink: 0;
}

.model-name {
  font-size: 13px;
  font-weight: 500;
  color: #111111;
  line-height: 1.3;
}

.model-tag {
  display: inline-flex;
  align-items: center;
  padding: 1px 6px;
  border-radius: 2px;
  font-size: 10px;
  font-weight: 500;
  background: rgba(255,255,255,0.08);
  color: #6B5D40;
  white-space: nowrap;
}

.model-tag-rec {
  background: rgba(232, 163, 23, 0.15);
  color: #E8A317;
}

.model-tag-premium {
  font-size: 10px;
  padding: 1px 5px;
  border-radius: 2px;
  background: linear-gradient(135deg, #F5C34B, #C88A0C);
  color: #5D3A00;
  font-weight: 600;
  letter-spacing: 0.5px;
  line-height: 1.4;
  white-space: nowrap;
}

.model-item-locked {
  opacity: 0.65;
  position: relative;
}

.model-item-locked:hover {
  opacity: 0.8;
}

.model-desc {
  font-size: 12px;
  color: #8B7A5A;
  margin-top: 2px;
  line-height: 1.4;
}

/* ─── Preset panel ─── */
.preset-search-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px 12px;
}

.preset-search-box {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
  height: 36px;
  padding: 0 12px;
  border: 2px solid #D4C898;
  border-radius: 2px;
  background: rgba(0,0,0,0.2);
}

.preset-search-input {
  flex: 1;
  border: none;
  outline: none;
  background: transparent;
  font-size: 13px;
  color: #333333;
}

.preset-search-input::placeholder {
  color: #8B7A5A;
}

.preset-new-btn {
  height: 36px;
  padding: 0 16px;
  border-radius: 2px;
  background: #E8A317;
  color: #fff;
  font-size: 13px;
  font-weight: 500;
  border: 2px solid #B87D08;
  cursor: pointer;
  white-space: nowrap;
  transition: background 0.15s;
}

.preset-new-btn:hover {
  background: #C88A0C;
}

.preset-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 32px 16px;
  gap: 12px;
}

.preset-empty p {
  font-size: 13px;
  color: #8B7A5A;
}

/* ─── Chat Conversation View ─── */

.chat-message {
  margin-bottom: 20px;
}

/* User message — right aligned bubble */
.chat-row-user {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.chat-user-content {
  background: rgba(232, 163, 23, 0.15);
  color: #1A1508;
  font-size: 15px;
  line-height: 1.7;
  padding: 12px 18px;
  border-radius: 2px;
  max-width: 70%;
  word-break: break-word;
}

.chat-time {
  font-size: 12px;
  color: #8B7A5A;
  margin-top: 6px;
  padding-right: 4px;
}

/* Assistant message — left aligned */
.chat-row-assistant {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}

.chat-assistant-text {
  font-size: 15px;
  line-height: 1.8;
  color: #2D2515;
  max-width: 90%;
  word-break: break-word;
}

.chat-media-job-card {
  width: min(420px, 90%);
  margin-top: 12px;
  padding: 12px 14px;
  border: 2px solid #D4C898;
  border-radius: 2px;
  background: #FDF5D6;
  box-shadow: 3px 3px 0 0 rgba(0,0,0,0.25);
}

.chat-media-job-main {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.chat-media-job-title {
  font-size: 13px;
  font-weight: 700;
  color: #1A1508;
}

.chat-media-job-meta {
  font-size: 12px;
  line-height: 1.5;
  color: #6B5D40;
  word-break: break-word;
}

.chat-media-job-progress {
  height: 6px;
  margin-top: 10px;
  border: 1px solid #D4C898;
  background: rgba(255,255,255,0.55);
  overflow: hidden;
}

.chat-media-job-progress span {
  display: block;
  height: 100%;
  min-width: 4px;
  background: #E8A317;
  transition: width 0.2s ease;
}

.chat-media-job-link {
  display: inline-flex;
  align-items: center;
  margin-top: 10px;
  font-size: 12px;
  font-weight: 700;
  color: #B87D08;
}

/* ── Media result (image/video inline display) ── */
.chat-media-result {
  margin-top: 12px;
  border: 2px solid #D4C898;
  border-radius: 2px;
  overflow: hidden;
  background: rgba(0,0,0,0.03);
}

.chat-media-result-img {
  display: block;
  width: 100%;
  max-height: 480px;
  object-fit: contain;
  background: #fff;
  cursor: pointer;
  transition: opacity 0.3s ease;
}

.chat-media-result-video {
  display: block;
  width: 100%;
  max-height: 480px;
  background: #000;
  outline: none;
}

.chat-media-result-fallback {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 32px 16px;
  color: #8B7A5A;
  font-size: 13px;
  background: rgba(0,0,0,0.03);
}

.chat-media-result-link {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  margin: 8px 10px 10px;
  font-size: 12px;
  font-weight: 600;
  color: #B87D08;
  text-decoration: none;
  transition: color 0.15s;
}

.chat-media-result-link:hover {
  color: #E8A317;
}

.chat-media-error {
  margin-top: 10px;
  padding: 10px 14px;
  border-radius: 2px;
  background: rgba(231, 76, 60, 0.08);
  border: 2px solid rgba(231, 76, 60, 0.2);
  font-size: 13px;
  color: #C0392B;
  line-height: 1.5;
}

/* ── Thinking dots animation ── */
.chat-thinking {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 8px 0;
}

.thinking-dot {
  width: 7px;
  height: 7px;
  border-radius: 2px;
  background: #F5C34B;
  animation: thinkingBounce 1.4s ease-in-out infinite both;
}

.thinking-dot:nth-child(1) { animation-delay: 0s; }
.thinking-dot:nth-child(2) { animation-delay: 0.16s; }
.thinking-dot:nth-child(3) { animation-delay: 0.32s; }

@keyframes thinkingBounce {
  0%, 80%, 100% {
    transform: scale(0.6);
    opacity: 0.4;
    background: #F5C34B;
  }
  40% {
    transform: scale(1.15);
    opacity: 1;
    background: #F39C12;
  }
}

/* ── Streaming cursor ── */
.streaming-cursor {
  display: inline-block;
  color: #E8A317;
  font-weight: 500;
  font-size: 16px;
  line-height: 1;
  vertical-align: text-bottom;
  margin-left: 1px;
  animation: cursorBlink 0.7s infinite;
}

@keyframes cursorBlink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.15; }
}

/* ─── Bottom Chat Input Bar ─── */
.chat-input-bar {
  flex-shrink: 0;
  padding: 12px 0 20px;
  background: transparent;
  border-top: 2px solid #D4C898;
}

.chat-input-card {
  background: #FDF5D6;
  border: 2px solid #D4C898;
  border-radius: 2px;
  padding: 14px 16px 10px;
  box-shadow: 3px 3px 0 0 rgba(0,0,0,0.3);
  transition: border-color 0.2s, box-shadow 0.2s;
}

.chat-input-card:focus-within {
  border-color: #F5C34B;
  box-shadow: 0 0 0 3px rgba(245, 195, 75, 0.2), 3px 3px 0 0 rgba(0,0,0,0.3);
}

.chat-input-textarea {
  width: 100%;
  min-height: 24px;
  max-height: 120px;
  border: none;
  outline: none;
  resize: none;
  font-size: 15px;
  line-height: 1.6;
  color: #1A1508;
  background: transparent;
}

.chat-input-textarea::placeholder {
  color: #8B7A5A;
}

.chat-input-toolbar {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 8px;
}

.chat-tool-btn {
  width: 34px;
  height: 34px;
  border-radius: 2px;
  border: 2px solid #D4C898;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #6B5D40;
  background: transparent;
  cursor: pointer;
  transition: all 0.15s;
}

.chat-tool-btn:hover {
  background: rgba(0,0,0,0.04);
  color: #F5C34B;
}

.chat-mode-btn {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 0 12px;
  height: 34px;
  border-radius: 2px;
  border: 2px solid #D4C898;
  font-size: 13px;
  color: #6B5D40;
  background: transparent;
  cursor: pointer;
  transition: all 0.15s;
}

.chat-mode-btn:hover {
  background: rgba(0,0,0,0.04);
}

.chat-send-btn {
  width: 38px;
  height: 38px;
  border-radius: 2px;
  border: 2px solid #D4C898;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  color: #8B7A5A;
  cursor: pointer;
  transition: all 0.1s ease;
}

.chat-send-btn svg {
  color: inherit;
}

.chat-send-active {
  background: #E8A317 !important;
  border-color: #B87D08 !important;
  color: #fff !important;
  cursor: pointer;
  box-shadow: 3px 3px 0 0 #B87D08;
}

.chat-send-active svg {
  color: #fff;
  stroke: #fff;
}

.chat-send-active:hover {
  background: #C88A0C !important;
  box-shadow: 2px 2px 0 0 #B87D08;
  transform: translate(1px, 1px);
}

.chat-optimize-active {
  color: #F5C34B !important;
  background: rgba(245, 195, 75, 0.1) !important;
  border-color: #F5C34B !important;
}

/* ── Home page send button ── */
.home-send-btn {
  width: 40px;
  height: 40px;
  border-radius: 2px;
  border: 2px solid #D4C898;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  color: #8B7A5A;
  cursor: pointer;
  transition: all 0.1s ease;
}

.home-send-btn.active {
  background: #E8A317;
  border-color: #B87D08;
  color: #fff;
  cursor: pointer;
  box-shadow: 3px 3px 0 0 #B87D08;
}

.home-send-btn.active svg {
  color: #fff;
}

.home-send-btn.active svg path {
  stroke: #fff;
}

.home-send-btn.active:hover {
  background: #C88A0C;
  box-shadow: 2px 2px 0 0 #B87D08;
  transform: translate(1px, 1px);
}

.chat-stop-btn {
  background: #E8A317 !important;
  border-color: #B87D08 !important;
  color: #fff !important;
  cursor: pointer !important;
}

.chat-stop-btn:hover {
  background: #C88A0C !important;
}

/* ─── Sidebar Conversation Items ─── */
.sidebar-conv-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 2px;
  cursor: pointer;
  transition: background 0.15s;
}

.sidebar-conv-delete {
  width: 28px;
  height: 28px;
  border: 1px solid transparent;
  border-radius: 2px;
  background: transparent;
  color: #8B7A5A;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  opacity: 0;
  transform: translateX(3px);
  pointer-events: none;
  transition: opacity 0.14s ease, transform 0.14s ease, color 0.14s ease, background 0.14s ease, border-color 0.14s ease;
}

.sidebar-conv-item:hover {
  background: rgba(0,0,0,0.04);
}

.sidebar-conv-item:hover .sidebar-conv-delete,
.sidebar-conv-delete:focus-visible {
  opacity: 1;
  transform: translateX(0);
  pointer-events: auto;
}

.sidebar-conv-delete:hover {
  border-color: rgba(194, 61, 48, 0.22);
  background: rgba(194, 61, 48, 0.08);
  color: #B33A2F;
}

.sidebar-conv-delete:focus-visible {
  outline: 2px solid rgba(232, 163, 23, 0.45);
  outline-offset: 2px;
}

.sidebar-conv-active {
  background: rgba(232, 163, 23, 0.12) !important;
}

.sidebar-conv-active .sidebar-conv-delete {
  opacity: 0.86;
  transform: translateX(0);
  pointer-events: auto;
}

.sidebar-conv-icon {
  width: 32px;
  height: 32px;
  border-radius: 2px;
  background: rgba(232, 163, 23, 0.15);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #E8A317;
  flex-shrink: 0;
}

.sidebar-conv-active .sidebar-conv-icon {
  background: rgba(232, 163, 23, 0.25);
}

/* ─── Top Bar ─── */
.topbar {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding: 0 20px;
  flex-shrink: 0;
  margin-top: 4px;
}

.topbar-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

/* Credits + Subscribe red group */
.topbar-credits-group {
  display: flex;
  align-items: center;
  gap: 6px;
  height: 36px;
  padding: 0 14px;
  border-radius: 2px;
  background: rgba(232, 163, 23, 0.15);
  cursor: pointer;
  transition: all 0.15s;
  border: 2px solid rgba(232, 163, 23, 0.2);
}

.topbar-credits-group:hover {
  background: rgba(232, 163, 23, 0.25);
}

.topbar-credits-icon {
  color: #E8A317;
  font-size: 15px;
}

.topbar-credits-num {
  font-weight: 600;
  font-size: 14px;
  color: #E8A317;
}

.topbar-credits-group svg {
  color: #E8A317;
  opacity: 0.6;
}

.topbar-group-divider {
  width: 1px;
  height: 16px;
  background: rgba(232, 163, 23, 0.3);
  margin: 0 4px;
}

.topbar-subscribe {
  font-size: 13px;
  font-weight: 600;
  color: #E8A317;
}

/* Icon buttons */
.topbar-icon-btn {
  width: 36px;
  height: 36px;
  border-radius: 2px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #6B5D40;
  background: none;
  border: none;
  cursor: pointer;
  transition: all 0.15s;
}

.topbar-icon-btn:hover {
  background: rgba(0,0,0,0.04);
  color: #1A1508;
}

/* Avatar */
.topbar-avatar {
  width: 32px;
  height: 32px;
  border-radius: 2px;
  background: #E8A317;
  color: #fff;
  font-size: 12px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.15s;
  margin-left: 2px;
}

.topbar-avatar:hover {
  background: #C88A0C;
}

/* ─── Subscription Plans ─── */
.plan-logo {
  width: 48px;
  height: 48px;
  border-radius: 2px;
  background: #E8A317;
  color: #fff;
  font-size: 22px;
  font-weight: 700;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 16px;
  border: 3px solid #B87D08;
  box-shadow: 3px 3px 0 0 #B87D08;
}

.plan-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}

.plan-card {
  border: 2px solid #D4C898;
  border-radius: 2px;
  padding: 28px 24px;
  background: #FDF5D6;
}

.plan-card-featured {
  border: 2px solid #F5C34B;
}

.plan-card-title {
  font-size: 16px;
  font-weight: 700;
  color: #111111;
  margin: 0 0 12px;
}

.plan-card-header {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 16px;
  font-weight: 700;
  color: #111111;
  margin-bottom: 12px;
}

.plan-price-row {
  display: flex;
  align-items: baseline;
  gap: 2px;
  margin-bottom: 6px;
}

.plan-price-symbol {
  font-size: 16px;
  font-weight: 600;
  color: #111111;
}

.plan-price-big {
  font-size: 36px;
  font-weight: 800;
  color: #111111;
  letter-spacing: -1px;
}

.plan-price-unit {
  font-size: 14px;
  color: #6B5D40;
  margin-left: 2px;
}

.plan-discount-tag {
  font-size: 11px;
  font-weight: 600;
  color: #E74C3C;
  border: 2px solid #C0392B;
  border-radius: 2px;
  padding: 1px 6px;
  margin-left: 8px;
  white-space: nowrap;
}

.plan-price-note {
  font-size: 12px;
  color: #8B7A5A;
  margin-bottom: 16px;
  line-height: 1.5;
}

.plan-action-btn {
  width: 100%;
  height: 44px;
  border-radius: 2px;
  border: 2px solid;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.1s ease;
  margin-bottom: 20px;
  font-family: 'Press Start 2P', monospace;
  font-size: 11px;
  letter-spacing: 1px;
}

.plan-action-disabled {
  background: #D4C898;
  border-color: #D4C898;
  color: #8B7A5A;
  cursor: default;
}

.plan-action-primary {
  background: #E8A317;
  border-color: #B87D08;
  color: #fff;
  box-shadow: 3px 3px 0 0 #B87D08;
}

.plan-action-primary:hover {
  background: #C88A0C;
  box-shadow: 2px 2px 0 0 #B87D08;
  transform: translate(1px, 1px);
}

.plan-action-dark {
  background: #E8A317;
  border-color: #B87D08;
  color: #fff;
  box-shadow: 3px 3px 0 0 #B87D08;
}

.plan-action-dark:hover {
  background: #C88A0C;
  box-shadow: 2px 2px 0 0 #B87D08;
  transform: translate(1px, 1px);
}

.plan-section-label {
  font-size: 14px;
  font-weight: 700;
  color: #111111;
  margin-bottom: 10px;
}

.plan-list {
  list-style: none;
  padding: 0;
  margin: 0 0 18px;
  font-size: 13px;
  color: #2D2515;
}

.plan-list li {
  padding: 3px 0 3px 22px;
  position: relative;
  line-height: 1.7;
}

.plan-check::before {
  content: '✓';
  position: absolute;
  left: 0;
  color: #2ECC71;
  font-weight: 600;
}

.plan-cross::before {
  content: '✗';
  position: absolute;
  left: 0;
  color: #E74C3C;
  font-weight: 600;
}

.plan-sub {
  font-size: 12px;
  color: #8B7A5A;
}

/* ─── Feedback ─── */
.feedback-types {
  display: flex;
  gap: 8px;
  margin-bottom: 14px;
}

.feedback-type-btn {
  padding: 6px 16px;
  border-radius: 2px;
  border: 2px solid #D4C898;
  background: transparent;
  font-size: 13px;
  color: #6B5D40;
  cursor: pointer;
  transition: all 0.15s;
}

.feedback-type-btn:hover {
  border-color: #F5C34B;
}

.feedback-type-active {
  background: rgba(232, 163, 23, 0.15);
  border-color: #E8A317;
  color: #E8A317;
}

.feedback-textarea {
  width: 100%;
  border: 2px solid #D4C898;
  border-radius: 2px;
  padding: 12px 14px;
  font-size: 14px;
  color: #1A1508;
  background: rgba(0,0,0,0.2);
  resize: none;
  outline: none;
  line-height: 1.6;
  box-sizing: border-box;
}

.feedback-textarea:focus {
  border-color: #F5C34B;
  box-shadow: 0 0 0 3px rgba(245, 195, 75, 0.2);
}

.feedback-submit {
  width: 100%;
  height: 44px;
  border-radius: 2px;
  border: 2px solid #B87D08;
  background: #E8A317;
  color: #fff;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  margin-top: 14px;
  transition: all 0.1s ease;
  font-family: 'Press Start 2P', monospace;
  font-size: 11px;
  letter-spacing: 1px;
  box-shadow: 3px 3px 0 0 #B87D08;
}

.feedback-submit:hover:not(:disabled) {
  background: #C88A0C;
  box-shadow: 2px 2px 0 0 #B87D08;
  transform: translate(1px, 1px);
}

.feedback-submit:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

/* ─── Empty Sheet ─── */
.empty-sheet {
  text-align: center;
  padding: 40px 0;
}

.empty-sheet-icon {
  font-size: 40px;
  margin-bottom: 12px;
}

.empty-sheet p {
  font-size: 15px;
  font-weight: 600;
  color: #111111;
  margin: 0 0 6px;
}

.empty-sheet span {
  font-size: 13px;
  color: #8B7A5A;
}
</style>
