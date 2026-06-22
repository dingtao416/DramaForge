<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserAIConfigStore } from '@/stores/user-ai-config'
import type { MediaCapability, ModelConfig, ProviderConfig } from '@/types/user-ai-config'

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

const providerForm = ref({
  name: '',
  provider_type: 'openai_compatible',
  auth_type: 'bearer',
  base_url: '',
  api_key: '',
  priority: 0,
  enabled: true,
  model_ids: '',
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
  await Promise.all([aiStore.fetchProviders(), aiStore.fetchDefaults()])
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

function openAddProvider() {
  editingProvider.value = null
  testResult.value = null
  providerForm.value = {
    name: '',
    provider_type: 'openai_compatible',
    auth_type: 'bearer',
    base_url: '',
    api_key: '',
    priority: 0,
    enabled: true,
    model_ids: '',
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
    enabled: provider.enabled,
    model_ids: modelsForCapability(provider, activeCapability.value).map((model) => model.model_id).join('\n'),
  }
  showProviderForm.value = true
}

async function saveProvider() {
  const modelIds = normalizedModels()
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

    const existing = new Set(modelsForCapability(provider, activeCapability.value).map((model) => model.model_id))
    for (const modelId of modelIds) {
      if (existing.has(modelId)) continue
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

              <label class="form-row form-row-required">
                <span>支持的模型</span>
                <textarea
                  v-model="providerForm.model_ids"
                  rows="3"
                  placeholder="请输入模型名，多个模型可用换行或逗号分隔"
                />
              </label>

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
