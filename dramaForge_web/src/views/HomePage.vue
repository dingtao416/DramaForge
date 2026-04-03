<script setup lang="ts">
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import { projectsApi } from '@/api/projects'
import { scriptsApi } from '@/api/scripts'
import { VideoStyle } from '@/types/enums'
import type { ProjectList } from '@/types/project'
import { useAuthStore } from '@/stores/auth'
import { useChatStore } from '@/stores/chat'
import { useBillingStore } from '@/stores/billing'
import BottomSheet from '@/components/common/BottomSheet.vue'
import ModalOverlay from '@/components/common/ModalOverlay.vue'

const router = useRouter()
const authStore = useAuthStore()
const chatStore = useChatStore()
const billingStore = useBillingStore()
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
const feedbackText = ref('')
const feedbackType = ref('bug')

/* ─── Mode definitions ─── */
type Mode = 'agent' | 'drama' | 'clip' | 'longvideo2' | 'image' | 'longvideo'

interface ModeOption {
  key: Mode
  label: string
  tag?: string
  desc: string
  placeholder: string
  topHint?: string
}

const modes: ModeOption[] = [
  { key: 'agent', label: 'Agent 模式', desc: '全能创作 Agent，图片、短片、长视频一站式创作', placeholder: '想做视频？做图片？还是来点灵感探索？' },
  { key: 'drama', label: '短剧 Agent', tag: 'New', desc: '一键进入短剧创作工作台，快速开始分镜与剧情生成', placeholder: '' },
  { key: 'clip', label: '沉浸式短片', desc: '15秒内音画同出短视频，一句话秒出片', placeholder: '描述你的想法，可用@指定素材，进行参考生视频' },
  { key: 'longvideo2', label: '智能长视频 2.0', desc: '自动多分镜编排，轻松生成高质量长片', placeholder: '描述你想创作的长视频内容...' },
  { key: 'image', label: '生成图片', desc: '输入描述即刻出图，快速验证创意灵感', placeholder: '描述你想生成的图片...' },
  { key: 'longvideo', label: '智能长视频', desc: '基础长视频流程，速度稳定均衡', placeholder: '描述你想创作的视频内容...' },
]

const currentMode = ref<Mode>('agent')
const showModeMenu = ref(false)

const currentModeOption = computed(() => modes.find(m => m.key === currentMode.value)!)

/** Map frontend mode to backend agent mode for chat */
const modeAgentMap: Record<Mode, string> = {
  agent: 'general',
  drama: 'scriptwriter',
  clip: 'director',
  longvideo2: 'director',
  image: 'general',
  longvideo: 'director',
}

function selectMode(mode: Mode) {
  currentMode.value = mode
  closeAllMenus()
}

/* ─── Dropdown states ─── */
const showUploadMenu = ref(false)
const showModelMenu = ref(false)
const showRatioMenu = ref(false)
const showPresetMenu = ref(false)

const modelAuto = ref(true)
const modelTab = ref<'video' | 'image' | 'chat'>('chat')
const selectedRatio = ref('auto')
const presetSearch = ref('')
const selectedModel = ref('')  // '' means auto

interface ModelOption {
  id: string
  name: string
  desc: string
  tag?: string                                       // '推荐' / '高质量' / '极速' 等
  modes: Mode[]                                      // 哪些前端模式下显示
  premium?: boolean                                  // 是否需要付费会员
}

// ── Chat / LLM 模型 ──
const chatModels: ModelOption[] = [
  { id: 'gpt-4.1-mini',              name: 'GPT-4.1 Mini',           desc: '快速低成本，日常对话首选',        tag: '推荐',   modes: ['agent', 'drama', 'clip', 'longvideo2', 'image', 'longvideo'] },
  { id: 'gpt-4o',                    name: 'GPT-4o',                 desc: '多模态理解，创意能力最强',        tag: '创意',   modes: ['agent', 'drama', 'clip', 'longvideo2'], premium: true },
  { id: 'claude-sonnet-4-20250514',  name: 'Claude Sonnet 4',        desc: '长文本输出质量最佳，深度编剧',    tag: '高质量', modes: ['agent', 'drama'], premium: true },
  { id: 'deepseek-v3.1',             name: 'DeepSeek V3.1',          desc: '中文理解好，性价比高',            tag: '性价比', modes: ['agent', 'drama', 'clip', 'longvideo2', 'image', 'longvideo'] },
  { id: 'glm-4.5-flash',             name: 'GLM-4.5 Flash',          desc: '极速回复，接近免费',              tag: '极速',   modes: ['agent', 'drama', 'clip', 'longvideo2', 'image', 'longvideo'] },
  { id: 'kimi-k2',                   name: 'Kimi K2',                desc: '联网搜索能力强，适合调研',                       modes: ['agent', 'drama'] },
  { id: 'gemini-3-flash-preview',    name: 'Gemini 3 Flash',         desc: 'Google 快速模型，多模态',                        modes: ['agent', 'image'] },
  { id: 'qwen-max',                  name: 'Qwen Max',               desc: '阿里通义主力，中文顶级',                         modes: ['agent', 'drama'] },
]

// ── 视频生成模型 ──
const videoModels: ModelOption[] = [
  { id: 'seedance-2.0',   name: 'SeeDance 2.0',         desc: '火山引擎，高性价比，9:16竖版',     tag: '推荐',   modes: ['clip', 'longvideo2', 'longvideo'] },
  { id: 'kling-v2.1',     name: 'Kling 可灵 V2.1',      desc: '最新版，效果最佳，Pro模式',        tag: '高质量', modes: ['clip', 'longvideo2', 'drama', 'longvideo'], premium: true },
  { id: 'veo-3.1-fast',   name: 'VEO 3.1 Fast',         desc: 'Google 快速出片，按秒计费',        tag: '极速',   modes: ['clip', 'longvideo2', 'longvideo'], premium: true },
  { id: 'wan-v2.1-i2v',   name: 'Wan 万象 图生视频',     desc: '阿里，图片驱动视频生成',                          modes: ['clip', 'longvideo2', 'longvideo'] },
  { id: 'hailuo-01',      name: 'Hailuo 海螺',           desc: 'MiniMax，支持1080p高分辨率',                      modes: ['clip', 'longvideo2'] },
  { id: 'runway-gen4',    name: 'Runway Gen-4',          desc: 'Runway 最新，运动控制优秀',                       modes: ['clip', 'longvideo2'] },
  { id: 'vidu-2.5',       name: 'Vidu 2.5',              desc: '多分辨率支持，积分制计费',                         modes: ['clip', 'longvideo2', 'longvideo'] },
  { id: 'sora-720p',      name: 'Sora 720p',             desc: 'OpenAI Sora，按秒计费',                           modes: ['clip', 'longvideo2'] },
]

// ── 图片生成模型 ──
const imageModels: ModelOption[] = [
  { id: 'gpt-image-1-mini', name: 'GPT Image Mini',     desc: 'OpenAI 原生，质量好成本低',       tag: '推荐',   modes: ['agent', 'image', 'drama'] },
  { id: 'gpt-image-1',      name: 'GPT Image 1',        desc: 'OpenAI 高质量图片生成',           tag: '高质量', modes: ['agent', 'image', 'drama'] },
  { id: 'midjourney-imagine',name: 'Midjourney',         desc: '艺术质量最高，风格化出色',        tag: '艺术',   modes: ['agent', 'image'], premium: true },
  { id: 'ideogram-v3',      name: 'Ideogram V3',        desc: '文字渲染能力强，适合海报',        tag: '文字',   modes: ['agent', 'image'] },
]

/** Get filtered models by current mode */
const filteredChatModels = computed(() => chatModels.filter(m => m.modes.includes(currentMode.value)))
const filteredVideoModels = computed(() => videoModels.filter(m => m.modes.includes(currentMode.value)))
const filteredImageModels = computed(() => imageModels.filter(m => m.modes.includes(currentMode.value)))

/** Current model display name */
const selectedModelName = computed(() => {
  if (!selectedModel.value) return '自动'
  const all = [...chatModels, ...videoModels, ...imageModels]
  return all.find(m => m.id === selectedModel.value)?.name || '自动'
})

function selectModel(id: string) {
  selectedModel.value = id
  modelAuto.value = false
  closeAllMenus()
}

/** Auto-select appropriate default model tab based on mode */
watch(currentMode, (mode) => {
  if (['clip', 'longvideo2', 'longvideo'].includes(mode)) {
    modelTab.value = 'video'
  } else if (mode === 'image') {
    modelTab.value = 'image'
  } else {
    modelTab.value = 'chat'
  }
  // Reset to auto for new mode
  selectedModel.value = ''
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
  { title: '短剧 Agent', desc: 'Seedance 2.0 多剧集一键成片', isNew: true, bg: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' },
  { title: 'Seedance 2.0', desc: '首发试用', isNew: false, bg: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)' },
  { title: '爆款复刻', desc: '自动解析爆点，参考文案/主题/画风', isNew: false, bg: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)' },
  { title: '一镜到底', desc: '多张图片生成连续自然的转场', isNew: false, bg: 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)' },
]

;(async () => {
  try {
    const { data } = await projectsApi.list({ limit: 10 })
    recentProjects.value = data
  } catch {}
})()

// Load chat conversations and billing on mount
onMounted(async () => {
  if (authStore.isLoggedIn) {
    await Promise.all([
      chatStore.fetchConversations(),
      billingStore.initialize(),
    ])
  }
})

// Auto-scroll when new messages arrive
watch(() => chatStore.messages.length, () => {
  nextTick(() => {
    messagesEndRef.value?.scrollIntoView({ behavior: 'smooth' })
  })
})

// Also scroll during streaming content updates
watch(() => chatStore.streamingContent, () => {
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
  userInput.value = ''
  await chatStore.sendMessage(input, { mode: agentMode, model })

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

async function handleLoadConversation(convId: number) {
  await chatStore.loadConversation(convId)
}

function handleLogout() {
  authStore.doLogout()
  router.push('/login')
}

async function handleSubscribe(planCode: string) {
  const ok = await billingStore.doSubscribe(planCode)
  if (ok) {
    showSubscribeSheet.value = false
  } else {
    // Error is stored in billingStore.error, user sees it
    alert(billingStore.error || '订阅失败，请稍后再试')
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
</script>

<template>
  <div class="h-screen flex">
    <!-- ═══ Left Sidebar ═══ -->
    <aside
      class="border-r border-[#EBEBEB] bg-white flex flex-col shrink-0 transition-all duration-200"
      :class="sidebarCollapsed ? 'w-0 overflow-hidden border-r-0' : 'w-[272px]'"
    >
      <!-- Top: Logo + collapse -->
      <div class="sidebar-section sidebar-header flex items-center justify-between h-[56px] shrink-0">
        <div class="flex items-center gap-2.5">
          <div class="w-7 h-7 bg-primary-600 rounded-lg flex items-center justify-center text-white text-[11px] font-bold">D</div>
          <span class="text-[15px] font-semibold text-gray-900 whitespace-nowrap">DramaForge</span>
        </div>
        <button
          class="w-7 h-7 rounded-md flex items-center justify-center text-gray-400 hover:bg-gray-100 hover:text-gray-600 cursor-pointer transition-colors"
          @click="sidebarCollapsed = true"
        >
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><rect x="2" y="2" width="12" height="12" rx="2" stroke="currentColor" stroke-width="1.5"/><line x1="6" y1="2" x2="6" y2="14" stroke="currentColor" stroke-width="1.5"/></svg>
        </button>
      </div>

      <!-- + 新对话 -->
      <div class="sidebar-section sidebar-new-chat">
        <button
          class="new-chat-btn rounded-full border border-[#E5E5E5] bg-white text-gray-600 flex items-center hover:bg-gray-50 cursor-pointer transition-colors"
          @click="handleNewChat"
        >
          <svg width="14" height="14" viewBox="0 0 16 16" fill="none"><line x1="8" y1="3" x2="8" y2="13" stroke="currentColor" stroke-width="2" stroke-linecap="round"/><line x1="3" y1="8" x2="13" y2="8" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
          <span>新对话</span>
        </button>
      </div>

      <!-- 资产库 -->
      <div class="sidebar-section">
        <div
          class="sidebar-item rounded-[10px] text-gray-600 flex items-center hover:bg-gray-50 cursor-pointer transition-colors"
          @click="router.push('/assets')"
        >
          <svg width="18" height="18" viewBox="0 0 18 18" fill="none"><path d="M2.5 5.5C2.5 4.4 3.4 3.5 4.5 3.5H7L8.75 5.25H13.5C14.6 5.25 15.5 6.15 15.5 7.25V12.5C15.5 13.6 14.6 14.5 13.5 14.5H4.5C3.4 14.5 2.5 13.6 2.5 12.5V5.5Z" stroke="currentColor" stroke-width="1.4"/></svg>
          资产库
        </div>
      </div>

      <!-- 历史记录 -->
      <div class="sidebar-section sidebar-history flex items-center justify-between">
        <span class="text-[12px] text-gray-400 font-medium">历史记录</span>
        <span class="text-[12px] text-gray-400 cursor-pointer hover:text-primary-600 transition-colors">全部</span>
      </div>

      <!-- Conversation + Project list -->
      <div class="sidebar-section flex-1 overflow-y-auto">
        <!-- Today's conversations -->
        <template v-if="todayConversations.length">
          <div class="text-[11px] text-gray-400 px-3 mb-2">今天</div>
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
              <div class="text-[13px] text-gray-800 truncate leading-tight">{{ conv.title || '新对话' }}</div>
              <div class="text-[11px] text-gray-400 truncate mt-0.5">{{ getModeLabel(conv.mode) }}</div>
            </div>
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
              <div class="text-[13px] text-gray-800 truncate leading-tight">{{ conv.title || '新对话' }}</div>
              <div class="text-[11px] text-gray-400 truncate mt-0.5">{{ getModeLabel(conv.mode) }}</div>
            </div>
          </div>
        </template>
        <div v-if="!chatStore.conversations.length" class="text-center text-[13px] text-gray-400 py-10">暂无记录</div>
      </div>
    </aside>

    <!-- Sidebar expand button -->
    <button
      v-if="sidebarCollapsed"
      class="absolute left-3 top-4 z-20 w-8 h-8 rounded-lg bg-white border border-gray-200 flex items-center justify-center text-gray-400 hover:text-gray-600 hover:bg-gray-50 cursor-pointer shadow-sm transition-colors"
      @click="sidebarCollapsed = false"
    >
      <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><rect x="2" y="2" width="12" height="12" rx="2" stroke="currentColor" stroke-width="1.5"/><line x1="6" y1="2" x2="6" y2="14" stroke="currentColor" stroke-width="1.5"/></svg>
    </button>

    <!-- ═══ Main Content ═══ -->
    <div class="flex-1 flex flex-col bg-white min-w-0">
      <!-- Top bar -->
      <div class="topbar">
        <div class="topbar-actions">
          <!-- Credits + Subscribe (purple bg group) -->
          <div class="topbar-credits-group" @click="showSubscribeSheet = true">
            <span class="topbar-credits-icon">✦</span>
            <span class="topbar-credits-num">{{ billingStore.credits }}</span>
            <svg width="10" height="10" viewBox="0 0 10 10" fill="none"><path d="M3 4L5 6L7 4" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/></svg>
            <div class="topbar-group-divider" />
            <span class="topbar-subscribe">订阅</span>
          </div>
          <!-- Feedback -->
          <button class="topbar-icon-btn" title="反馈" @click="showFeedbackSheet = true">
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none"><path d="M4 5.5A1.5 1.5 0 015.5 4h9A1.5 1.5 0 0116 5.5v7a1.5 1.5 0 01-1.5 1.5H8.5L6 16v-3H5.5A1.5 1.5 0 014 11.5v-6z" stroke="currentColor" stroke-width="1.4" stroke-linejoin="round"/><path d="M7.5 8h5M7.5 10.5h3" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/></svg>
          </button>
          <!-- Notification -->
          <button class="topbar-icon-btn" title="通知" @click="showNotificationSheet = true">
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none"><path d="M10 3a4 4 0 00-4 4v3c0 .9-.4 1.75-1.1 2.35l-.4.3a.75.75 0 00.5 1.35h10a.75.75 0 00.5-1.35l-.4-.3A3.5 3.5 0 0114 10V7a4 4 0 00-4-4z" stroke="currentColor" stroke-width="1.4"/><path d="M8 14s.5 2 2 2 2-2 2-2" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/></svg>
          </button>
          <!-- Messages -->
          <button class="topbar-icon-btn" title="消息" @click="showMessageSheet = true">
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none"><rect x="3" y="4.5" width="14" height="10" rx="1.5" stroke="currentColor" stroke-width="1.4"/><path d="M3 6l7 4.5L17 6" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/></svg>
          </button>
          <!-- Avatar -->
          <div
            class="topbar-avatar"
            :title="authStore.isLoggedIn ? authStore.displayName : '未登录'"
            @click="authStore.isLoggedIn ? handleLogout() : router.push('/login')"
          >{{ authStore.isLoggedIn ? authStore.displayName.charAt(0).toUpperCase() : 'U' }}</div>
        </div>
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

                <!-- ── Assistant message (left-aligned, with tool calls) ── -->
                <div v-else class="chat-row-assistant">
                  <div class="chat-assistant-text whitespace-pre-wrap">{{ msg.content }}<span v-if="msg.isStreaming" class="streaming-cursor">▍</span></div>
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
                  <button class="chat-mode-btn" @click="toggleMenu('mode')">
                    <svg width="14" height="14" viewBox="0 0 16 16" fill="none"><rect x="2" y="2" width="12" height="12" rx="2" stroke="currentColor" stroke-width="1.2"/><path d="M6 6h4M6 10h4" stroke="currentColor" stroke-width="1" stroke-linecap="round"/></svg>
                    <span>{{ currentModeOption.label }}</span>
                  </button>

                  <div class="flex-1" />

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
          <h1 class="greeting-title text-[42px] font-bold text-gray-900 text-center leading-[1.2] tracking-[-0.5px] mb-0">
            Hi，DramaForge 助你爆款写剧一键成片
          </h1>

          <!-- ─── Input card ─── -->
          <div class="input-card w-full max-w-[777px] bg-white rounded-[24px] border border-[#E5E5E5] shadow-[0_1px_4px_rgba(0,0,0,0.03)] focus-within:border-[#C4B5FD] focus-within:shadow-[0_0_0_3px_rgba(124,58,237,0.06)] transition-all" style="margin-top: 35px;">
            <!-- Top hint bar (mode-specific) -->
            <div v-if="currentModeOption.topHint" class="top-hint-bar">
              {{ currentModeOption.topHint }}
            </div>

            <!-- Textarea -->
            <textarea
              v-model="userInput"
              rows="1"
              class="input-textarea w-full pr-7 resize-none border-none outline-none text-[16px] text-gray-800 placeholder-gray-400 bg-transparent leading-[1.8]"
              :placeholder="currentModeOption.placeholder"
              @keydown.enter.exact.prevent="startCreation"
            />

            <!-- Toolbar -->
            <div class="input-toolbar flex items-center pr-6">
              <!-- ① + 上传参考素材（所有模式） -->
              <div class="dropdown-wrapper">
                <button
                  class="w-[36px] h-[36px] rounded-[10px] border border-[#E5E5E5] flex items-center justify-center text-gray-500 hover:bg-gray-50 hover:text-gray-700 cursor-pointer transition-colors bg-white"
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
              <div class="dropdown-wrapper">
                <button
                  class="toolbar-btn-text rounded-full flex items-center text-gray-600 hover:bg-gray-50 cursor-pointer transition-colors border border-[#E5E5E5] bg-white"
                  @click="toggleMenu('mode')"
                >
                  <!-- Agent 模式 — 地球/网络图标 -->
                  <svg v-if="currentMode === 'agent'" width="14" height="14" viewBox="0 0 16 16" fill="none"><circle cx="8" cy="8" r="6" stroke="currentColor" stroke-width="1.2"/><ellipse cx="8" cy="8" rx="3" ry="6" stroke="currentColor" stroke-width="1"/><path d="M2 8h12" stroke="currentColor" stroke-width="1"/><path d="M2.8 5h10.4M2.8 11h10.4" stroke="currentColor" stroke-width="0.8"/></svg>
                  <!-- 沉浸式短片 — 闪电图标 -->
                  <svg v-else-if="currentMode === 'clip'" width="14" height="14" viewBox="0 0 16 16" fill="none"><path d="M9.5 1.5L4 9h4l-1.5 5.5L13 7H9l.5-5.5z" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/></svg>
                  <!-- 智能长视频2.0 — 视频+星星图标 -->
                  <svg v-else-if="currentMode === 'longvideo2'" width="14" height="14" viewBox="0 0 16 16" fill="none"><rect x="1" y="3.5" width="11" height="8" rx="1.5" stroke="currentColor" stroke-width="1.2"/><polygon points="6,6 6,9.5 9,7.75" fill="currentColor"/><path d="M13.5 2l.4 1.2 1.1.3-1.1.3-.4 1.2-.4-1.2-1.1-.3 1.1-.3z" fill="currentColor"/></svg>
                  <!-- 生成图片 — 风景画图标 -->
                  <svg v-else-if="currentMode === 'image'" width="14" height="14" viewBox="0 0 16 16" fill="none"><rect x="1.5" y="2.5" width="13" height="11" rx="2" stroke="currentColor" stroke-width="1.2"/><circle cx="5.5" cy="6" r="1.5" stroke="currentColor" stroke-width="1"/><path d="M2 12l3-3.5 2.5 2 3-4L14.5 12" stroke="currentColor" stroke-width="1.1" stroke-linecap="round" stroke-linejoin="round"/></svg>
                  <!-- 智能长视频 — 场记板图标 -->
                  <svg v-else-if="currentMode === 'longvideo'" width="14" height="14" viewBox="0 0 16 16" fill="none"><rect x="2" y="4" width="12" height="9" rx="1.5" stroke="currentColor" stroke-width="1.2"/><path d="M2 7h12" stroke="currentColor" stroke-width="1"/><path d="M5 4L7 7M9 4l2 3" stroke="currentColor" stroke-width="1" stroke-linecap="round"/></svg>
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
                  class="toolbar-btn-icon-text rounded-full flex items-center text-gray-600 hover:bg-gray-50 cursor-pointer transition-colors border border-[#E5E5E5] bg-white"
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
                    <div class="auto-toggle" @click="modelAuto = !modelAuto; if(modelAuto) selectedModel = ''">
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
                    <div class="model-section-label">对话模型 · {{ currentModeOption.label }}</div>
                    <div
                      v-for="m in filteredChatModels"
                      :key="m.id"
                      class="model-item"
                      :class="[selectedModel === m.id ? 'model-item-active' : '', m.premium && billingStore.planCode === 'free' ? 'model-item-locked' : '']"
                      @click="m.premium && billingStore.planCode === 'free' ? showSubscriptionModal = true : selectModel(m.id)"
                    >
                      <svg width="18" height="18" viewBox="0 0 18 18" fill="none" class="model-icon"><circle cx="9" cy="9" r="6" stroke="currentColor" stroke-width="1.3"/><path d="M9 6v6M6 9h6" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/></svg>
                      <div class="flex-1 min-w-0">
                        <div class="flex items-center gap-2">
                          <span class="model-name">{{ m.name }}</span>
                          <span v-if="m.tag" class="model-tag" :class="m.tag === '推荐' ? 'model-tag-rec' : ''">{{ m.tag }}</span>
                          <span v-if="m.premium" class="model-tag-premium">PRO</span>
                        </div>
                        <div class="model-desc">{{ m.desc }}</div>
                      </div>
                      <svg v-if="m.premium && billingStore.planCode === 'free'" width="14" height="14" viewBox="0 0 14 14" fill="none" class="shrink-0 text-amber-500"><path d="M7 1.5l1.5 3H12l-2.5 2 1 3.5L7 8l-3.5 2 1-3.5L2 4.5h3.5z" fill="currentColor"/></svg>
                      <svg v-else-if="selectedModel === m.id" width="14" height="14" viewBox="0 0 14 14" fill="none" class="shrink-0"><path d="M3 7l3 3 5-6" stroke="#7C3AED" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>
                    </div>
                  </template>
                  <!-- Video models -->
                  <template v-if="modelTab === 'video'">
                    <div class="model-section-label">视频模型 · {{ currentModeOption.label }}</div>
                    <div v-if="!filteredVideoModels.length" class="text-center text-[13px] text-gray-400 py-4">当前模式无视频模型</div>
                    <div
                      v-for="m in filteredVideoModels"
                      :key="m.id"
                      class="model-item"
                      :class="[selectedModel === m.id ? 'model-item-active' : '', m.premium && billingStore.planCode === 'free' ? 'model-item-locked' : '']"
                      @click="m.premium && billingStore.planCode === 'free' ? showSubscriptionModal = true : selectModel(m.id)"
                    >
                      <svg width="18" height="18" viewBox="0 0 18 18" fill="none" class="model-icon"><rect x="3" y="4" width="12" height="10" rx="2" stroke="currentColor" stroke-width="1.3"/><path d="M7 7.5l4 2.5-4 2.5z" fill="currentColor"/></svg>
                      <div class="flex-1 min-w-0">
                        <div class="flex items-center gap-2">
                          <span class="model-name">{{ m.name }}</span>
                          <span v-if="m.tag" class="model-tag" :class="m.tag === '推荐' ? 'model-tag-rec' : ''">{{ m.tag }}</span>
                          <span v-if="m.premium" class="model-tag-premium">PRO</span>
                        </div>
                        <div class="model-desc">{{ m.desc }}</div>
                      </div>
                      <svg v-if="m.premium && billingStore.planCode === 'free'" width="14" height="14" viewBox="0 0 14 14" fill="none" class="shrink-0 text-amber-500"><path d="M7 1.5l1.5 3H12l-2.5 2 1 3.5L7 8l-3.5 2 1-3.5L2 4.5h3.5z" fill="currentColor"/></svg>
                      <svg v-else-if="selectedModel === m.id" width="14" height="14" viewBox="0 0 14 14" fill="none" class="shrink-0"><path d="M3 7l3 3 5-6" stroke="#7C3AED" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>
                    </div>
                  </template>
                  <!-- Image models -->
                  <template v-if="modelTab === 'image'">
                    <div class="model-section-label">图片模型 · {{ currentModeOption.label }}</div>
                    <div v-if="!filteredImageModels.length" class="text-center text-[13px] text-gray-400 py-4">当前模式无图片模型</div>
                    <div
                      v-for="m in filteredImageModels"
                      :key="m.id"
                      class="model-item"
                      :class="[selectedModel === m.id ? 'model-item-active' : '', m.premium && billingStore.planCode === 'free' ? 'model-item-locked' : '']"
                      @click="m.premium && billingStore.planCode === 'free' ? showSubscriptionModal = true : selectModel(m.id)"
                    >
                      <svg width="18" height="18" viewBox="0 0 18 18" fill="none" class="model-icon"><rect x="3" y="3" width="12" height="12" rx="2" stroke="currentColor" stroke-width="1.3"/><circle cx="7" cy="7.5" r="1.5" stroke="currentColor" stroke-width="1"/><path d="M3 13l3-4 2 2 3-3 4 5" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/></svg>
                      <div class="flex-1 min-w-0">
                        <div class="flex items-center gap-2">
                          <span class="model-name">{{ m.name }}</span>
                          <span v-if="m.tag" class="model-tag" :class="m.tag === '推荐' ? 'model-tag-rec' : ''">{{ m.tag }}</span>
                          <span v-if="m.premium" class="model-tag-premium">PRO</span>
                        </div>
                        <div class="model-desc">{{ m.desc }}</div>
                      </div>
                      <svg v-if="m.premium && billingStore.planCode === 'free'" width="14" height="14" viewBox="0 0 14 14" fill="none" class="shrink-0 text-amber-500"><path d="M7 1.5l1.5 3H12l-2.5 2 1 3.5L7 8l-3.5 2 1-3.5L2 4.5h3.5z" fill="currentColor"/></svg>
                      <svg v-else-if="selectedModel === m.id" width="14" height="14" viewBox="0 0 14 14" fill="none" class="shrink-0"><path d="M3 7l3 3 5-6" stroke="#7C3AED" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>
                    </div>
                  </template>
                </div>
              </div>

              <!-- ⑤ @引用素材（仅沉浸式短片） -->
              <button v-if="currentMode === 'clip'" class="toolbar-btn-circle rounded-full flex items-center justify-center text-gray-600 hover:bg-gray-50 cursor-pointer transition-colors border border-[#E5E5E5] bg-white" title="@引用素材">
                <!-- @ 符号 -->
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><circle cx="8" cy="8" r="2.5" stroke="currentColor" stroke-width="1.2"/><path d="M10.5 8v1a2 2 0 004 0V8a6 6 0 10-2 4.5" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/></svg>
              </button>

              <!-- ⑥ 画幅比例（所有模式通用） -->
              <div class="dropdown-wrapper">
                <button
                  class="toolbar-btn-circle rounded-full flex items-center justify-center text-gray-600 hover:bg-gray-50 cursor-pointer transition-colors border border-[#E5E5E5] bg-white"
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

              <!-- ⑦ 参考（仅沉浸式短片） -->
              <button v-if="currentMode === 'clip'" class="toolbar-btn-circle rounded-full flex items-center justify-center text-gray-600 hover:bg-gray-50 cursor-pointer transition-colors border border-[#E5E5E5] bg-white" title="参考风格">
                <!-- 链接/参考图标 -->
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M6.5 9.5l3-3" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/><path d="M9 7l1.5-1.5a2.12 2.12 0 013 3L12 10" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/><path d="M7 9L5.5 10.5a2.12 2.12 0 01-3-3L4 6" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/></svg>
              </button>

              <!-- ⑧ 时长选择（仅沉浸式短片） -->
              <button v-if="currentMode === 'clip'" class="toolbar-btn-circle rounded-full flex items-center justify-center text-gray-600 hover:bg-gray-50 cursor-pointer transition-colors border border-[#E5E5E5] bg-white" title="时长选择">
                <!-- 时钟图标 -->
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><circle cx="8" cy="8" r="6" stroke="currentColor" stroke-width="1.2"/><path d="M8 5v3.5l2.5 1.5" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/></svg>
              </button>

              <!-- ⑨ 创作偏好（仅智能长视频2.0） -->
              <button v-if="currentMode === 'longvideo2'" class="toolbar-btn-circle rounded-full flex items-center justify-center text-gray-600 hover:bg-gray-50 cursor-pointer transition-colors border border-[#E5E5E5] bg-white" title="创作偏好">
                <!-- 调色板/画笔图标 -->
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><circle cx="8" cy="8" r="6" stroke="currentColor" stroke-width="1.2"/><circle cx="5.5" cy="6.5" r="1" fill="currentColor"/><circle cx="8" cy="5" r="1" fill="currentColor"/><circle cx="10.5" cy="6.5" r="1" fill="currentColor"/><circle cx="5.5" cy="9.5" r="1" fill="currentColor"/></svg>
              </button>

              <!-- ⑩ 预设提示词（Agent / 沉浸式短片 / 智能长视频2.0 / 生成图片 / 智能长视频） -->
              <div v-if="['agent', 'clip', 'longvideo2', 'image', 'longvideo'].includes(currentMode)" class="dropdown-wrapper">
                <button
                  class="toolbar-btn-circle rounded-full flex items-center justify-center text-gray-600 hover:bg-gray-50 cursor-pointer transition-colors border border-[#E5E5E5] bg-white"
                  @click="toggleMenu('preset')"
                  title="预设提示词"
                >
                  <!-- 文档/模板图标 -->
                  <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M4 2h6l4 4v7.5a1.5 1.5 0 01-1.5 1.5h-7A1.5 1.5 0 014 13.5V2z" stroke="currentColor" stroke-width="1.2" stroke-linejoin="round"/><path d="M10 2v4h4" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/><path d="M6.5 8.5h3M6.5 11h5" stroke="currentColor" stroke-width="1" stroke-linecap="round"/></svg>
                </button>
                <div v-if="showPresetMenu" class="dropdown-menu dropdown-preset">
                  <div class="dropdown-header">
                    <div class="flex items-center gap-2">
                      <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><rect x="2" y="2" width="12" height="12" rx="2" stroke="currentColor" stroke-width="1.3"/><line x1="5" y1="6" x2="11" y2="6" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/><line x1="5" y1="10" x2="9" y2="10" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/></svg>
                      <span class="dropdown-header-title">预设提示词</span>
                    </div>
                    <div class="flex items-center gap-2">
                      <svg width="14" height="14" viewBox="0 0 14 14" fill="none" class="text-gray-400 cursor-pointer hover:text-gray-600"><path d="M7 2v10M2 7h10" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/></svg>
                      <svg width="14" height="14" viewBox="0 0 14 14" fill="none" class="text-gray-400 cursor-pointer hover:text-gray-600"><path d="M2 4h10M4 4v7a1 1 0 001 1h4a1 1 0 001-1V4" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/></svg>
                    </div>
                  </div>
                  <div class="preset-search-row">
                    <div class="preset-search-box">
                      <svg width="14" height="14" viewBox="0 0 14 14" fill="none" class="text-gray-400"><circle cx="6" cy="6" r="4" stroke="currentColor" stroke-width="1.3"/><path d="M9.5 9.5L12 12" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/></svg>
                      <input v-model="presetSearch" class="preset-search-input" placeholder="搜索预设..." />
                    </div>
                    <button class="preset-new-btn">+ 新建</button>
                  </div>
                  <div class="preset-empty">
                    <svg width="48" height="48" viewBox="0 0 48 48" fill="none" class="text-gray-200"><rect x="8" y="6" width="32" height="36" rx="4" stroke="currentColor" stroke-width="2"/><path d="M16 18h16M16 26h10" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
                    <p>暂无预设，点击新建创建第一个预设</p>
                  </div>
                </div>
              </div>

              <div class="flex-1" />

              <!-- 一键优化提示词（固定） -->
              <button class="w-[36px] h-[36px] rounded-[8px] flex items-center justify-center text-gray-400 hover:bg-gray-100 hover:text-primary-500 cursor-pointer transition-colors" title="一键优化提示词">
                <!-- 魔法棒/星火图标 -->
                <svg width="18" height="18" viewBox="0 0 18 18" fill="none"><path d="M9 2l1.2 3.6L14 7l-3.8 1.4L9 12l-1.2-3.6L4 7l3.8-1.4L9 2z" stroke="currentColor" stroke-width="1.1" stroke-linejoin="round"/><path d="M14 12l.5 1.5L16 14l-1.5.5L14 16l-.5-1.5L12 14l1.5-.5z" fill="currentColor"/><path d="M3 13l.4 1L4.5 14.5l-1.1.5-.4 1-.4-1-1.1-.5 1.1-.5z" fill="currentColor"/></svg>
              </button>
              <!-- 发送 -->
              <button
                class="w-[40px] h-[40px] rounded-full flex items-center justify-center transition-all cursor-pointer"
                :class="userInput.trim()
                  ? 'bg-gray-900 text-white hover:bg-black shadow-[0_2px_8px_rgba(0,0,0,0.15)]'
                  : 'bg-gray-100 text-gray-400 cursor-not-allowed'"
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
          <svg width="18" height="18" viewBox="0 0 18 18" fill="none"><path d="M9 2l2.3 4.6L16 7.5l-3.5 3.4L13.4 16 9 13.6 4.6 16l.9-5.1L2 7.5l4.7-.9L9 2z" fill="#7c3aed" stroke="#7c3aed" stroke-width="1"/></svg>
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
          <svg width="18" height="18" viewBox="0 0 18 18" fill="none"><path d="M9 2l2.3 4.6L16 7.5l-3.5 3.4L13.4 16 9 13.6 4.6 16l.9-5.1L2 7.5l4.7-.9L9 2z" fill="#7c3aed" stroke="#7c3aed" stroke-width="1"/></svg>
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

  <!-- 消息 -->
  <BottomSheet :visible="showMessageSheet" title="消息" height="60vh" @close="showMessageSheet = false">
    <div class="empty-sheet">
      <div class="empty-sheet-icon">✉️</div>
      <p>暂无消息</p>
      <span>收到的私信和系统消息将显示在这里</span>
    </div>
  </BottomSheet>

  <!-- 积分不足弹窗 -->
  <ModalOverlay :visible="showInsufficientCredits" title="积分不足" subtitle="当前积分余额不足以完成此操作" width="480px" @close="showInsufficientCredits = false">
    <template #icon>
      <div style="width:48px;height:48px;border-radius:50%;background:#FEF3C7;display:flex;align-items:center;justify-content:center;margin:0 auto 12px;font-size:24px;">⚡</div>
    </template>
    <div style="text-align:center;padding:0 20px;">
      <div style="display:flex;justify-content:center;align-items:baseline;gap:4px;margin-bottom:8px;">
        <span style="font-size:14px;color:#999;">当前余额</span>
        <span style="font-size:28px;font-weight:800;color:#7c3aed;">{{ billingStore.credits }}</span>
        <span style="font-size:14px;color:#999;">积分</span>
      </div>
      <p style="font-size:13px;color:#999;margin:0 0 24px;">每次 AI 对话消耗 1-3 积分，升级会员可获得每月 1200 积分</p>
      <div style="display:flex;gap:12px;justify-content:center;">
        <button
          style="flex:1;height:44px;border-radius:12px;border:1px solid #e5e5e5;background:#fff;color:#333;font-size:14px;font-weight:600;cursor:pointer;"
          @click="showInsufficientCredits = false"
        >稍后再说</button>
        <button
          style="flex:1;height:44px;border-radius:12px;border:none;background:#7c3aed;color:#fff;font-size:14px;font-weight:600;cursor:pointer;"
          @click="showInsufficientCredits = false; showSubscribeSheet = true"
        >升级套餐</button>
      </div>
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
  border-radius: 50%;
  background: #1a1a1a;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 18px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
}

.greeting-title {
  font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Helvetica Neue', sans-serif;
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
  border-radius: 20px;
  font-size: 13px;
  color: #444;
  background: #fff;
  border: 1px solid #E8E8E8;
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
  letter-spacing: 0.3px;
}

.tag-pill:hover {
  border-color: #C4B5FD;
  color: #7C3AED;
  background: #F5F3FF;
  box-shadow: 0 1px 6px rgba(124, 58, 237, 0.08);
}

/* ─── Feature cards ─── */
.feature-section {
  margin-top: 100px;
}

.feature-section-title {
  font-size: 13px;
  margin-bottom: 12px;
}

.feature-cards-grid {
  display: flex;
  gap: 16px;
}

.feature-card {
  width: 235px;
  height: 115px;
}

.feature-card .new-badge {
  top: 8px;
  left: 10px;
  background: linear-gradient(135deg, #34d399, #10b981);
  color: #fff;
  font-size: 9px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 10px;
  letter-spacing: 0.5px;
  line-height: 1.4;
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
  background: #fff;
  border: 1px solid #E5E5E5;
  border-radius: 14px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1), 0 2px 8px rgba(0, 0, 0, 0.04);
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
  color: #888;
  background: #FAFAFA;
  border-bottom: 1px solid #F0F0F0;
  border-radius: 24px 24px 0 0;
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
  border-radius: 10px;
  cursor: pointer;
  transition: background 0.15s;
}

.mode-item:hover {
  background: #F8F7FF;
}

.mode-item-active {
  background: #F5F3FF;
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
  color: #1a1a1a;
}

.mode-tag {
  font-size: 10px;
  font-weight: 600;
  color: #fff;
  background: linear-gradient(135deg, #34d399, #10b981);
  padding: 1px 6px;
  border-radius: 8px;
  letter-spacing: 0.3px;
}

.mode-item-desc {
  font-size: 12px;
  color: #999;
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
  color: #444;
  border-radius: 10px;
  cursor: pointer;
  transition: background 0.15s;
}

.dropdown-item:hover {
  background: #F5F3FF;
}

.dropdown-item-active {
  color: #7C3AED;
  background: #F5F3FF;
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
  color: #1a1a1a;
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
  color: #666;
}

.toggle-switch {
  width: 40px;
  height: 22px;
  border-radius: 11px;
  background: #ddd;
  position: relative;
  transition: background 0.2s;
}

.toggle-switch.toggle-on {
  background: #7C3AED;
}

.toggle-dot {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #fff;
  position: absolute;
  top: 2px;
  left: 2px;
  transition: left 0.2s;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.15);
}

.toggle-on .toggle-dot {
  left: 20px;
}

/* ─── Model tabs ─── */
.model-tabs {
  display: flex;
  gap: 0;
  padding: 0 16px;
  border-bottom: 1px solid #f0f0f0;
}

.model-tab {
  padding: 8px 16px;
  font-size: 13px;
  color: #888;
  border-bottom: 2px solid transparent;
  cursor: pointer;
  transition: all 0.15s;
  background: none;
  border-top: none;
  border-left: none;
  border-right: none;
}

.model-tab:hover {
  color: #333;
}

.model-tab-active {
  color: #1a1a1a;
  font-weight: 600;
  border-bottom-color: #1a1a1a;
}

.model-section-label {
  font-size: 11px;
  color: #aaa;
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
  border-radius: 8px;
  margin: 2px 6px;
}

.model-item:hover {
  background: #F5F5F5;
}

.model-item-active {
  background: #F3F0FF !important;
}

.model-item:last-child {
  border-radius: 8px;
}

.model-icon {
  color: #666;
  margin-top: 2px;
  flex-shrink: 0;
}

.model-name {
  font-size: 13px;
  font-weight: 500;
  color: #1a1a1a;
  line-height: 1.3;
}

.model-tag {
  display: inline-flex;
  align-items: center;
  padding: 1px 6px;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 500;
  background: #F5F5F5;
  color: #888;
  white-space: nowrap;
}

.model-tag-rec {
  background: #F3F0FF;
  color: #7C3AED;
}

.model-tag-premium {
  font-size: 10px;
  padding: 1px 5px;
  border-radius: 3px;
  background: linear-gradient(135deg, #F59E0B, #D97706);
  color: #fff;
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
  color: #999;
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
  border: 1px solid #E5E5E5;
  border-radius: 10px;
  background: #FAFAFA;
}

.preset-search-input {
  flex: 1;
  border: none;
  outline: none;
  background: transparent;
  font-size: 13px;
  color: #333;
}

.preset-search-input::placeholder {
  color: #bbb;
}

.preset-new-btn {
  height: 36px;
  padding: 0 16px;
  border-radius: 10px;
  background: #1a1a1a;
  color: #fff;
  font-size: 13px;
  font-weight: 500;
  border: none;
  cursor: pointer;
  white-space: nowrap;
  transition: background 0.15s;
}

.preset-new-btn:hover {
  background: #333;
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
  color: #aaa;
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
  background: #f3f0ff;
  color: #1a1a1a;
  font-size: 15px;
  line-height: 1.7;
  padding: 12px 18px;
  border-radius: 18px 18px 4px 18px;
  max-width: 70%;
  word-break: break-word;
}

.chat-time {
  font-size: 12px;
  color: #bbb;
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
  color: #1a1a1a;
  max-width: 90%;
  word-break: break-word;
}

/* Streaming cursor */
.streaming-cursor {
  display: inline-block;
  color: #7c3aed;
  font-weight: 400;
  animation: cursorBlink 0.8s infinite;
}

@keyframes cursorBlink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

/* ─── Bottom Chat Input Bar ─── */
.chat-input-bar {
  flex-shrink: 0;
  padding: 12px 0 20px;
  background: #fff;
  border-top: 1px solid #f5f5f5;
}

.chat-input-card {
  background: #fff;
  border: 1px solid #e5e5e5;
  border-radius: 20px;
  padding: 14px 16px 10px;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.chat-input-card:focus-within {
  border-color: #c4b5fd;
  box-shadow: 0 0 0 3px rgba(124, 58, 237, 0.06);
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
  color: #333;
  background: transparent;
}

.chat-input-textarea::placeholder {
  color: #bbb;
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
  border-radius: 10px;
  border: 1px solid #e8e8e8;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #888;
  background: #fff;
  cursor: pointer;
  transition: all 0.15s;
}

.chat-tool-btn:hover {
  background: #f5f5f5;
  color: #555;
}

.chat-mode-btn {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 0 12px;
  height: 34px;
  border-radius: 10px;
  border: 1px solid #e8e8e8;
  font-size: 13px;
  color: #666;
  background: #fff;
  cursor: pointer;
  transition: all 0.15s;
}

.chat-mode-btn:hover {
  background: #f5f5f5;
}

.chat-send-btn {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #e5e5e5;
  color: #999;
  cursor: not-allowed;
  transition: all 0.2s;
}

.chat-send-active {
  background: #0a0a0a;
  color: #fff;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.12);
}

.chat-send-active:hover {
  background: #1a1a1a;
}

.chat-stop-btn {
  background: #0a0a0a !important;
  color: #fff !important;
  cursor: pointer !important;
}

.chat-stop-btn:hover {
  background: #333 !important;
}

/* ─── Sidebar Conversation Items ─── */
.sidebar-conv-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 10px;
  cursor: pointer;
  transition: background 0.15s;
}

.sidebar-conv-item:hover {
  background: #f5f5f5;
}

.sidebar-conv-active {
  background: #f3f0ff !important;
}

.sidebar-conv-icon {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: #f3f0ff;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #7c3aed;
  flex-shrink: 0;
}

.sidebar-conv-active .sidebar-conv-icon {
  background: #ede9fe;
}

/* ─── Top Bar ─── */
.topbar {
  height: 56px;
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

/* Credits + Subscribe purple group */
.topbar-credits-group {
  display: flex;
  align-items: center;
  gap: 6px;
  height: 36px;
  padding: 0 14px;
  border-radius: 20px;
  background: #f3f0ff;
  cursor: pointer;
  transition: all 0.15s;
}

.topbar-credits-group:hover {
  background: #ede9fe;
}

.topbar-credits-icon {
  color: #7c3aed;
  font-size: 15px;
}

.topbar-credits-num {
  font-weight: 600;
  font-size: 14px;
  color: #7c3aed;
}

.topbar-credits-group svg {
  color: #7c3aed;
  opacity: 0.6;
}

.topbar-group-divider {
  width: 1px;
  height: 16px;
  background: #d8ccf5;
  margin: 0 4px;
}

.topbar-subscribe {
  font-size: 13px;
  font-weight: 600;
  color: #7c3aed;
}

/* Icon buttons — black */
.topbar-icon-btn {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #1a1a1a;
  background: none;
  border: none;
  cursor: pointer;
  transition: all 0.15s;
}

.topbar-icon-btn:hover {
  background: #f5f5f5;
  color: #000;
}

/* Avatar */
.topbar-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #1a1a1a;
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
  background: #333;
}

/* ─── Subscription Plans (reference style) ─── */
.plan-logo {
  width: 48px;
  height: 48px;
  border-radius: 14px;
  background: #1a1a1a;
  color: #fff;
  font-size: 22px;
  font-weight: 700;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 16px;
}

.plan-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}

.plan-card {
  border: 1px solid #e5e5e5;
  border-radius: 16px;
  padding: 28px 24px;
}

.plan-card-featured {
  border: 2px solid #7c3aed;
}

.plan-card-title {
  font-size: 16px;
  font-weight: 700;
  color: #1a1a1a;
  margin: 0 0 12px;
}

.plan-card-header {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 16px;
  font-weight: 700;
  color: #1a1a1a;
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
  color: #1a1a1a;
}

.plan-price-big {
  font-size: 36px;
  font-weight: 800;
  color: #1a1a1a;
  letter-spacing: -1px;
}

.plan-price-unit {
  font-size: 14px;
  color: #999;
  margin-left: 2px;
}

.plan-discount-tag {
  font-size: 11px;
  font-weight: 600;
  color: #ef4444;
  border: 1px solid #fca5a5;
  border-radius: 4px;
  padding: 1px 6px;
  margin-left: 8px;
  white-space: nowrap;
}

.plan-price-note {
  font-size: 12px;
  color: #999;
  margin-bottom: 16px;
  line-height: 1.5;
}

.plan-action-btn {
  width: 100%;
  height: 44px;
  border-radius: 10px;
  border: none;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s;
  margin-bottom: 20px;
}

.plan-action-disabled {
  background: #f5f5f5;
  color: #bbb;
  cursor: default;
}

.plan-action-primary {
  background: #7c3aed;
  color: #fff;
}

.plan-action-primary:hover {
  background: #6d28d9;
}

.plan-action-dark {
  background: #1a1a1a;
  color: #fff;
}

.plan-action-dark:hover {
  background: #333;
}

.plan-section-label {
  font-size: 14px;
  font-weight: 700;
  color: #1a1a1a;
  margin-bottom: 10px;
}

.plan-list {
  list-style: none;
  padding: 0;
  margin: 0 0 18px;
  font-size: 13px;
  color: #444;
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
  color: #22c55e;
  font-weight: 600;
}

.plan-cross::before {
  content: '✗';
  position: absolute;
  left: 0;
  color: #ef4444;
  font-weight: 600;
}

.plan-sub {
  font-size: 12px;
  color: #999;
}

/* ─── Feedback ─── */
.feedback-types {
  display: flex;
  gap: 8px;
  margin-bottom: 14px;
}

.feedback-type-btn {
  padding: 6px 16px;
  border-radius: 20px;
  border: 1px solid #e5e5e5;
  background: #fff;
  font-size: 13px;
  color: #555;
  cursor: pointer;
  transition: all 0.15s;
}

.feedback-type-btn:hover {
  border-color: #ccc;
}

.feedback-type-active {
  background: #f3f0ff;
  border-color: #c4b5fd;
  color: #7c3aed;
}

.feedback-textarea {
  width: 100%;
  border: 1px solid #e5e5e5;
  border-radius: 12px;
  padding: 12px 14px;
  font-size: 14px;
  color: #333;
  resize: none;
  outline: none;
  line-height: 1.6;
  box-sizing: border-box;
}

.feedback-textarea:focus {
  border-color: #c4b5fd;
  box-shadow: 0 0 0 3px rgba(124, 58, 237, 0.06);
}

.feedback-submit {
  width: 100%;
  height: 44px;
  border-radius: 12px;
  border: none;
  background: #1a1a1a;
  color: #fff;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  margin-top: 14px;
  transition: all 0.15s;
}

.feedback-submit:hover:not(:disabled) {
  background: #333;
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
  color: #333;
  margin: 0 0 6px;
}

.empty-sheet span {
  font-size: 13px;
  color: #999;
}
</style>
