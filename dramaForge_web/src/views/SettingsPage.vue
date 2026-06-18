<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useUserAIConfigStore } from '@/stores/user-ai-config'
import * as aiConfigApi from '@/api/user-ai-config'
import type { CatalogProvider, MediaCapability, ProviderConfig } from '@/types/user-ai-config'

const router = useRouter()
const authStore = useAuthStore()
const aiStore = useUserAIConfigStore()

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

const capabilityLabels: Record<string, string> = {
  image: '图片',
  video: '视频',
}
const mediaCapabilities: MediaCapability[] = ['image', 'video']

const showProviderForm = ref(false)
const editingProvider = ref<ProviderConfig | null>(null)
const expandedProvider = ref<number | null>(null)
const catalog = ref<CatalogProvider[]>([])
const testResult = ref<{ success: boolean; message: string } | null>(null)
const saving = ref(false)
const testing = ref(false)
const toast = ref<{ show: boolean; msg: string; type: 'ok' | 'err' }>({ show: false, msg: '', type: 'ok' })

const providerForm = ref({
  name: '',
  provider_type: 'openai_compatible',
  auth_type: 'bearer',
  base_url: '',
  api_key: '',
  priority: 100,
  headers_json: '{}',
  config_json: '{}',
  enabled: true,
})

const showModelForm = ref(false)
const modelProviderId = ref<number | null>(null)
const modelForm = ref({
  capability: 'image' as MediaCapability,
  model_id: '',
  display_name: '',
  is_default: false,
  default_params_json: '{}',
  capabilities_json: '{}',
})

const activeProviders = computed(() => aiStore.providers.filter((p) => p.enabled))

onMounted(async () => {
  await Promise.all([aiStore.fetchProviders(), aiStore.fetchDefaults(), loadCatalog()])
  if (aiStore.providers.length === 1) expandedProvider.value = aiStore.providers[0].id
})

async function loadCatalog() {
  catalog.value = await aiConfigApi.listCatalog()
}

function showToast(msg: string, type: 'ok' | 'err' = 'ok') {
  toast.value = { show: true, msg, type }
  window.setTimeout(() => (toast.value.show = false), 2500)
}

function parseJsonObject(value: string, label: string) {
  try {
    const parsed = JSON.parse(value || '{}')
    if (!parsed || Array.isArray(parsed) || typeof parsed !== 'object') throw new Error()
    return parsed
  } catch {
    throw new Error(`${label} 必须是 JSON 对象`)
  }
}

function openAddProvider() {
  editingProvider.value = null
  testResult.value = null
  providerForm.value = {
    name: '',
    provider_type: 'openai_compatible',
    auth_type: 'bearer',
    base_url: '',
    api_key: '',
    priority: 100,
    headers_json: '{}',
    config_json: '{}',
    enabled: true,
  }
  showProviderForm.value = true
}

function openEditProvider(provider: ProviderConfig) {
  editingProvider.value = provider
  testResult.value = null
  providerForm.value = {
    name: provider.name,
    provider_type: provider.provider_type,
    auth_type: provider.auth_type,
    base_url: provider.base_url,
    api_key: '',
    priority: provider.priority,
    headers_json: JSON.stringify(provider.headers_json || {}, null, 2),
    config_json: JSON.stringify(provider.config_json || {}, null, 2),
    enabled: provider.enabled,
  }
  showProviderForm.value = true
}

async function saveProvider() {
  if (!providerForm.value.name.trim()) return showToast('请填写 Provider 名称', 'err')
  saving.value = true
  try {
    const payload: any = {
      name: providerForm.value.name,
      provider_type: providerForm.value.provider_type,
      auth_type: providerForm.value.auth_type,
      base_url: providerForm.value.base_url,
      priority: Number(providerForm.value.priority) || 100,
      enabled: providerForm.value.enabled,
      headers_json: parseJsonObject(providerForm.value.headers_json, 'Headers'),
      config_json: parseJsonObject(providerForm.value.config_json, 'Config'),
    }
    if (!editingProvider.value || providerForm.value.api_key) payload.api_key = providerForm.value.api_key
    const provider = editingProvider.value
      ? await aiStore.updateProvider(editingProvider.value.id, payload)
      : await aiStore.addProvider(payload)
    expandedProvider.value = provider.id
    showProviderForm.value = false
    await aiStore.fetchDefaults()
    showToast('Provider 已保存')
  } catch (e: any) {
    showToast(e.message || '保存失败', 'err')
  } finally {
    saving.value = false
  }
}

async function testProvider() {
  if (!editingProvider.value) return
  testing.value = true
  testResult.value = null
  try {
    testResult.value = await aiStore.testKey(editingProvider.value.id)
  } finally {
    testing.value = false
  }
}

async function importCatalog(index: number) {
  const provider = await aiConfigApi.importCatalog(index)
  await aiStore.fetchProviders()
  await aiStore.fetchDefaults()
  expandedProvider.value = provider.id
  showToast('模板已导入，请填写 API Key')
}

function openAddModel(providerId: number, capability: MediaCapability = 'image') {
  modelProviderId.value = providerId
  modelForm.value = {
    capability,
    model_id: '',
    display_name: '',
    is_default: false,
    default_params_json: '{}',
    capabilities_json: '{}',
  }
  showModelForm.value = true
}

async function saveModel() {
  if (!modelProviderId.value || !modelForm.value.model_id.trim()) return showToast('请填写模型 ID', 'err')
  try {
    await aiStore.addModel(modelProviderId.value, {
      capability: modelForm.value.capability,
      model_id: modelForm.value.model_id,
      display_name: modelForm.value.display_name || modelForm.value.model_id,
      is_default: modelForm.value.is_default,
      default_params_json: parseJsonObject(modelForm.value.default_params_json, '默认参数'),
      capabilities_json: parseJsonObject(modelForm.value.capabilities_json, '能力配置'),
      param_schema_json: {},
    })
    showModelForm.value = false
    await aiStore.fetchDefaults()
    showToast('模型已添加')
  } catch (e: any) {
    showToast(e.message || '模型添加失败', 'err')
  }
}

async function deleteProvider(id: number) {
  await aiStore.removeProvider(id)
  await aiStore.fetchDefaults()
  showToast('Provider 已删除')
}

async function setDefaultModel(modelId: number) {
  await aiStore.setDefault(modelId)
  showToast('默认模型已更新')
}

function groupedModels(provider: ProviderConfig) {
  return {
    image: provider.models.filter((m) => (m.capability || m.capability_type) === 'image'),
    video: provider.models.filter((m) => (m.capability || m.capability_type) === 'video'),
  }
}

function logout() {
  authStore.doLogout()
  router.push('/login')
}
</script>

<template>
  <div class="settings-page">
    <Transition name="toast">
      <div v-if="toast.show" class="toast" :class="toast.type === 'ok' ? 'toast-ok' : 'toast-err'">
        {{ toast.msg }}
      </div>
    </Transition>

    <header class="settings-header">
      <div class="settings-header-inner">
        <button class="btn-back" @click="router.push('/')">‹</button>
        <div>
          <h1 class="settings-title">设置</h1>
          <p class="settings-subtitle">管理图片和视频生成 Provider、模型与任务配置</p>
        </div>
      </div>
    </header>

    <main class="settings-main">
      <div class="card account-card">
        <div class="account-avatar">{{ authStore.isLoggedIn ? authStore.displayName.charAt(0).toUpperCase() : 'U' }}</div>
        <div class="account-info">
          <div class="account-name">{{ authStore.isLoggedIn ? authStore.displayName : '未登录' }}</div>
          <div class="account-email">{{ authStore.user?.email || authStore.user?.phone || '-' }}</div>
        </div>
        <span class="status-badge status-active"><span class="status-dot"></span>活跃</span>
      </div>

      <section class="section">
        <div class="section-header">
          <div>
            <h2 class="section-title">媒体生成 Provider</h2>
            <p class="section-desc">图片和视频模型使用新的 Provider / Model / Adapter 配置，不再读取旧 Key 配置。</p>
          </div>
          <button class="btn btn-primary" @click="openAddProvider">添加 Provider</button>
        </div>

        <div v-if="aiStore.loading" class="card empty-card">
          <div class="empty-text">加载配置中...</div>
        </div>

        <div v-else-if="aiStore.providers.length === 0">
          <div class="card empty-card">
            <div class="empty-title">还没有 Provider</div>
            <div class="empty-desc">导入模板后填写 API Key，或手动添加一个自定义 Provider。</div>
          </div>
          <div class="quick-label">快速导入</div>
          <div class="quick-grid">
            <button v-for="(item, i) in catalog" :key="item.name" class="quick-card" @click="importCatalog(i)">
              <div class="quick-card-body">
                <div class="quick-card-name">{{ item.name }}</div>
                <div class="quick-card-desc">{{ item.provider_type }} · {{ item.models.length }} models</div>
              </div>
            </button>
          </div>
        </div>

        <div v-else class="key-list">
          <div v-for="provider in aiStore.providers" :key="provider.id" class="key-card" :class="{ 'key-card-expanded': expandedProvider === provider.id }">
            <div class="key-header" @click="expandedProvider = expandedProvider === provider.id ? null : provider.id">
              <div class="key-status" :class="provider.enabled ? 'key-status-on' : 'key-status-off'"></div>
              <div class="key-header-info">
                <div class="key-name">
                  {{ provider.name }}
                  <span class="default-badge">{{ provider.provider_type }}</span>
                </div>
                <div class="key-url">{{ provider.base_url || 'No base URL' }}</div>
              </div>
              <div class="key-header-caps">
                <span class="cap-chip">图片 {{ groupedModels(provider).image.length }}</span>
                <span class="cap-chip">视频 {{ groupedModels(provider).video.length }}</span>
              </div>
              <div class="key-header-meta">
                <span class="key-meta-item">P{{ provider.priority }}</span>
              </div>
            </div>

            <Transition name="expand">
              <div v-if="expandedProvider === provider.id" class="key-body">
                <div class="key-info-bar">
                  <div class="key-info-item">Auth: {{ provider.auth_type }}</div>
                  <div class="key-info-item">Key: <span class="font-mono">{{ provider.api_key_masked || '-' }}</span></div>
                </div>

                <div class="model-groups">
                  <div v-for="cap in mediaCapabilities" :key="cap" class="model-group">
                    <div class="model-group-label">
                      <span>{{ capabilityLabels[cap] }}</span>
                      <span class="model-group-count">{{ groupedModels(provider)[cap].length }}</span>
                    </div>
                    <div class="model-group-list">
                      <div v-for="model in groupedModels(provider)[cap]" :key="model.id" class="model-row" :class="{ 'model-row-default': model.is_default }">
                        <div class="model-row-info">
                          <span class="model-row-name">{{ model.display_name }}</span>
                          <span class="model-row-id">{{ model.model_id }}</span>
                        </div>
                        <div class="model-row-actions">
                          <span v-if="model.is_default" class="model-default-tag">默认</span>
                          <button v-else class="btn-text-sm" @click.stop="setDefaultModel(model.id)">设为默认</button>
                          <button class="btn-icon-sm btn-icon-danger" @click.stop="aiStore.removeModel(model.id)">删除</button>
                        </div>
                      </div>
                      <button class="btn btn-ghost" @click.stop="openAddModel(provider.id, cap)">添加{{ capabilityLabels[cap] }}模型</button>
                    </div>
                  </div>
                </div>

                <div class="key-actions">
                  <button class="btn btn-ghost" @click.stop="openEditProvider(provider)">编辑</button>
                  <div class="flex-1"></div>
                  <button class="btn btn-ghost btn-ghost-danger" @click.stop="deleteProvider(provider.id)">删除</button>
                </div>
              </div>
            </Transition>
          </div>
        </div>
      </section>

      <section class="section">
        <div class="section-header">
          <div>
            <h2 class="section-title">当前默认模型</h2>
            <p class="section-desc">业务生成会优先使用这里的默认图片和视频模型。</p>
          </div>
        </div>
        <div class="key-info-bar">
          <div class="key-info-item">图片：{{ aiStore.defaults.image?.provider_name || '系统默认' }} / {{ aiStore.defaults.image?.model_id || '-' }}</div>
          <div class="key-info-item">视频：{{ aiStore.defaults.video?.provider_name || '系统默认' }} / {{ aiStore.defaults.video?.model_id || '-' }}</div>
        </div>
      </section>

      <button class="btn-logout" @click="logout">退出登录</button>
    </main>

    <Teleport to="body">
      <Transition name="modal">
        <div v-if="showProviderForm" class="modal-mask">
          <div class="modal-panel">
            <div class="modal-header">
              <div>
                <h3 class="modal-title">{{ editingProvider ? '编辑 Provider' : '添加 Provider' }}</h3>
                <p class="modal-subtitle">配置厂商协议、鉴权方式和扩展参数。</p>
              </div>
              <button class="btn-icon" @click="showProviderForm = false">×</button>
            </div>
            <div class="modal-body">
              <div class="form-group">
                <label class="form-label">名称</label>
                <input v-model="providerForm.name" class="form-input" placeholder="OpenAI Native" />
              </div>
              <div class="form-group">
                <label class="form-label">Provider Type</label>
                <select v-model="providerForm.provider_type" class="form-input">
                  <option v-for="type in providerTypes" :key="type" :value="type">{{ type }}</option>
                </select>
              </div>
              <div class="form-group">
                <label class="form-label">Auth Type</label>
                <select v-model="providerForm.auth_type" class="form-input">
                  <option value="bearer">bearer</option>
                  <option value="api-key">api-key</option>
                  <option value="query">query</option>
                </select>
              </div>
              <div class="form-group">
                <label class="form-label">Base URL</label>
                <input v-model="providerForm.base_url" class="form-input form-input-mono" placeholder="https://api.openai.com/v1" />
              </div>
              <div class="form-group">
                <label class="form-label">API Key</label>
                <input v-model="providerForm.api_key" type="password" class="form-input" :placeholder="editingProvider ? '留空则不修改' : 'sk-...'" />
              </div>
              <div class="form-group">
                <label class="form-label">Priority</label>
                <input v-model.number="providerForm.priority" type="number" class="form-input" />
              </div>
              <div class="form-group">
                <label class="form-label">Headers JSON</label>
                <textarea v-model="providerForm.headers_json" class="form-input form-input-mono" rows="4"></textarea>
              </div>
              <div class="form-group">
                <label class="form-label">Config JSON</label>
                <textarea v-model="providerForm.config_json" class="form-input form-input-mono" rows="5"></textarea>
              </div>
              <label class="key-info-item">
                <input v-model="providerForm.enabled" type="checkbox" />
                启用 Provider
              </label>
              <div v-if="testResult" class="alert" :class="testResult.success ? 'alert-ok' : 'alert-err'">
                {{ testResult.message }}
              </div>
            </div>
            <div class="modal-footer">
              <div class="modal-footer-left">
                <button v-if="editingProvider" class="btn btn-outline" :disabled="testing" @click="testProvider">
                  {{ testing ? '测试中...' : '测试连接' }}
                </button>
              </div>
              <div class="modal-footer-right">
                <button class="btn btn-ghost" @click="showProviderForm = false">取消</button>
                <button class="btn btn-primary" :disabled="saving" @click="saveProvider">{{ saving ? '保存中...' : '保存' }}</button>
              </div>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <Teleport to="body">
      <Transition name="modal">
        <div v-if="showModelForm" class="modal-mask">
          <div class="modal-panel modal-panel-sm">
            <div class="modal-header">
              <div>
                <h3 class="modal-title">添加模型</h3>
                <p class="modal-subtitle">模型参数会合并到每次生成请求。</p>
              </div>
              <button class="btn-icon" @click="showModelForm = false">×</button>
            </div>
            <div class="modal-body">
              <div class="form-group">
                <label class="form-label">能力</label>
                <select v-model="modelForm.capability" class="form-input">
                  <option value="image">图片</option>
                  <option value="video">视频</option>
                </select>
              </div>
              <div class="form-group">
                <label class="form-label">模型 ID</label>
                <input v-model="modelForm.model_id" class="form-input form-input-mono" placeholder="gpt-image-1" />
              </div>
              <div class="form-group">
                <label class="form-label">显示名称</label>
                <input v-model="modelForm.display_name" class="form-input" placeholder="GPT Image" />
              </div>
              <div class="form-group">
                <label class="form-label">默认参数 JSON</label>
                <textarea v-model="modelForm.default_params_json" class="form-input form-input-mono" rows="5"></textarea>
              </div>
              <label class="key-info-item">
                <input v-model="modelForm.is_default" type="checkbox" />
                设为该能力默认模型
              </label>
            </div>
            <div class="modal-footer">
              <button class="btn btn-ghost" @click="showModelForm = false">取消</button>
              <button class="btn btn-primary" @click="saveModel">保存</button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<style scoped>
.settings-page {
  min-height: 100vh;
  background: #f7f8fa;
  color: #17202a;
}
.settings-header {
  border-bottom: 1px solid #e6e8eb;
  background: #fff;
}
.settings-header-inner,
.settings-main {
  width: min(1120px, calc(100% - 32px));
  margin: 0 auto;
}
.settings-header-inner {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 18px 0;
}
.settings-main {
  display: grid;
  gap: 18px;
  padding: 20px 0 40px;
}
.settings-title,
.section-title,
.modal-title {
  margin: 0;
  letter-spacing: 0;
}
.settings-title {
  font-size: 22px;
}
.settings-subtitle,
.section-desc,
.modal-subtitle,
.empty-desc,
.quick-card-desc,
.key-url,
.model-row-id {
  color: #6b7280;
}
.settings-subtitle,
.section-desc,
.modal-subtitle {
  margin: 4px 0 0;
  font-size: 13px;
}
.card,
.key-card,
.section {
  background: #fff;
  border: 1px solid #e6e8eb;
  border-radius: 8px;
}
.account-card,
.section {
  padding: 16px;
}
.account-card,
.section-header,
.key-header,
.key-info-bar,
.key-actions,
.model-row,
.modal-footer {
  display: flex;
  align-items: center;
  gap: 12px;
}
.account-avatar {
  display: grid;
  place-items: center;
  width: 40px;
  height: 40px;
  border-radius: 8px;
  background: #111827;
  color: #fff;
  font-weight: 700;
}
.account-info,
.key-header-info,
.model-row-info,
.quick-card-body {
  min-width: 0;
  flex: 1;
}
.account-name,
.key-name,
.quick-card-name,
.model-row-name {
  font-weight: 650;
}
.section-header {
  justify-content: space-between;
  margin-bottom: 14px;
}
.btn,
.btn-back,
.btn-icon,
.btn-icon-sm,
.btn-text-sm,
.btn-logout {
  border: 1px solid #d9dde3;
  background: #fff;
  color: #17202a;
  border-radius: 7px;
  min-height: 34px;
  padding: 0 12px;
  cursor: pointer;
}
.btn-primary {
  border-color: #111827;
  background: #111827;
  color: #fff;
}
.btn-ghost-danger,
.btn-icon-danger {
  color: #b91c1c;
}
.btn-back,
.btn-icon,
.btn-icon-sm {
  display: grid;
  place-items: center;
  width: 34px;
  padding: 0;
}
.btn-text-sm {
  border: 0;
  min-height: auto;
  padding: 0;
  color: #2563eb;
}
.key-list,
.model-groups,
.model-group-list,
.quick-grid {
  display: grid;
  gap: 10px;
}
.quick-grid {
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
}
.quick-card {
  text-align: left;
  border: 1px solid #e6e8eb;
  background: #fff;
  border-radius: 8px;
  padding: 14px;
  cursor: pointer;
}
.quick-label {
  margin: 14px 0 8px;
  font-size: 13px;
  font-weight: 650;
}
.key-header {
  padding: 14px;
  cursor: pointer;
}
.key-body {
  border-top: 1px solid #e6e8eb;
  padding: 14px;
}
.key-status {
  width: 10px;
  height: 10px;
  border-radius: 999px;
  background: #9ca3af;
}
.key-status-on {
  background: #16a34a;
}
.key-status-off {
  background: #dc2626;
}
.key-header-caps {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}
.cap-chip,
.default-badge,
.model-default-tag,
.status-badge,
.key-info-item {
  border: 1px solid #e6e8eb;
  border-radius: 999px;
  padding: 4px 8px;
  font-size: 12px;
  background: #f9fafb;
}
.model-group {
  border-top: 1px solid #eef0f3;
  padding-top: 12px;
}
.model-group-label {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  font-size: 13px;
  font-weight: 650;
}
.model-group-count {
  color: #6b7280;
}
.model-row {
  justify-content: space-between;
  min-height: 44px;
  border: 1px solid #eef0f3;
  border-radius: 7px;
  padding: 8px 10px;
}
.model-row-actions,
.modal-footer-right,
.modal-footer-left {
  display: flex;
  align-items: center;
  gap: 8px;
}
.flex-1 {
  flex: 1;
}
.font-mono,
.form-input-mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
}
.empty-card {
  padding: 28px;
  text-align: center;
}
.empty-title {
  font-weight: 700;
}
.modal-mask {
  position: fixed;
  inset: 0;
  display: grid;
  place-items: center;
  padding: 20px;
  background: rgb(15 23 42 / 45%);
  z-index: 50;
}
.modal-panel {
  width: min(680px, 100%);
  max-height: min(760px, calc(100vh - 40px));
  overflow: auto;
  background: #fff;
  border-radius: 8px;
  border: 1px solid #e6e8eb;
}
.modal-panel-sm {
  width: min(520px, 100%);
}
.modal-header,
.modal-body,
.modal-footer {
  padding: 16px;
}
.modal-header {
  display: flex;
  justify-content: space-between;
  border-bottom: 1px solid #e6e8eb;
}
.modal-footer {
  justify-content: space-between;
  border-top: 1px solid #e6e8eb;
}
.form-group {
  display: grid;
  gap: 6px;
  margin-bottom: 12px;
}
.form-label {
  font-size: 13px;
  font-weight: 650;
}
.form-input {
  width: 100%;
  border: 1px solid #d9dde3;
  border-radius: 7px;
  padding: 9px 10px;
  background: #fff;
  color: #17202a;
  box-sizing: border-box;
}
.alert {
  border-radius: 7px;
  padding: 10px;
  margin-top: 10px;
}
.alert-ok {
  background: #ecfdf5;
  color: #047857;
}
.alert-err,
.toast-err {
  background: #fef2f2;
  color: #b91c1c;
}
.toast {
  position: fixed;
  top: 18px;
  right: 18px;
  z-index: 60;
  border-radius: 7px;
  padding: 10px 12px;
  box-shadow: 0 10px 30px rgb(15 23 42 / 16%);
}
.toast-ok {
  background: #111827;
  color: #fff;
}
.btn-logout {
  justify-self: start;
}
@media (max-width: 720px) {
  .section-header,
  .key-header,
  .model-row,
  .key-actions,
  .modal-footer {
    align-items: stretch;
    flex-direction: column;
  }
  .key-header-caps {
    width: 100%;
  }
}
</style>
