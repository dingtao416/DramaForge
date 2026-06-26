<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserAIConfigStore } from '@/stores/user-ai-config'
import { discoverModelsFromUrl } from '@/api/user-ai-config'
import type { MediaCapability, ModelConfig, ProviderConfig, VideoModelPreset } from '@/types/user-ai-config'

const router = useRouter()
const aiStore = useUserAIConfigStore()

const capabilities: MediaCapability[] = ['chat', 'image', 'video']
const capabilityLabels: Record<MediaCapability, string> = {
  chat: '文本模型',
  image: '图片模型',
  video: '视频模型',
}

const providerTypes = [
  'openai_compatible',
  'openai_native',
  'replicate',
  'fal',
  'runway',
  'luma',
  'volcengine_ark',
  'dashscope',
  'google_vertex',
]

const providerLabels: Record<string, string> = {
  openai_compatible: 'OpenAI Compatible',
  openai_native: 'OpenAI Native',
  replicate: 'Replicate',
  fal: 'fal.ai',
  runway: 'Runway',
  luma: 'Luma',
  volcengine_ark: 'Volcengine Ark',
  dashscope: 'DashScope',
  google_vertex: 'Google Vertex',
}

const activeCapability = ref<MediaCapability>('image')
const showProviderForm = ref(false)
const editingProvider = ref<ProviderConfig | null>(null)
const testResult = ref<{ success: boolean; message: string } | null>(null)
const saving = ref(false)
const testing = ref(false)
const toast = ref<{ show: boolean; msg: string; type: 'ok' | 'err' }>({ show: false, msg: '', type: 'ok' })
const videoPresetIdKey = 'video_preset_id'
let videoModelRowSeq = 0

const fetchedModels = ref<string[]>([])
const fetchingModels = ref(false)
const fetchStatus = ref<'idle' | 'ok' | 'err'>('idle')
const fetchStatusMsg = ref('')
const selectedModels = ref<Set<string>>(new Set())
const modelSearch = ref('')
const dropdownOpen = ref(false)
const showManualTextarea = ref(false)
const modelDropdownRef = ref<HTMLElement | null>(null)
const modelSearchRef = ref<HTMLInputElement | null>(null)

const filteredFetchedModels = computed(() => {
  if (!modelSearch.value.trim()) return fetchedModels.value
  const q = modelSearch.value.trim().toLowerCase()
  return fetchedModels.value.filter((m) => m.toLowerCase().includes(q))
})

function toggleDropdown() {
  dropdownOpen.value = !dropdownOpen.value
  if (dropdownOpen.value) {
    nextTick(() => modelSearchRef.value?.focus())
  }
}

function closeDropdown() {
  dropdownOpen.value = false
}

function onDropdownKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape') closeDropdown()
}

function onClickOutside(e: MouseEvent) {
  if (modelDropdownRef.value && !modelDropdownRef.value.contains(e.target as Node)) {
    closeDropdown()
  }
}

interface VideoModelRow {
  key: number
  existing_id?: number
  model_id: string
  display_name: string
  preset_id: string
  show_video_advanced: boolean
  default_params_json: Record<string, any>
  video_size: boolean
  video_supported_sizes: string
  video_size_param: string
  video_duration: boolean
  video_supported_durations: string
  video_duration_param: string
  video_aspect_ratio: boolean
  video_aspect_ratio_param: string
  video_first_frame: boolean
  video_multi_reference: boolean
  video_max_reference_images: number
  video_role_character: boolean
  video_role_scene: boolean
  video_role_style: boolean
}

const providerForm = ref({
  name: '',
  provider_type: 'openai_compatible',
  auth_type: 'bearer',
  base_url: '',
  api_key: '',
  priority: 0,
  enabled: true,
  model_ids: '',
  video_models: [] as VideoModelRow[],
  show_video_advanced: false,
  video_size: false,
  video_supported_sizes: '',
  video_size_param: 'size',
  video_duration: false,
  video_supported_durations: '',
  video_duration_param: 'seconds',
  video_aspect_ratio: false,
  video_aspect_ratio_param: 'aspect_ratio',
  video_first_frame: false,
  video_multi_reference: false,
  video_max_reference_images: 3,
  video_role_character: false,
  video_role_scene: false,
  video_role_style: false,
})

const filteredProviders = computed(() =>
  aiStore.providers
    .map((provider) => ({
      provider,
      models: modelsForCapability(provider, activeCapability.value),
    }))
    .filter((item) => item.models.length > 0)
)

onMounted(async () => {
  await Promise.all([aiStore.fetchProviders(), aiStore.fetchDefaults(), aiStore.fetchVideoModelPresets()])
  document.addEventListener('mousedown', onClickOutside)
  document.addEventListener('keydown', onDropdownKeydown)
})

onUnmounted(() => {
  document.removeEventListener('mousedown', onClickOutside)
  document.removeEventListener('keydown', onDropdownKeydown)
})

function showToast(msg: string, type: 'ok' | 'err' = 'ok') {
  toast.value = { show: true, msg, type }
  window.setTimeout(() => (toast.value.show = false), 2500)
}

function modelsForCapability(provider: ProviderConfig, capability: MediaCapability): ModelConfig[] {
  return provider.models.filter((model) => (model.capability || model.capability_type) === capability)
}

function modelNames(models: ModelConfig[]) {
  return models.map((model) => model.display_name || model.model_id).join('、')
}

function normalizedModels() {
  return providerForm.value.model_ids
    .split(/[\n,，]/)
    .map((item) => item.trim())
    .filter(Boolean)
}

async function fetchModelsFromProvider() {
  if (!providerForm.value.base_url.trim()) return showToast('请先填写接口地址', 'err')
  if (!providerForm.value.api_key.trim()) return showToast('请先填写 API Key', 'err')
  fetchingModels.value = true
  fetchStatus.value = 'idle'
  fetchStatusMsg.value = ''
  dropdownOpen.value = false
  fetchedModels.value = []
  selectedModels.value = new Set()
  providerForm.value.model_ids = ''
  try {
    const result = await discoverModelsFromUrl({
      provider_type: providerForm.value.provider_type,
      auth_type: providerForm.value.auth_type,
      base_url: providerForm.value.base_url.trim(),
      api_key: providerForm.value.api_key.trim(),
    })
    fetchedModels.value = result.models || []
    if (fetchedModels.value.length === 0) {
      fetchStatus.value = 'err'
      fetchStatusMsg.value = '未获取到模型列表'
    } else {
      fetchStatus.value = 'ok'
      fetchStatusMsg.value = `发现 ${fetchedModels.value.length} 个模型`
      dropdownOpen.value = true
      nextTick(() => modelSearchRef.value?.focus())
    }
  } catch (e: any) {
    fetchStatus.value = 'err'
    fetchStatusMsg.value = e.response?.data?.detail || e.message || '获取失败，请检查地址和密钥'
  } finally {
    fetchingModels.value = false
  }
}

function toggleModelSelection(modelId: string) {
  const s = new Set(selectedModels.value)
  if (s.has(modelId)) {
    s.delete(modelId)
  } else {
    s.add(modelId)
  }
  selectedModels.value = s
  syncSelectedToTextarea()
}

function syncSelectedToTextarea() {
  const manual = providerForm.value.model_ids
    .split(/[\n,，]/)
    .map((item) => item.trim())
    .filter(Boolean)
  const fetchedSet = new Set(fetchedModels.value)
  const manualOnly = manual.filter((m) => !fetchedSet.has(m))
  const result = [...selectedModels.value, ...manualOnly]
  providerForm.value.model_ids = result.join('\n')
}

function onManualModelInput() {
  if (fetchedModels.value.length === 0) return
  const current = normalizedModels()
  const s = new Set<string>()
  for (const m of current) {
    if (fetchedModels.value.includes(m)) s.add(m)
  }
  selectedModels.value = s
}

function selectAllModels() {
  const s = new Set(selectedModels.value)
  for (const m of filteredFetchedModels.value) {
    s.add(m)
  }
  selectedModels.value = s
  syncSelectedToTextarea()
}

function deselectAllModels() {
  const s = new Set(selectedModels.value)
  for (const m of filteredFetchedModels.value) {
    s.delete(m)
  }
  selectedModels.value = s
  syncSelectedToTextarea()
}

function removeModelFromSelection(modelId: string) {
  const s = new Set(selectedModels.value)
  s.delete(modelId)
  selectedModels.value = s
  syncSelectedToTextarea()
}

function textList(value: unknown) {
  if (Array.isArray(value)) return value.map(item => String(item)).join('\n')
  if (typeof value === 'string') return value
  return ''
}

function normalizedList(value: string) {
  return value
    .split(/[\n,，]/)
    .map((item) => item.trim())
    .filter(Boolean)
}

function capabilityFields(caps: Record<string, any> | undefined) {
  const value = caps || {}
  return {
    video_size: Boolean(value.video_size || value.video_supported_sizes),
    video_supported_sizes: textList(value.video_supported_sizes),
    video_size_param: String(value.video_size_param || 'size'),
    video_duration: Boolean(value.video_duration || value.video_supported_durations),
    video_supported_durations: textList(value.video_supported_durations),
    video_duration_param: String(value.video_duration_param || 'seconds'),
    video_aspect_ratio: Boolean(value.video_aspect_ratio),
    video_aspect_ratio_param: String(value.video_aspect_ratio_param || 'aspect_ratio'),
    video_first_frame: Boolean(value.video_first_frame),
    video_multi_reference: Boolean(value.video_multi_reference || value.video_reference_images),
    video_max_reference_images: Number(value.video_max_reference_images || 3),
    video_role_character: Array.isArray(value.video_reference_roles) ? value.video_reference_roles.includes('character') : false,
    video_role_scene: Array.isArray(value.video_reference_roles) ? value.video_reference_roles.includes('scene') : false,
    video_role_style: Array.isArray(value.video_reference_roles) ? value.video_reference_roles.includes('style') : false,
  }
}

function blankVideoModelRow(modelId = '', preset?: VideoModelPreset | null): VideoModelRow {
  const caps = capabilityFields(preset?.capabilities_json || {})
  return {
    key: ++videoModelRowSeq,
    model_id: modelId || preset?.default_model_id || '',
    display_name: preset?.display_name || modelId || '',
    preset_id: preset?.preset_id || '',
    show_video_advanced: false,
    default_params_json: { ...(preset?.default_params_json || {}) },
    ...caps,
  }
}

function videoModelRowFromModel(model: ModelConfig): VideoModelRow {
  const presetId = String(model.preset_id || model.param_schema_json?.[videoPresetIdKey] || '')
  return {
    ...blankVideoModelRow(model.model_id),
    existing_id: model.id,
    model_id: model.model_id,
    display_name: model.display_name || model.model_id,
    preset_id: presetId,
    default_params_json: { ...(model.effective_default_params_json || model.default_params_json || {}) },
    ...capabilityFields(model.effective_capabilities_json || model.capabilities_json || {}),
  }
}

function findVideoPreset(presetId: string) {
  return aiStore.videoModelPresets.find((preset) => preset.preset_id === presetId) || null
}

function applyVideoPreset(row: VideoModelRow) {
  const preset = findVideoPreset(row.preset_id)
  if (!preset) return
  row.model_id = preset.default_model_id || preset.model_ids[0] || row.model_id
  row.display_name = preset.display_name
  row.default_params_json = { ...preset.default_params_json }
  Object.assign(row, capabilityFields(preset.capabilities_json))
}

function addVideoModelRow() {
  providerForm.value.video_models.push(blankVideoModelRow())
}

function removeVideoModelRow(rowKey: number) {
  providerForm.value.video_models = providerForm.value.video_models.filter((row) => row.key !== rowKey)
  if (providerForm.value.video_models.length === 0) {
    providerForm.value.video_models.push(blankVideoModelRow())
  }
}

function videoCapabilitySummary(row: VideoModelRow) {
  const parts = []
  if (row.video_size || normalizedList(row.video_supported_sizes).length) parts.push('尺寸')
  if (row.video_duration || normalizedList(row.video_supported_durations).length) parts.push('时长')
  if (row.video_aspect_ratio) parts.push('比例')
  if (row.video_first_frame) parts.push('首帧')
  if (row.video_multi_reference) parts.push('多参考图')
  return parts.length ? parts.join('、') : '基础 prompt 生成'
}

function openAddProvider() {
  editingProvider.value = null
  testResult.value = null
  fetchedModels.value = []
  selectedModels.value = new Set()
  modelSearch.value = ''
  fetchStatus.value = 'idle'
  fetchStatusMsg.value = ''
  dropdownOpen.value = false
  showManualTextarea.value = false
  providerForm.value = {
    name: '',
    provider_type: 'openai_compatible',
    auth_type: 'bearer',
    base_url: '',
    api_key: '',
    priority: 0,
    enabled: true,
    model_ids: '',
    video_models: [blankVideoModelRow()],
    show_video_advanced: false,
    video_size: false,
    video_supported_sizes: '',
    video_size_param: 'size',
    video_duration: false,
    video_supported_durations: '',
    video_duration_param: 'seconds',
    video_aspect_ratio: false,
    video_aspect_ratio_param: 'aspect_ratio',
    video_first_frame: false,
    video_multi_reference: false,
    video_max_reference_images: 3,
    video_role_character: false,
    video_role_scene: false,
    video_role_style: false,
  }
  showProviderForm.value = true
}

function openEditProvider(provider: ProviderConfig) {
  const firstModel = modelsForCapability(provider, activeCapability.value)[0]
  const caps = firstModel?.capabilities_json || {}
  const videoModels = modelsForCapability(provider, 'video').map(videoModelRowFromModel)
  editingProvider.value = provider
  testResult.value = null
  fetchedModels.value = []
  fetchStatus.value = 'idle'
  fetchStatusMsg.value = ''
  dropdownOpen.value = false
  showManualTextarea.value = false
  const existingModelIds = modelsForCapability(provider, activeCapability.value).map((model) => model.model_id)
  selectedModels.value = new Set(existingModelIds)
  providerForm.value = {
    name: provider.name,
    provider_type: provider.provider_type,
    auth_type: provider.auth_type,
    base_url: provider.base_url,
    api_key: '',
    priority: provider.priority,
    enabled: provider.enabled,
    model_ids: modelsForCapability(provider, activeCapability.value).map((model) => model.model_id).join('\n'),
    video_models: videoModels.length ? videoModels : [blankVideoModelRow()],
    show_video_advanced: false,
    video_size: Boolean(caps.video_size || caps.video_supported_sizes),
    video_supported_sizes: textList(caps.video_supported_sizes),
    video_size_param: String(caps.video_size_param || 'size'),
    video_duration: Boolean(caps.video_duration || caps.video_supported_durations),
    video_supported_durations: textList(caps.video_supported_durations),
    video_duration_param: String(caps.video_duration_param || 'seconds'),
    video_aspect_ratio: Boolean(caps.video_aspect_ratio),
    video_aspect_ratio_param: String(caps.video_aspect_ratio_param || 'aspect_ratio'),
    video_first_frame: Boolean(caps.video_first_frame),
    video_multi_reference: Boolean(caps.video_multi_reference || caps.video_reference_images),
    video_max_reference_images: Number(caps.video_max_reference_images || 3),
    video_role_character: Array.isArray(caps.video_reference_roles) ? caps.video_reference_roles.includes('character') : false,
    video_role_scene: Array.isArray(caps.video_reference_roles) ? caps.video_reference_roles.includes('scene') : false,
    video_role_style: Array.isArray(caps.video_reference_roles) ? caps.video_reference_roles.includes('style') : false,
  }
  showProviderForm.value = true
}

function videoCapabilities(row: VideoModelRow) {
  const roles = [
    row.video_role_character ? 'character' : '',
    row.video_role_scene ? 'scene' : '',
    row.video_role_style ? 'style' : '',
  ].filter(Boolean)
  const supportedSizes = normalizedList(row.video_supported_sizes)
  const supportedDurations = normalizedList(row.video_supported_durations)
  const supportsReference = row.video_first_frame || row.video_multi_reference
  const capabilities: Record<string, any> = {}
  if (row.video_size || supportedSizes.length) {
    capabilities.video_size = true
    capabilities.video_supported_sizes = supportedSizes
    capabilities.video_size_param = row.video_size_param.trim() || 'size'
  }
  if (row.video_duration || supportedDurations.length) {
    capabilities.video_duration = true
    capabilities.video_supported_durations = supportedDurations
    capabilities.video_duration_param = row.video_duration_param.trim() || 'seconds'
  }
  if (row.video_aspect_ratio) {
    capabilities.video_aspect_ratio = true
    capabilities.video_aspect_ratio_param = row.video_aspect_ratio_param.trim() || 'aspect_ratio'
  }
  if (supportsReference) {
    capabilities.video_reference_images = row.video_multi_reference
    capabilities.video_first_frame = row.video_first_frame
    capabilities.video_multi_reference = row.video_multi_reference
    capabilities.video_max_reference_images = Number(row.video_max_reference_images) || 1
    capabilities.video_reference_roles = roles.length ? roles : ['character', 'scene']
  }
  return capabilities
}

async function saveProvider() {
  const videoRows = providerForm.value.video_models
    .map((row) => ({ ...row, model_id: row.model_id.trim() }))
    .filter((row) => row.model_id)
  const modelIds = activeCapability.value === 'video' ? videoRows.map((row) => row.model_id) : normalizedModels()
  if (!providerForm.value.name.trim()) return showToast('请填写配置名称', 'err')
  if (!providerForm.value.base_url.trim()) return showToast('请填写接口地址', 'err')
  if (!editingProvider.value && !providerForm.value.api_key.trim()) return showToast('请填写 API Key', 'err')
  if (modelIds.length === 0) return showToast('请至少填写一个支持的模型', 'err')

  saving.value = true
  try {
    const payload: any = {
      name: providerForm.value.name.trim(),
      provider_type: providerForm.value.provider_type,
      auth_type: providerForm.value.auth_type,
      base_url: providerForm.value.base_url.trim(),
      priority: Number(providerForm.value.priority) || 0,
      enabled: providerForm.value.enabled,
      headers_json: {},
      config_json: {},
    }
    if (!editingProvider.value || providerForm.value.api_key) payload.api_key = providerForm.value.api_key

    const provider = editingProvider.value
      ? await aiStore.updateProvider(editingProvider.value.id, payload)
      : await aiStore.addProvider(payload)

    if (activeCapability.value === 'video') {
      const existingModels = modelsForCapability(provider, 'video')
      const keptIds = new Set<number>()
      for (const row of videoRows) {
        const existingModel = row.existing_id
          ? existingModels.find((model) => model.id === row.existing_id)
          : existingModels.find((model) => model.model_id === row.model_id)
        const payload = {
          capability: 'video' as MediaCapability,
          model_id: row.model_id,
          display_name: row.display_name.trim() || row.model_id,
          is_default: existingModel?.is_default ?? (videoRows.length === 1 && !aiStore.defaults.video),
          default_params_json: row.default_params_json || {},
          capabilities_json: videoCapabilities(row),
          param_schema_json: row.preset_id ? { [videoPresetIdKey]: row.preset_id } : {},
        }
        const savedModel = existingModel
          ? await aiStore.updateModel(existingModel.id, payload)
          : await aiStore.addModel(provider.id, payload)
        keptIds.add(savedModel.id)
      }
      for (const model of existingModels) {
        if (!keptIds.has(model.id)) {
          await aiStore.removeModel(model.id)
        }
      }
    } else {
      // 先删除该能力下所有旧模型
      const existingModels = modelsForCapability(editingProvider.value || provider, activeCapability.value)
      for (const model of existingModels) {
        await aiStore.removeModel(model.id)
      }
      // 再重新添加选中的模型
      for (const modelId of modelIds) {
        await aiStore.addModel(provider.id, {
          capability: activeCapability.value,
          model_id: modelId,
          display_name: modelId,
          is_default: modelIds.length === 1 && !aiStore.defaults[activeCapability.value],
          default_params_json: {},
          capabilities_json: {},
          param_schema_json: {},
        })
      }
    }

    showProviderForm.value = false
    await Promise.all([aiStore.fetchProviders(), aiStore.fetchDefaults()])
    showToast(editingProvider.value ? '配置已更新' : '配置已创建')
  } catch (e: any) {
    showToast(e.message || '保存失败', 'err')
  } finally {
    saving.value = false
  }
}

async function testProvider() {
  if (!editingProvider.value) {
    showToast('请先创建配置后再测试连通性', 'err')
    return
  }
  testing.value = true
  testResult.value = null
  try {
    testResult.value = await aiStore.testKey(editingProvider.value.id)
  } finally {
    testing.value = false
  }
}

async function deleteProvider(id: number) {
  await aiStore.removeProvider(id)
  await aiStore.fetchDefaults()
  showToast('配置已删除')
}

function increasePriority() {
  providerForm.value.priority = Number(providerForm.value.priority || 0) + 1
}

function decreasePriority() {
  providerForm.value.priority = Number(providerForm.value.priority || 0) - 1
}

</script>

<template>
  <div class="settings-page">
    <Transition name="fade">
      <div
        v-if="toast.show"
        class="settings-toast"
        :class="toast.type === 'ok' ? 'settings-toast-ok' : 'settings-toast-err'"
      >
        {{ toast.msg }}
      </div>
    </Transition>

    <main class="service-dialog" aria-label="AI 服务配置">
      <header class="service-header">
        <h1>AI 服务配置</h1>
        <div class="service-header-actions">
          <button class="service-close" aria-label="关闭" @click="router.push('/')">×</button>
        </div>
      </header>

      <div class="service-toolbar">
        <nav class="service-tabs" aria-label="模型类型">
          <button
            v-for="cap in capabilities"
            :key="cap"
            class="service-tab"
            :class="{ 'service-tab-active': activeCapability === cap }"
            @click="activeCapability = cap"
          >
            {{ capabilityLabels[cap] }}
          </button>
        </nav>

        <button class="service-primary" @click="openAddProvider">
          <span>+</span>
          添加配置
        </button>
      </div>

      <section class="service-table-wrap">
        <table class="service-table">
          <thead>
            <tr>
              <th>配置名称</th>
              <th>厂商</th>
              <th>模型列表</th>
              <th>优先级</th>
              <th>状态</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody v-if="aiStore.loading">
            <tr>
              <td colspan="6">
                <div class="service-empty">正在加载配置...</div>
              </td>
            </tr>
          </tbody>
          <tbody v-else-if="filteredProviders.length === 0">
            <tr>
              <td colspan="6">
                <div class="service-empty">暂无数据</div>
              </td>
            </tr>
          </tbody>
          <tbody v-else>
            <tr v-for="{ provider, models } in filteredProviders" :key="provider.id">
              <td>
                <div class="config-name">{{ provider.name }}</div>
                <div class="config-url">{{ provider.base_url || '未设置接口地址' }}</div>
              </td>
              <td>{{ providerLabels[provider.provider_type] || provider.provider_type }}</td>
              <td>
                <div class="model-list">{{ modelNames(models) }}</div>
              </td>
              <td>{{ provider.priority }}</td>
              <td>
                <span class="service-status" :class="provider.enabled ? 'service-status-on' : 'service-status-off'">
                  {{ provider.enabled ? '启用' : '停用' }}
                </span>
              </td>
              <td>
                <div class="service-actions">
                  <button @click="openEditProvider(provider)">编辑</button>
                  <button class="danger" @click="deleteProvider(provider.id)">删除</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </section>
    </main>

    <Teleport to="body">
      <Transition name="fade">
        <div v-if="showProviderForm" class="form-mask">
          <section class="config-dialog" aria-label="添加配置">
            <header class="config-header">
              <h2>{{ editingProvider ? '编辑配置' : '添加配置' }}</h2>
              <button class="service-close" aria-label="关闭" @click="showProviderForm = false">×</button>
            </header>

            <div class="config-body">
              <label class="form-row form-row-required">
                <span>配置名称</span>
                <input v-model="providerForm.name" placeholder="例如：GetGo-图片-1177" />
              </label>

              <label class="form-row form-row-required">
                <span>厂商提供商</span>
                <select v-model="providerForm.provider_type">
                  <option v-for="type in providerTypes" :key="type" :value="type">
                    {{ providerLabels[type] || type }}
                  </option>
                </select>
              </label>

              <div class="form-row">
                <span>优先级</span>
                <div class="priority-control">
                  <button type="button" @click="decreasePriority">−</button>
                  <input v-model.number="providerForm.priority" type="number" />
                  <button type="button" @click="increasePriority">+</button>
                </div>
              </div>

              <div v-if="activeCapability !== 'video'" class="form-row form-row-required">
                <span>
                  支持的模型
                  <span v-if="selectedModels.size > 0" class="model-badge">{{ selectedModels.size }}</span>
                </span>
                <div class="model-selector">
                  <div class="model-fetch-row">
                    <button
                      type="button"
                      class="fetch-models-btn"
                      :class="{ 'fetch-models-btn--loading': fetchingModels }"
                      :disabled="fetchingModels"
                      @click="fetchModelsFromProvider"
                    >
                      <svg v-if="!fetchingModels" class="fetch-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <polyline points="23 4 23 10 17 10" />
                        <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" />
                      </svg>
                      <svg v-else class="fetch-icon fetch-spinner" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <polyline points="23 4 23 10 17 10" />
                        <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" />
                      </svg>
                      {{ fetchingModels ? '获取中...' : (fetchStatus === 'idle' ? '获取模型列表' : '重新获取') }}
                    </button>
                    <Transition name="status-fade">
                      <span v-if="!fetchingModels && fetchStatus === 'ok'" class="fetch-status fetch-status--ok">
                        <svg class="status-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                          <polyline points="20 6 9 17 4 12" />
                        </svg>
                        {{ fetchStatusMsg }}
                      </span>
                    </Transition>
                    <Transition name="status-fade">
                      <span v-if="!fetchingModels && fetchStatus === 'err'" class="fetch-status fetch-status--err">
                        <svg class="status-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                          <circle cx="12" cy="12" r="10" />
                          <line x1="12" y1="8" x2="12" y2="12" />
                          <line x1="12" y1="16" x2="12.01" y2="16" />
                        </svg>
                        {{ fetchStatusMsg }}
                      </span>
                    </Transition>
                  </div>

                  <!-- 下拉选择器 -->
                  <div v-if="fetchedModels.length > 0" ref="modelDropdownRef" class="ms-dropdown" @click.stop>
                    <div class="ms-trigger" @click.stop="toggleDropdown">
                      <div v-if="selectedModels.size === 0" class="ms-placeholder">请选择模型</div>
                      <div v-else class="ms-chips">
                        <span
                          v-for="model in Array.from(selectedModels)"
                          :key="model"
                          class="ms-chip"
                          @click.stop="removeModelFromSelection(model)"
                        >
                          {{ model }}
                          <svg class="ms-chip-x" viewBox="0 0 12 12" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
                            <line x1="3" y1="3" x2="9" y2="9" /><line x1="9" y1="3" x2="3" y2="9" />
                          </svg>
                        </span>
                      </div>
                      <svg class="ms-arrow" :class="{ 'ms-arrow--open': dropdownOpen }" viewBox="0 0 12 8" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                        <polyline points="1 1 6 6 11 1" />
                      </svg>
                    </div>

                    <Transition name="dropdown-fade">
                      <div v-if="dropdownOpen" class="ms-panel">
                        <div class="ms-panel-search">
                          <svg class="ms-search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
                          </svg>
                          <input
                            ref="modelSearchRef"
                            v-model="modelSearch"
                            class="ms-search-input"
                            placeholder="搜索模型…"
                          />
                          <div class="ms-panel-actions">
                            <button type="button" class="ms-action-btn" @click.stop="selectAllModels">全选</button>
                            <button type="button" class="ms-action-btn" @click.stop="deselectAllModels">清除</button>
                          </div>
                        </div>
                        <div class="ms-list">
                          <div
                            v-for="model in filteredFetchedModels"
                            :key="model"
                            class="ms-option"
                            :class="{ 'ms-option--selected': selectedModels.has(model) }"
                            @click.stop="toggleModelSelection(model)"
                          >
                            <span class="ms-checkbox" :class="{ 'ms-checkbox--checked': selectedModels.has(model) }">
                              <svg v-if="selectedModels.has(model)" class="ms-check" viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                                <polyline points="2.5 7 5.5 10 11.5 4" />
                              </svg>
                            </span>
                            <span class="ms-option-label">{{ model }}</span>
                          </div>
                          <div v-if="filteredFetchedModels.length === 0" class="ms-empty">未找到匹配模型</div>
                        </div>
                        <div class="ms-footer">
                          <span class="ms-footer-info">已选 {{ selectedModels.size }} / {{ fetchedModels.length }}</span>
                          <button type="button" class="ms-footer-btn" @click.stop="showManualTextarea = !showManualTextarea">手动补充</button>
                        </div>
                      </div>
                    </Transition>
                  </div>

                  <Transition name="manual-slide">
                    <textarea
                      v-if="showManualTextarea || fetchedModels.length === 0"
                      v-model="providerForm.model_ids"
                      rows="2"
                      class="ms-manual-input"
                      :placeholder="fetchedModels.length > 0 ? '手动输入模型名，多个用换行或逗号分隔' : '请输入模型名，多个模型可用换行或逗号分隔'"
                      @input="onManualModelInput"
                    />
                  </Transition>
                </div>
              </div>

              <div v-if="activeCapability === 'video'" class="form-row video-capability-row">
                <span>视频模型</span>
                <div class="video-model-editor">
                  <article v-for="row in providerForm.video_models" :key="row.key" class="video-model-card">
                    <div class="video-model-main">
                      <input v-model="row.model_id" class="video-model-id" placeholder="模型 ID，例如 sora-2" />
                      <select v-model="row.preset_id" class="video-preset-select" @change="applyVideoPreset(row)">
                        <option value="">自定义 / 不使用预设</option>
                        <option v-for="preset in aiStore.videoModelPresets" :key="preset.preset_id" :value="preset.preset_id">
                          {{ preset.display_name }}
                        </option>
                      </select>
                      <button type="button" class="row-delete-button" @click="removeVideoModelRow(row.key)">删除</button>
                    </div>
                    <div class="video-capability-summary">
                      <span>{{ row.preset_id ? findVideoPreset(row.preset_id)?.display_name : '自定义模型' }}</span>
                      <strong>{{ videoCapabilitySummary(row) }}</strong>
                    </div>
                    <button
                      type="button"
                      class="advanced-toggle"
                      @click="row.show_video_advanced = !row.show_video_advanced"
                    >
                      {{ row.show_video_advanced ? '收起高级配置' : '展开高级配置' }}
                    </button>

                    <div v-if="row.show_video_advanced" class="video-advanced-grid">
                      <label class="switch-row">
                        <input v-model="row.video_size" type="checkbox" />
                        <span>支持尺寸参数</span>
                      </label>
                      <label class="inline-field">
                        <span>尺寸参数名</span>
                        <input v-model="row.video_size_param" />
                      </label>
                      <label class="stack-field">
                        <span>支持尺寸</span>
                        <textarea v-model="row.video_supported_sizes" rows="3" placeholder="720x1280&#10;1280x720" />
                      </label>

                      <label class="switch-row">
                        <input v-model="row.video_duration" type="checkbox" />
                        <span>支持时长参数</span>
                      </label>
                      <label class="inline-field">
                        <span>时长参数名</span>
                        <input v-model="row.video_duration_param" />
                      </label>
                      <label class="stack-field">
                        <span>支持时长</span>
                        <textarea v-model="row.video_supported_durations" rows="3" placeholder="4&#10;8&#10;12" />
                      </label>

                      <label class="switch-row">
                        <input v-model="row.video_aspect_ratio" type="checkbox" />
                        <span>支持比例参数</span>
                      </label>
                      <label class="inline-field">
                        <span>比例参数名</span>
                        <input v-model="row.video_aspect_ratio_param" />
                      </label>

                      <label class="switch-row">
                        <input v-model="row.video_first_frame" type="checkbox" />
                        <span>支持首帧图</span>
                      </label>
                      <label class="switch-row">
                        <input v-model="row.video_multi_reference" type="checkbox" />
                        <span>支持多参考图</span>
                      </label>
                      <label class="inline-field">
                        <span>最大参考图</span>
                        <input v-model.number="row.video_max_reference_images" type="number" min="1" max="8" />
                      </label>
                      <div class="role-checks">
                        <label><input v-model="row.video_role_character" type="checkbox" /> 角色</label>
                        <label><input v-model="row.video_role_scene" type="checkbox" /> 场景</label>
                        <label><input v-model="row.video_role_style" type="checkbox" /> 风格</label>
                      </div>
                    </div>
                  </article>
                  <button type="button" class="add-row-button" @click="addVideoModelRow">添加视频模型</button>
                  <small>选择预设可自动填充模型 ID 与已知能力；未知模型默认只传提示词。</small>
                </div>
              </div>

              <label class="form-row form-row-required">
                <span>接口地址</span>
                <input v-model="providerForm.base_url" placeholder="http://api.lingguoai.com/v1" />
                <small>包含域名和协议的完整基础路径。实际请求路径示例：/images/generations</small>
              </label>

              <label class="form-row form-row-required">
                <span>API Key</span>
                <input
                  v-model="providerForm.api_key"
                  type="password"
                  :placeholder="editingProvider ? '留空则不修改' : 'sk-...'"
                />
              </label>

              <label class="form-row">
                <span>状态</span>
                <label class="switch-row">
                  <input v-model="providerForm.enabled" type="checkbox" />
                  <span>{{ providerForm.enabled ? '启用' : '停用' }}</span>
                </label>
              </label>

              <div v-if="testResult" class="test-result" :class="testResult.success ? 'test-ok' : 'test-err'">
                {{ testResult.message }}
              </div>
            </div>

            <footer class="config-footer">
              <button class="test-button" :disabled="testing" @click="testProvider">
                {{ testing ? '测试中...' : '测试连通性' }}
              </button>
              <div class="footer-actions">
                <button class="secondary-button" @click="showProviderForm = false">取消</button>
                <button class="service-primary" :disabled="saving" @click="saveProvider">
                  {{ saving ? '保存中...' : editingProvider ? '保存' : '创建' }}
                </button>
              </div>
            </footer>
          </section>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<style scoped>
.settings-page {
  min-height: 100vh;
  padding: 22px 24px;
  background: rgba(0, 0, 0, 0.58);
  color: #1f2329;
}

.service-dialog {
  width: min(1000px, calc(100vw - 48px));
  min-height: 370px;
  margin: 0 auto;
  padding: 32px;
  border: 1px solid #e5e6eb;
  border-radius: 8px;
  background: #FDF5D6;
  box-shadow: 0 18px 50px rgba(0, 0, 0, 0.18);
}

.service-header,
.service-toolbar,
.config-header,
.config-footer,
.footer-actions,
.service-header-actions {
  display: flex;
  align-items: center;
}

.service-header,
.config-header {
  justify-content: space-between;
}

.service-header h1,
.config-header h2 {
  margin: 0;
  color: #111827;
  font-size: 18px;
  font-weight: 700;
}

.service-header-actions {
  gap: 14px;
}

.video-capability-row {
  align-items: flex-start;
}

.video-capability-box {
  display: grid;
  gap: 10px;
  padding: 12px;
  border: 1px solid #e5e6eb;
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.5);
}

.video-model-editor {
  display: grid;
  gap: 12px;
  min-width: 0;
}

.video-model-card {
  display: grid;
  gap: 10px;
  padding: 12px;
  border: 1px solid #e5e6eb;
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.58);
}

.video-model-main {
  display: grid;
  grid-template-columns: minmax(180px, 1fr) minmax(180px, 220px) 64px;
  gap: 8px;
  align-items: center;
}

.video-model-id,
.video-preset-select {
  min-width: 0;
  height: 32px;
  padding: 0 9px;
  border: 1px solid #d1d5db;
  border-radius: 5px;
  background: #fff;
  color: #111827;
  font-size: 13px;
}

.row-delete-button,
.add-row-button {
  height: 30px;
  border: 1px solid #d1d5db;
  border-radius: 5px;
  background: #fff;
  color: #374151;
  cursor: pointer;
  font-size: 12px;
}

.row-delete-button {
  color: #b42318;
}

.add-row-button {
  width: fit-content;
  padding: 0 10px;
}

.video-capability-summary {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  color: #6b7280;
  font-size: 12px;
}

.video-capability-summary strong {
  color: #1f2937;
  font-weight: 600;
}

.advanced-toggle {
  width: fit-content;
  height: 30px;
  padding: 0 10px;
  border: 1px solid #d1d5db;
  border-radius: 5px;
  background: #fff;
  color: #374151;
  cursor: pointer;
  font-size: 12px;
}

.video-advanced-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px 14px;
  padding-bottom: 10px;
  border-bottom: 1px solid #e5e7eb;
}

.inline-field,
.role-checks,
.stack-field {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #4b5563;
  font-size: 12px;
}

.stack-field {
  grid-column: 1 / -1;
  align-items: flex-start;
}

.inline-field input {
  width: 120px;
  height: 28px;
  padding: 0 8px;
  border: 1px solid #d1d5db;
  border-radius: 5px;
  background: #fff;
}

.stack-field textarea {
  flex: 1;
  min-width: 0;
  padding: 8px;
  border: 1px solid #d1d5db;
  border-radius: 5px;
  background: #fff;
  resize: vertical;
}

.role-checks label {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.service-text-button {
  border: 0;
  background: transparent;
  color: #6b7280;
  font-size: 13px;
  cursor: pointer;
}

.service-close {
  width: 30px;
  height: 30px;
  border: 0;
  border-radius: 6px;
  background: transparent;
  color: #4b5563;
  font-size: 22px;
  line-height: 1;
  cursor: pointer;
  transition: background 0.15s ease, color 0.15s ease;
}

.service-close:hover {
  background: #f3f4f6;
  color: #111827;
}

.service-toolbar {
  justify-content: space-between;
  gap: 20px;
  margin-top: 26px;
  border-bottom: 1px solid #e5e7eb;
}

.service-tabs {
  display: flex;
  gap: 4px;
}

.service-tab {
  min-width: 86px;
  height: 42px;
  border: 0;
  border-bottom: 3px solid transparent;
  background: transparent;
  color: #6b7280;
  font-size: 14px;
  cursor: pointer;
  transition: color 0.15s ease, border-color 0.15s ease;
}

.service-tab:hover,
.service-tab-active {
  color: #0b5cff;
}

.service-tab-active {
  border-bottom-color: #0b5cff;
  font-weight: 600;
}

.service-primary {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-width: 112px;
  height: 34px;
  padding: 0 16px;
  border: 0;
  border-radius: 4px;
  background: #0b5cff;
  color: #2D2515;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s ease, box-shadow 0.15s ease;
}

.service-primary:hover:not(:disabled) {
  background: #004ee6;
  box-shadow: 0 6px 16px rgba(11, 92, 255, 0.22);
}

.service-primary:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.service-table-wrap {
  margin-top: 16px;
  overflow-x: auto;
  border-bottom: 6px solid #D4C898;
}

.service-table {
  width: 100%;
  min-width: 920px;
  border-collapse: collapse;
  table-layout: fixed;
}

.service-table th {
  height: 46px;
  padding: 0 16px;
  color: #86909c;
  background: #FDF5D6;
  font-size: 13px;
  font-weight: 500;
  text-align: left;
}

.service-table th:nth-child(1) { width: 17%; }
.service-table th:nth-child(2) { width: 13%; }
.service-table th:nth-child(3) { width: 31%; }
.service-table th:nth-child(4) { width: 10%; }
.service-table th:nth-child(5) { width: 9%; }
.service-table th:nth-child(6) { width: 20%; }

.service-table td {
  height: 64px;
  padding: 12px 16px;
  border-top: 1px solid #FDF4D8;
  color: #374151;
  font-size: 13px;
  vertical-align: middle;
}

.service-table tbody tr {
  background: #FDF5D6;
  transition: background 0.15s ease;
}

.service-table tbody tr:hover {
  background: #fbfcff;
}

.service-empty {
  display: grid;
  place-items: center;
  height: 118px;
  background: #FDF4D8;
  color: #b0b4bb;
}

.config-name {
  color: #111827;
  font-weight: 600;
}

.config-url,
.model-list {
  overflow: hidden;
  color: #86909c;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.config-url {
  margin-top: 3px;
  font-size: 12px;
}

.service-status {
  display: inline-flex;
  align-items: center;
  height: 24px;
  padding: 0 8px;
  border-radius: 999px;
  font-size: 12px;
}

.service-status-on {
  background: #ecfdf3;
  color: #0f9f5f;
}

.service-status-off {
  background: #f3f4f6;
  color: #6b7280;
}

.service-actions {
  display: flex;
  gap: 10px;
}

.service-actions button {
  border: 0;
  background: transparent;
  color: #0b5cff;
  cursor: pointer;
}

.service-actions .danger {
  color: #d92d20;
}

.form-mask {
  position: fixed;
  inset: 0;
  z-index: 70;
  display: grid;
  place-items: center;
  padding: 24px;
  background: rgba(0, 0, 0, 0.62);
}

.config-dialog {
  width: min(650px, calc(100vw - 48px));
  max-height: min(760px, calc(100vh - 48px));
  overflow: auto;
  border: 1px solid #e5e6eb;
  border-radius: 8px;
  background: #FDF5D6;
  box-shadow: 0 18px 50px rgba(0, 0, 0, 0.22);
}

.config-header {
  padding: 24px 32px 16px;
}

.config-body {
  display: grid;
  gap: 18px;
  padding: 0 32px 16px;
}

.form-row {
  display: grid;
  grid-template-columns: 90px minmax(0, 1fr);
  column-gap: 14px;
  align-items: start;
}

.form-row > span {
  padding-top: 8px;
  color: #111827;
  font-size: 14px;
  text-align: right;
}

.form-row-required > span::before {
  content: '* ';
  color: #f04438;
}

.form-row input,
.form-row select,
.form-row textarea {
  width: 100%;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  background: #FDF5D6;
  color: #111827;
  font-size: 14px;
  outline: none;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

.form-row input,
.form-row select {
  height: 32px;
  padding: 0 10px;
}

.form-row textarea {
  min-height: 68px;
  padding: 8px 10px;
  resize: vertical;
}

.form-row input:focus,
.form-row select:focus,
.form-row textarea:focus {
  border-color: #0b5cff;
  box-shadow: 0 0 0 3px rgba(11, 92, 255, 0.08);
}

.form-row small {
  grid-column: 2;
  margin-top: 6px;
  color: #8b949e;
  font-size: 12px;
  line-height: 1.6;
}

.model-selector {
  display: grid;
  gap: 10px;
  --model-surface: #FEF9E7;
  --model-surface-strong: #FDF5D6;
  --model-border: #D4C898;
  --model-border-strong: #E8A317;
  --model-text: #2D2515;
  --model-muted: #6B5D40;
  --model-soft: #A89870;
  --model-accent: #E8A317;
  --model-accent-hover: #F5C34B;
  --model-accent-dark: #C88A0C;
}

.model-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  margin-left: 6px;
  border-radius: 9px;
  background: var(--model-accent);
  color: #fffaf0;
  font-size: 11px;
  font-weight: 600;
  vertical-align: middle;
}

/* === 获取按钮 === */
.model-fetch-row {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.fetch-models-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 36px;
  padding: 0 16px;
  border: 1.5px solid var(--model-border-strong);
  border-radius: 6px;
  background: rgba(232, 163, 23, 0.08);
  color: var(--model-accent-dark);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
  transition: background 0.2s ease, border-color 0.2s ease, color 0.2s ease, box-shadow 0.2s ease, transform 0.1s ease;
  user-select: none;
}

.fetch-models-btn:hover:not(:disabled) {
  background: var(--model-accent);
  border-color: var(--model-accent);
  color: #fffaf0;
  box-shadow: 0 4px 12px rgba(200, 138, 12, 0.22);
}

.fetch-models-btn:active:not(:disabled) {
  transform: scale(0.97);
  transition: transform 0.1s;
}

.fetch-models-btn--loading {
  opacity: 0.8;
  pointer-events: none;
}

.fetch-icon {
  width: 14px;
  height: 14px;
  flex-shrink: 0;
}

.fetch-spinner {
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* === 状态文字 === */
.fetch-status {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  font-weight: 500;
  white-space: nowrap;
}

.fetch-status--ok {
  color: #2f8f4e;
}

.fetch-status--err {
  color: #D94841;
}

.status-icon {
  width: 14px;
  height: 14px;
  flex-shrink: 0;
}

.status-fade-enter-active {
  transition: opacity 0.3s ease;
}

.status-fade-enter-from {
  opacity: 0;
}

/* === 下拉选择器 === */
.ms-dropdown {
  position: relative;
}

.ms-trigger {
  display: flex;
  align-items: center;
  min-height: 42px;
  padding: 6px 10px;
  border: 1.5px solid var(--model-border);
  border-radius: 6px;
  background: var(--model-surface-strong);
  cursor: pointer;
  transition: border-color 0.2s ease, box-shadow 0.2s ease, background 0.2s ease;
  overflow: hidden;
}

.ms-trigger:hover {
  border-color: var(--model-border-strong);
  background: #fff8df;
  box-shadow: 0 0 0 3px rgba(232, 163, 23, 0.1);
}

.ms-placeholder {
  flex: 1;
  color: var(--model-soft);
  font-size: 13px;
  user-select: none;
}

.ms-chips {
  display: flex;
  align-items: center;
  gap: 6px;
  flex: 1;
  min-width: 0;
  overflow-x: auto;
  overflow-y: hidden;
  scrollbar-width: none;
}

.ms-chips::-webkit-scrollbar {
  display: none;
}

.ms-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  height: 24px;
  padding: 0 7px 0 9px;
  border-radius: 6px;
  border: 1px solid rgba(232, 163, 23, 0.28);
  background: rgba(232, 163, 23, 0.12);
  color: var(--model-text);
  font-size: 11px;
  font-weight: 600;
  white-space: nowrap;
  flex-shrink: 0;
  cursor: pointer;
  transition: background 0.15s ease, border-color 0.15s ease, color 0.15s ease;
}

.ms-chip:hover {
  border-color: rgba(217, 72, 65, 0.38);
  background: rgba(217, 72, 65, 0.1);
  color: #B7352F;
}

.ms-chip-x {
  width: 10px;
  height: 10px;
  flex-shrink: 0;
  stroke-width: 2.5;
}

.ms-arrow {
  width: 12px;
  height: 8px;
  flex-shrink: 0;
  margin-left: 8px;
  color: var(--model-soft);
  transition: transform 0.25s ease;
}

.ms-arrow--open {
  transform: rotate(180deg);
}

/* === 下拉面板 === */
.ms-panel {
  position: absolute;
  top: calc(100% + 6px);
  left: 0;
  right: 0;
  z-index: 100;
  border: 1.5px solid var(--model-border);
  border-radius: 8px;
  background: var(--model-surface);
  box-shadow: 0 14px 30px rgba(45, 37, 21, 0.16);
  overflow: hidden;
}

.dropdown-fade-enter-active {
  transition: all 0.25s ease;
}

.dropdown-fade-leave-active {
  transition: all 0.15s ease-in;
}

.dropdown-fade-enter-from {
  opacity: 0;
  transform: translateY(-4px);
}

.dropdown-fade-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}

/* 搜索栏 */
.ms-panel-search {
  display: flex;
  align-items: center;
  gap: 8px;
  height: 40px;
  padding: 0 12px;
  background: var(--model-surface-strong);
  border-bottom: 1px solid var(--model-border);
}

.ms-search-icon {
  width: 14px;
  height: 14px;
  flex-shrink: 0;
  color: var(--model-soft);
}

.ms-search-input {
  flex: 1;
  height: 100%;
  border: none;
  background: transparent;
  font-size: 13px;
  color: var(--model-text);
  outline: none;
}

.ms-search-input::placeholder {
  color: var(--model-soft);
}

.ms-panel-actions {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

.ms-action-btn {
  height: 24px;
  padding: 0 8px;
  border: none;
  border-radius: 4px;
  background: transparent;
  color: var(--model-muted);
  font-size: 11px;
  cursor: pointer;
  transition: background 0.15s ease, color 0.15s ease;
  white-space: nowrap;
}

.ms-action-btn:hover {
  background: rgba(232, 163, 23, 0.12);
  color: var(--model-accent-dark);
}

/* 模型列表 */
.ms-list {
  max-height: 240px;
  overflow-y: auto;
  scrollbar-width: thin;
  scrollbar-color: var(--model-border) transparent;
}

.ms-list::-webkit-scrollbar {
  width: 5px;
}

.ms-list::-webkit-scrollbar-track {
  background: transparent;
}

.ms-list::-webkit-scrollbar-thumb {
  background: var(--model-border);
  border-radius: 10px;
}

.ms-option {
  display: flex;
  align-items: center;
  gap: 10px;
  min-height: 38px;
  padding: 0 12px;
  cursor: pointer;
  transition: background 0.15s ease;
  user-select: none;
}

.ms-option:hover {
  background: rgba(232, 163, 23, 0.08);
}

.ms-option--selected {
  background: rgba(232, 163, 23, 0.14);
}

.ms-option--selected .ms-option-label {
  font-weight: 600;
  color: var(--model-accent-dark);
}

.ms-checkbox {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  height: 18px;
  border-radius: 5px;
  border: 1.5px solid var(--model-border);
  background: #fffaf0;
  flex-shrink: 0;
  transition: background 0.15s ease, border-color 0.15s ease, box-shadow 0.15s ease, transform 0.15s ease;
}

.ms-checkbox--checked {
  background: var(--model-accent);
  border-color: var(--model-accent);
  box-shadow: 0 0 0 2px rgba(232, 163, 23, 0.18);
  animation: check-bounce 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

@keyframes check-bounce {
  0% { transform: scale(0.8); }
  50% { transform: scale(1.15); }
  100% { transform: scale(1); }
}

.ms-check {
  width: 12px;
  height: 12px;
  color: #fff;
}

.ms-option-label {
  font-size: 13px;
  color: var(--model-text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.ms-empty {
  padding: 20px;
  text-align: center;
  color: var(--model-soft);
  font-size: 13px;
}

/* 底部信息栏 */
.ms-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 36px;
  padding: 0 12px;
  background: var(--model-surface-strong);
  border-top: 1px solid var(--model-border);
}

.ms-footer-info {
  font-size: 12px;
  color: var(--model-soft);
}

.ms-footer-btn {
  height: 24px;
  padding: 0 8px;
  border: none;
  border-radius: 4px;
  background: transparent;
  color: var(--model-accent-dark);
  font-size: 12px;
  cursor: pointer;
  transition: background 0.15s ease, color 0.15s ease;
}

.ms-footer-btn:hover {
  background: rgba(232, 163, 23, 0.12);
  color: var(--model-text);
}

/* 手动输入框 */
.ms-manual-input {
  min-height: 56px;
  padding: 8px 10px;
  resize: vertical;
}

.manual-slide-enter-active {
  transition: all 0.2s ease;
}

.manual-slide-leave-active {
  transition: all 0.15s ease-in;
}

.manual-slide-enter-from,
.manual-slide-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}

.priority-control {
  display: grid;
  grid-template-columns: 32px minmax(0, 176px) 32px;
  gap: 4px;
}

.priority-control button {
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  background: #f7f8fa;
  color: #4b5563;
  font-size: 18px;
  cursor: pointer;
}

.priority-control input {
  text-align: center;
}

.switch-row {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  height: 32px;
  color: #4b5563;
  font-size: 13px;
}

.switch-row input {
  width: 16px;
  height: 16px;
  accent-color: #0b5cff;
}

.test-result {
  margin-left: 104px;
  border-radius: 4px;
  padding: 8px 10px;
  font-size: 13px;
}

.test-ok {
  background: #ecfdf3;
  color: #0f9f5f;
}

.test-err {
  background: #fff2f0;
  color: #d92d20;
}

.config-footer {
  justify-content: space-between;
  padding: 16px 32px 32px;
}

.test-button,
.secondary-button {
  height: 32px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  background: #FDF5D6;
  color: #111827;
  padding: 0 14px;
  font-size: 14px;
  cursor: pointer;
}

.secondary-button {
  background: #FDF4D8;
  border-color: #1A1508;
}

.footer-actions {
  gap: 8px;
}

.settings-toast {
  position: fixed;
  top: 18px;
  right: 18px;
  z-index: 90;
  border-radius: 6px;
  padding: 10px 12px;
  box-shadow: 0 12px 30px rgba(0, 0, 0, 0.16);
  font-size: 13px;
}

.settings-toast-ok {
  background: #111827;
  color: #FFFFFF;
}

.settings-toast-err {
  background: #fff2f0;
  color: #d92d20;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.18s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

@media (max-width: 720px) {
  .settings-page,
  .form-mask {
    padding: 12px;
  }

  .service-dialog,
  .config-dialog {
    width: calc(100vw - 24px);
  }

  .service-dialog {
    padding: 22px;
  }

  .service-toolbar {
    align-items: stretch;
    flex-direction: column;
    border-bottom: 0;
  }

  .service-tabs {
    border-bottom: 1px solid #e5e7eb;
  }

  .service-primary {
    align-self: flex-end;
  }

  .form-row {
    grid-template-columns: 1fr;
    row-gap: 6px;
  }

  .form-row > span {
    padding-top: 0;
    text-align: left;
  }

  .form-row small,
  .test-result {
    grid-column: auto;
    margin-left: 0;
  }

  .config-header,
  .config-body,
  .config-footer {
    padding-left: 20px;
    padding-right: 20px;
  }

  .config-footer {
    align-items: stretch;
    flex-direction: column;
    gap: 14px;
  }

  .footer-actions {
    justify-content: flex-end;
  }
}
</style>
