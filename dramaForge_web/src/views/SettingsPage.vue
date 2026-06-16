<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useUserAIConfigStore } from '@/stores/user-ai-config'
import type { UserAPIKey, DiscoveredModel } from '@/types/user-ai-config'

const router = useRouter()
const authStore = useAuthStore()
const aiStore = useUserAIConfigStore()

const capMeta: Record<string, { icon: string; label: string; color: string; bg: string; ring: string }> = {
  chat:  { icon: '💬', label: '对话', color: 'text-blue-600', bg: 'bg-blue-50', ring: 'ring-blue-200' },
  image: { icon: '🎨', label: '图片', color: 'text-violet-600', bg: 'bg-violet-50', ring: 'ring-violet-200' },
  video: { icon: '🎬', label: '视频', color: 'text-amber-600', bg: 'bg-amber-50', ring: 'ring-amber-200' },
  tts:   { icon: '🎙️', label: '语音', color: 'text-emerald-600', bg: 'bg-emerald-50', ring: 'ring-emerald-200' },
}

// ── State ──
const showForm = ref(false)
const editingKey = ref<UserAPIKey | null>(null)
const form = ref({ name: '', base_url: '', api_key: '', capabilities: ['chat', 'image', 'video', 'tts'] as string[] })
const testResult = ref<{ success: boolean; message: string } | null>(null)
const testing = ref(false)
const saving = ref(false)
const discoveredModels = ref<DiscoveredModel[]>([])
const discovering = ref(false)
const showAddModel = ref(false)
const addModelKeyId = ref<number | null>(null)
const addModelForm = ref({ model_id: '', display_name: '', capability_type: 'chat' })
const expandedKey = ref<number | null>(null)
const toast = ref<{ show: boolean; msg: string; type: 'ok' | 'err' }>({ show: false, msg: '', type: 'ok' })

function showToast(msg: string, type: 'ok' | 'err' = 'ok') {
  toast.value = { show: true, msg, type }
  setTimeout(() => toast.value.show = false, 2500)
}

onMounted(async () => {
  await Promise.all([aiStore.fetchKeys(), aiStore.fetchDefaults()])
  if (aiStore.keys.length === 1) expandedKey.value = aiStore.keys[0].id
})

function toggleExpand(id: number) {
  expandedKey.value = expandedKey.value === id ? null : id
}

function openAddForm() {
  editingKey.value = null
  form.value = { name: '', base_url: '', api_key: '', capabilities: ['chat', 'image', 'video', 'tts'] }
  testResult.value = null
  discoveredModels.value = []
  showForm.value = true
}

function openEditForm(key: UserAPIKey) {
  editingKey.value = key
  form.value = { name: key.name, base_url: key.base_url, api_key: '', capabilities: [...key.capabilities] }
  testResult.value = null
  discoveredModels.value = []
  showForm.value = true
}

function toggleCap(cap: string) {
  const i = form.value.capabilities.indexOf(cap)
  i >= 0 ? form.value.capabilities.splice(i, 1) : form.value.capabilities.push(cap)
}

async function handleSave() {
  if (!form.value.name || !form.value.base_url) { showToast('请填写名称和 URL', 'err'); return }
  if (!editingKey.value && !form.value.api_key) { showToast('请填写 API Key', 'err'); return }
  saving.value = true
  try {
    if (editingKey.value) {
      const d: Record<string, any> = { name: form.value.name, base_url: form.value.base_url, capabilities: form.value.capabilities.join(',') }
      if (form.value.api_key) d.api_key = form.value.api_key
      await aiStore.updateKey(editingKey.value.id, d)
      showToast('已更新')
    } else {
      await aiStore.addKey({ ...form.value, capabilities: form.value.capabilities.join(',') })
      showToast('已添加')
    }
    showForm.value = false
    await aiStore.fetchDefaults()
  } catch (e: any) { showToast(e.message || '保存失败', 'err') }
  finally { saving.value = false }
}

async function handleTest() {
  const id = editingKey.value?.id
  if (!id) { testResult.value = { success: false, message: '请先保存后再测试' }; return }
  testing.value = true; testResult.value = null
  try { testResult.value = await aiStore.testKey(id) }
  finally { testing.value = false }
}

async function handleDiscover() {
  const id = editingKey.value?.id
  if (!id) { showToast('请先保存后再发现模型', 'err'); return }
  discovering.value = true
  try {
    const r = await aiStore.discoverModels(id)
    // Refresh key list to show auto-added models
    await aiStore.fetchKeys()
    await aiStore.fetchDefaults()
    // Keep expanded
    expandedKey.value = id
    if (r.added > 0) {
      showToast(`已自动添加 ${r.added} 个模型并设为默认`)
    } else {
      showToast('所有能力类型已有配置，无新增')
    }
  } catch (e: any) {
    showToast(e.message || '发现失败', 'err')
  } finally {
    discovering.value = false
  }
}

async function handleImportDiscovered(m: DiscoveredModel) {
  const id = editingKey.value?.id
  if (!id) return
  await aiStore.addModel(id, { model_id: m.model_id, display_name: m.display_name, capability_type: m.capability_type })
  discoveredModels.value = discoveredModels.value.filter(x => x !== m)
  showToast(`已添加 ${m.model_id}`)
}

async function handleDeleteKey(id: number) {
  await aiStore.removeKey(id)
  if (expandedKey.value === id) expandedKey.value = null
  await aiStore.fetchDefaults()
  showToast('已删除')
}

function openAddModel(keyId: number) {
  addModelKeyId.value = keyId
  addModelForm.value = { model_id: '', display_name: '', capability_type: 'chat' }
  showAddModel.value = true
}

async function handleAddModel() {
  if (!addModelKeyId.value || !addModelForm.value.model_id) return
  await aiStore.addModel(addModelKeyId.value, addModelForm.value)
  showAddModel.value = false
  showToast('模型已添加')
}

async function handleSetDefault(modelId: number) {
  await aiStore.setDefault(modelId)
  showToast('已设为默认')
}

async function handleImportCatalog(i: number) {
  const { default: c } = await import('@/api/client')
  await c.post(`/user-ai/catalog/import?catalog_index=${i}`)
  await aiStore.fetchKeys(); await aiStore.fetchDefaults()
  if (aiStore.keys.length === 1) expandedKey.value = aiStore.keys[0].id
  showToast('已导入')
}

function logout() { authStore.doLogout(); router.push('/login') }

function groupModels(models: UserAPIKey['models']) {
  const g: Record<string, typeof models> = {}
  for (const m of models) { (g[m.capability_type] ??= []).push(m) }
  return g
}
</script>

<template>
  <div class="settings-page">

    <!-- Toast -->
    <Transition name="toast">
      <div v-if="toast.show" class="toast" :class="toast.type === 'ok' ? 'toast-ok' : 'toast-err'">
        {{ toast.msg }}
      </div>
    </Transition>

    <!-- ═══ Header ═══ -->
    <header class="settings-header">
      <div class="settings-header-inner">
        <button class="btn-back" @click="router.push('/')">
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none"><path d="M12 5L7 10L12 15" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>
        </button>
        <div>
          <h1 class="settings-title">设置</h1>
          <p class="settings-subtitle">管理你的账户和 AI 模型配置</p>
        </div>
      </div>
    </header>

    <!-- ═══ Content ═══ -->
    <main class="settings-main">

      <!-- ── Account Card ── -->
      <div class="card account-card">
        <div class="account-avatar">
          {{ authStore.isLoggedIn ? authStore.displayName.charAt(0).toUpperCase() : 'U' }}
        </div>
        <div class="account-info">
          <div class="account-name">{{ authStore.isLoggedIn ? authStore.displayName : '未登录' }}</div>
          <div class="account-email">{{ authStore.user?.email || authStore.user?.phone || '—' }}</div>
        </div>
        <span class="status-badge status-active">
          <span class="status-dot"></span>
          活跃
        </span>
      </div>

      <!-- ── API Keys Section ── -->
      <div class="section">
        <div class="section-header">
          <div>
            <h2 class="section-title">AI 模型配置</h2>
            <p class="section-desc">管理 API Key 和模型，支持中转站或直连模式</p>
          </div>
          <button class="btn btn-primary" @click="openAddForm">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M8 3v10M3 8h10" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
            添加 Key
          </button>
        </div>

        <!-- Loading -->
        <div v-if="aiStore.loading" class="card empty-card">
          <div class="spinner-lg"></div>
          <div class="empty-text">加载配置中...</div>
        </div>

        <!-- Empty -->
        <div v-else-if="aiStore.keys.length === 0">
          <div class="card empty-card">
            <div class="empty-icon">🔑</div>
            <div class="empty-title">还没有配置 API Key</div>
            <div class="empty-desc">添加你的 API Key 以使用 AI 功能</div>
          </div>
          <div class="quick-label">快速开始</div>
          <div class="quick-grid">
            <button class="quick-card" @click="handleImportCatalog(0)">
              <div class="quick-card-icon" style="background: linear-gradient(135deg, #7C3AED, #A855F7);">L</div>
              <div class="quick-card-body">
                <div class="quick-card-name">laozhang.ai</div>
                <div class="quick-card-desc">中转站 · 全能力 · 推荐</div>
              </div>
              <div class="quick-card-caps">
                <span v-for="c in ['chat','image','video','tts']" :key="c" class="cap-chip-sm" :class="[capMeta[c].bg, capMeta[c].color]">{{ capMeta[c].icon }} {{ capMeta[c].label }}</span>
              </div>
            </button>
            <button class="quick-card" @click="handleImportCatalog(1)">
              <div class="quick-card-icon" style="background: linear-gradient(135deg, #059669, #10B981);">O</div>
              <div class="quick-card-body">
                <div class="quick-card-name">OpenAI</div>
                <div class="quick-card-desc">直连官方 · GPT 系列</div>
              </div>
              <div class="quick-card-caps">
                <span v-for="c in ['chat','image','tts']" :key="c" class="cap-chip-sm" :class="[capMeta[c].bg, capMeta[c].color]">{{ capMeta[c].icon }} {{ capMeta[c].label }}</span>
              </div>
            </button>
          </div>
        </div>

        <!-- Key List -->
        <div v-else class="key-list">
          <div v-for="key in aiStore.keys" :key="key.id" class="key-card" :class="{ 'key-card-expanded': expandedKey === key.id }">

            <!-- Collapsed Header -->
            <div class="key-header" @click="toggleExpand(key.id)">
              <div class="key-status" :class="key.enabled ? 'key-status-on' : 'key-status-off'"></div>
              <div class="key-header-info">
                <div class="key-name">
                  {{ key.name }}
                  <span v-if="key.is_default" class="default-badge">默认</span>
                </div>
                <div class="key-url">{{ key.base_url }}</div>
              </div>
              <div class="key-header-caps">
                <span v-for="cap in key.capabilities" :key="cap" class="cap-chip" :class="[capMeta[cap]?.bg, capMeta[cap]?.color]">
                  {{ capMeta[cap]?.icon }} {{ capMeta[cap]?.label }}
                </span>
              </div>
              <div class="key-header-meta">
                <span class="key-meta-item">{{ key.models.length }} 模型</span>
              </div>
              <svg class="key-chevron" :class="{ 'key-chevron-open': expandedKey === key.id }" width="20" height="20" viewBox="0 0 20 20" fill="none"><path d="M6 8L10 12L14 8" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>
            </div>

            <!-- Expanded Body -->
            <Transition name="expand">
              <div v-if="expandedKey === key.id" class="key-body">
                <div class="key-info-bar">
                  <div class="key-info-item">
                    <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><rect x="2" y="6" width="12" height="7" rx="2" stroke="currentColor" stroke-width="1.3"/><path d="M5 6V4.5a3 3 0 016 0V6" stroke="currentColor" stroke-width="1.3"/></svg>
                    <span class="font-mono">{{ key.api_key_masked }}</span>
                  </div>
                  <div class="key-info-item">
                    <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><circle cx="8" cy="8" r="6" stroke="currentColor" stroke-width="1.3"/><path d="M8 5v3l2.5 1.5" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/></svg>
                    <span>{{ key.created_at ? new Date(key.created_at).toLocaleDateString('zh-CN') : '—' }}</span>
                  </div>
                </div>

                <!-- Models by type -->
                <div v-if="key.models.length > 0" class="model-groups">
                  <div v-for="(models, capType) in groupModels(key.models)" :key="String(capType)" class="model-group">
                    <div class="model-group-label">
                      <span>{{ capMeta[String(capType)]?.icon }}</span>
                      <span>{{ capMeta[String(capType)]?.label || String(capType) }}</span>
                      <span class="model-group-count">{{ models.length }}</span>
                    </div>
                    <div class="model-group-list">
                      <div v-for="model in models" :key="model.id" class="model-row" :class="{ 'model-row-default': model.is_default }">
                        <div class="model-row-info">
                          <span class="model-row-name">{{ model.display_name }}</span>
                          <span class="model-row-id">{{ model.model_id }}</span>
                        </div>
                        <div class="model-row-actions">
                          <span v-if="model.is_default" class="model-default-tag">✓ 默认</span>
                          <button v-else class="btn-text-sm" @click.stop="handleSetDefault(model.id)">设为默认</button>
                          <button class="btn-icon-sm btn-icon-danger" @click.stop="aiStore.removeModel(model.id)" title="删除">
                            <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M3.5 3.5l7 7M10.5 3.5l-7 7" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
                <div v-else class="model-empty">暂无模型，点击下方按钮添加</div>

                <!-- Action bar -->
                <div class="key-actions">
                  <button class="btn btn-ghost" @click.stop="openAddModel(key.id)">
                    <svg width="15" height="15" viewBox="0 0 15 15" fill="none"><path d="M7.5 3v9M3 7.5h9" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>
                    添加模型
                  </button>
                  <button class="btn btn-ghost" @click.stop="openEditForm(key)">
                    <svg width="15" height="15" viewBox="0 0 15 15" fill="none"><path d="M10 2.5l2.5 2.5L5 12.5H2.5V10L10 2.5z" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/></svg>
                    编辑
                  </button>
                  <div class="flex-1"></div>
                  <button class="btn btn-ghost btn-ghost-danger" @click.stop="handleDeleteKey(key.id)">
                    <svg width="15" height="15" viewBox="0 0 15 15" fill="none"><path d="M2.5 4h10M5.5 4V2.5h4V4M4 4l.5 8.5h6L11 4" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/></svg>
                    删除
                  </button>
                </div>
              </div>
            </Transition>
          </div>
        </div>
      </div>

      <!-- ── Logout ── -->
      <button class="btn-logout" @click="logout">
        <svg width="18" height="18" viewBox="0 0 18 18" fill="none"><path d="M6 3H4A2 2 0 002 5v8a2 2 0 002 2h2M12 13l4-4-4-4M10 9h6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
        退出登录
      </button>
    </main>

    <!-- ═══ Add/Edit Key Modal ═══ -->
    <Teleport to="body">
      <Transition name="modal">
        <div v-if="showForm" class="modal-mask">
          <div class="modal-panel">
            <div class="modal-header">
              <div>
                <h3 class="modal-title">{{ editingKey ? '编辑 API Key' : '添加 API Key' }}</h3>
                <p class="modal-subtitle">{{ editingKey ? '修改供应商连接配置' : '配置一个新的 AI 供应商' }}</p>
              </div>
              <button class="btn-icon" @click="showForm = false">
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M3 3l10 10M13 3L3 13" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>
              </button>
            </div>

            <div class="modal-body">
              <div class="form-group">
                <label class="form-label">名称</label>
                <input v-model="form.name" class="form-input" placeholder="如：laozhang.ai 中转站" />
              </div>
              <div class="form-group">
                <label class="form-label">API URL</label>
                <input v-model="form.base_url" class="form-input form-input-mono" placeholder="https://api.laozhang.ai/v1" />
              </div>
              <div class="form-group">
                <label class="form-label">API Key</label>
                <input v-model="form.api_key" type="password" class="form-input" :placeholder="editingKey ? '留空则不修改' : 'sk-xxx'" />
              </div>
              <div class="form-group">
                <label class="form-label">支持的能力</label>
                <div class="cap-toggle-group">
                  <button v-for="cap in ['chat','image','video','tts']" :key="cap" class="cap-toggle" :class="form.capabilities.includes(cap) ? `cap-toggle-on ${capMeta[cap].bg} ${capMeta[cap].color} ring-1 ${capMeta[cap].ring}` : ''" @click="toggleCap(cap)">
                    <span class="cap-toggle-icon">{{ capMeta[cap].icon }}</span>
                    <span>{{ capMeta[cap].label }}</span>
                    <svg v-if="form.capabilities.includes(cap)" class="cap-toggle-check" width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M3.5 7l3 3L10.5 5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
                  </button>
                </div>
              </div>

              <!-- Test result -->
              <Transition name="fade">
                <div v-if="testResult" class="alert" :class="testResult.success ? 'alert-ok' : 'alert-err'">
                  <span class="alert-icon">{{ testResult.success ? '✅' : '❌' }}</span>
                  <span>{{ testResult.message }}</span>
                </div>
              </Transition>

              <!-- Discovered -->
              <Transition name="fade">
                <div v-if="discoveredModels.length > 0" class="discover-panel">
                  <div class="discover-header">
                    <span class="discover-title">发现 {{ discoveredModels.length }} 个模型</span>
                    <span class="discover-hint">点击添加</span>
                  </div>
                  <div class="discover-list">
                    <div v-for="m in discoveredModels" :key="m.model_id" class="discover-item" @click="handleImportDiscovered(m)">
                      <span class="cap-chip-sm" :class="[capMeta[m.capability_type]?.bg, capMeta[m.capability_type]?.color]">{{ capMeta[m.capability_type]?.icon }}</span>
                      <span class="discover-model-id">{{ m.model_id }}</span>
                      <span class="discover-add">+ 添加</span>
                    </div>
                  </div>
                </div>
              </Transition>
            </div>

            <div class="modal-footer">
              <div class="modal-footer-left">
                <button v-if="editingKey" class="btn btn-outline" :disabled="testing" @click="handleTest">
                  <div v-if="testing" class="spinner-sm"></div>
                  <svg v-else width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M2 7.5l3 3L12 3" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>
                  {{ testing ? '测试中' : '测试连接' }}
                </button>
                <button v-if="editingKey" class="btn btn-outline" :disabled="discovering" @click="handleDiscover">
                  <div v-if="discovering" class="spinner-sm"></div>
                  <svg v-else width="14" height="14" viewBox="0 0 14 14" fill="none"><circle cx="7" cy="7" r="5" stroke="currentColor" stroke-width="1.4"/><path d="M7 4.5v5M4.5 7h5" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/></svg>
                  {{ discovering ? '发现中' : '发现模型' }}
                </button>
              </div>
              <div class="modal-footer-right">
                <button class="btn btn-ghost" @click="showForm = false">取消</button>
                <button class="btn btn-primary" :disabled="saving" @click="handleSave">
                  <div v-if="saving" class="spinner-sm spinner-white"></div>
                  {{ saving ? '保存中' : '保存' }}
                </button>
              </div>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- ═══ Add Model Modal ═══ -->
    <Teleport to="body">
      <Transition name="modal">
        <div v-if="showAddModel" class="modal-mask">
          <div class="modal-panel modal-panel-sm">
            <div class="modal-header">
              <div>
                <h3 class="modal-title">添加模型</h3>
                <p class="modal-subtitle">为当前 API Key 添加一个模型</p>
              </div>
              <button class="btn-icon" @click="showAddModel = false">
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M3 3l10 10M13 3L3 13" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>
              </button>
            </div>

            <div class="modal-body">
              <div class="form-group">
                <label class="form-label">能力类型</label>
                <div class="cap-toggle-group">
                  <button v-for="cap in ['chat','image','video','tts']" :key="cap" class="cap-toggle" :class="addModelForm.capability_type === cap ? `cap-toggle-on ${capMeta[cap].bg} ${capMeta[cap].color} ring-1 ${capMeta[cap].ring}` : ''" @click="addModelForm.capability_type = cap">
                    <span class="cap-toggle-icon">{{ capMeta[cap].icon }}</span>
                    <span>{{ capMeta[cap].label }}</span>
                  </button>
                </div>
              </div>
              <div class="form-group">
                <label class="form-label">模型 ID</label>
                <input v-model="addModelForm.model_id" class="form-input form-input-mono" placeholder="gpt-4o" />
              </div>
              <div class="form-group">
                <label class="form-label">显示名称</label>
                <input v-model="addModelForm.display_name" class="form-input" placeholder="GPT-4o" />
              </div>
            </div>

            <div class="modal-footer">
              <div class="flex-1"></div>
              <div class="modal-footer-right">
                <button class="btn btn-ghost" @click="showAddModel = false">取消</button>
                <button class="btn btn-primary" @click="handleAddModel">添加</button>
              </div>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<style scoped>
/* ── Page ── */
.settings-page {
  min-height: 100vh;
  background: #F4F5F7;
  padding-bottom: 80px;
}

/* ── Toast ── */
.toast {
  position: fixed; top: 20px; left: 50%; transform: translateX(-50%);
  z-index: 999; padding: 10px 24px; border-radius: 12px;
  font-size: 13px; font-weight: 600; color: #fff;
  box-shadow: 0 8px 24px rgba(0,0,0,0.15);
}
.toast-ok { background: #10B981; }
.toast-err { background: #EF4444; }
.toast-enter-active, .toast-leave-active { transition: all 0.3s ease; }
.toast-enter-from, .toast-leave-to { opacity: 0; transform: translateX(-50%) translateY(-12px); }

/* ── Header ── */
.settings-header {
  background: #fff;
  border-bottom: 1px solid #E5E7EB;
  position: sticky; top: 0; z-index: 30;
}
.settings-header-inner {
  max-width: 960px; margin: 0 auto;
  padding: 16px 32px;
  display: flex; align-items: center; gap: 16px;
}
.btn-back {
  width: 40px; height: 40px; border-radius: 12px;
  display: flex; align-items: center; justify-content: center;
  color: #6B7280; background: #F3F4F6;
  border: none; cursor: pointer; transition: all 0.15s;
}
.btn-back:hover { background: #E5E7EB; color: #374151; }
.settings-title { font-size: 20px; font-weight: 700; color: #111827; letter-spacing: -0.3px; }
.settings-subtitle { font-size: 13px; color: #9CA3AF; margin-top: 2px; }

/* ── Main ── */
.settings-main {
  max-width: 960px; margin: 0 auto;
  padding: 28px 32px;
  display: flex; flex-direction: column; gap: 24px;
}

/* ── Card ── */
.card {
  background: #fff;
  border: 1px solid #E5E7EB;
  border-radius: 16px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}

/* ── Account ── */
.account-card {
  padding: 20px 24px;
  display: flex; align-items: center; gap: 16px;
}
.account-avatar {
  width: 48px; height: 48px; border-radius: 14px;
  background: linear-gradient(135deg, #1F2937, #4B5563);
  color: #fff; font-size: 18px; font-weight: 700;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.account-info { flex: 1; min-width: 0; }
.account-name { font-size: 15px; font-weight: 600; color: #111827; }
.account-email { font-size: 13px; color: #9CA3AF; margin-top: 2px; }
.status-badge {
  display: flex; align-items: center; gap: 6px;
  padding: 6px 14px; border-radius: 100px;
  font-size: 12px; font-weight: 600;
}
.status-active { background: #ECFDF5; color: #059669; }
.status-dot { width: 7px; height: 7px; border-radius: 50%; background: currentColor; }

/* ── Section ── */
.section-header {
  display: flex; align-items: flex-start; justify-content: space-between;
  margin-bottom: 16px;
}
.section-title { font-size: 17px; font-weight: 700; color: #111827; }
.section-desc { font-size: 13px; color: #9CA3AF; margin-top: 3px; }

/* ── Buttons ── */
.btn {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 10px 20px; border-radius: 12px;
  font-size: 14px; font-weight: 600;
  border: none; cursor: pointer; transition: all 0.15s;
  white-space: nowrap;
}
.btn-primary { background: #111827; color: #fff; }
.btn-primary:hover { background: #374151; }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-outline { background: #fff; color: #374151; border: 1.5px solid #D1D5DB; }
.btn-outline:hover { border-color: #9CA3AF; background: #F9FAFB; }
.btn-ghost { background: transparent; color: #6B7280; padding: 10px 16px; }
.btn-ghost:hover { background: #F3F4F6; color: #374151; }
.btn-ghost-danger:hover { background: #FEF2F2; color: #DC2626; }
.btn-icon {
  width: 36px; height: 36px; border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
  color: #9CA3AF; background: transparent; border: none; cursor: pointer;
  transition: all 0.15s;
}
.btn-icon:hover { background: #F3F4F6; color: #6B7280; }
.btn-icon-sm {
  width: 30px; height: 30px; border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
  color: #D1D5DB; background: transparent; border: none; cursor: pointer;
  transition: all 0.15s;
}
.btn-icon-sm:hover { background: #F3F4F6; color: #6B7280; }
.btn-icon-danger:hover { background: #FEF2F2; color: #DC2626; }
.btn-text-sm {
  font-size: 12px; font-weight: 600; color: #6B7280;
  background: none; border: none; cursor: pointer; padding: 4px 8px;
  border-radius: 6px; transition: all 0.15s;
}
.btn-text-sm:hover { background: #F3F4F6; color: #111827; }

/* ── Empty ── */
.empty-card {
  padding: 48px 24px; text-align: center;
}
.empty-icon { font-size: 40px; margin-bottom: 12px; }
.empty-title { font-size: 15px; font-weight: 600; color: #374151; margin-bottom: 4px; }
.empty-desc { font-size: 13px; color: #9CA3AF; }

/* ── Quick Templates ── */
.quick-label { font-size: 13px; font-weight: 600; color: #9CA3AF; margin: 16px 0 10px; }
.quick-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.quick-card {
  background: #fff; border: 1.5px solid #E5E7EB; border-radius: 16px;
  padding: 20px; text-align: left; cursor: pointer;
  transition: all 0.2s; display: flex; flex-direction: column; gap: 12px;
}
.quick-card:hover { border-color: #A78BFA; box-shadow: 0 4px 16px rgba(124,58,237,0.1); transform: translateY(-1px); }
.quick-card-icon {
  width: 44px; height: 44px; border-radius: 14px;
  color: #fff; font-size: 18px; font-weight: 800;
  display: flex; align-items: center; justify-content: center;
}
.quick-card-body { flex: 1; }
.quick-card-name { font-size: 15px; font-weight: 700; color: #111827; }
.quick-card-desc { font-size: 12px; color: #9CA3AF; margin-top: 2px; }
.quick-card-caps { display: flex; gap: 6px; flex-wrap: wrap; }

/* ── Key List ── */
.key-list { display: flex; flex-direction: column; gap: 12px; }
.key-card {
  background: #fff; border: 1.5px solid #E5E7EB; border-radius: 16px;
  overflow: hidden; transition: all 0.2s;
}
.key-card-expanded { border-color: #C4B5FD; box-shadow: 0 4px 16px rgba(124,58,237,0.08); }

.key-header {
  display: flex; align-items: center; gap: 14px;
  padding: 16px 20px; cursor: pointer; transition: background 0.15s;
}
.key-header:hover { background: #FAFAFA; }
.key-status { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }
.key-status-on { background: #10B981; box-shadow: 0 0 0 3px rgba(16,185,129,0.15); }
.key-status-off { background: #D1D5DB; }
.key-header-info { flex: 1; min-width: 0; }
.key-name { font-size: 15px; font-weight: 600; color: #111827; display: flex; align-items: center; gap: 8px; }
.key-url { font-size: 12px; color: #9CA3AF; margin-top: 3px; font-family: ui-monospace, monospace; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.default-badge {
  font-size: 10px; font-weight: 700; color: #7C3AED;
  background: #F3F0FF; padding: 2px 8px; border-radius: 6px;
}
.key-header-caps { display: flex; gap: 6px; flex-shrink: 0; }
.key-header-meta { font-size: 12px; color: #9CA3AF; flex-shrink: 0; }
.key-chevron { color: #D1D5DB; flex-shrink: 0; transition: transform 0.25s ease; }
.key-chevron-open { transform: rotate(180deg); }

/* ── Key Body ── */
.key-body { border-top: 1px solid #F3F4F6; padding: 20px; }
.expand-enter-active, .expand-leave-active { transition: all 0.25s ease; overflow: hidden; }
.expand-enter-from, .expand-leave-to { max-height: 0; opacity: 0; padding-top: 0; padding-bottom: 0; }

.key-info-bar {
  display: flex; gap: 24px; margin-bottom: 20px;
}
.key-info-item {
  display: flex; align-items: center; gap: 8px;
  font-size: 13px; color: #6B7280;
}

/* ── Model Groups ── */
.model-groups { display: flex; flex-direction: column; gap: 16px; margin-bottom: 20px; }
.model-group-label {
  display: flex; align-items: center; gap: 8px;
  font-size: 12px; font-weight: 700; color: #9CA3AF;
  text-transform: uppercase; letter-spacing: 0.5px;
  margin-bottom: 8px;
}
.model-group-count {
  background: #F3F4F6; color: #6B7280;
  font-size: 10px; padding: 1px 7px; border-radius: 6px;
}
.model-group-list { display: flex; flex-direction: column; gap: 4px; }
.model-row {
  display: flex; align-items: center; justify-content: space-between;
  padding: 10px 14px; border-radius: 12px;
  transition: background 0.15s;
}
.model-row:hover { background: #F9FAFB; }
.model-row-default { background: #FAF5FF; }
.model-row-info { display: flex; align-items: center; gap: 10px; min-width: 0; }
.model-row-name { font-size: 14px; font-weight: 500; color: #111827; }
.model-row-id { font-size: 12px; color: #9CA3AF; font-family: ui-monospace, monospace; }
.model-row-actions { display: flex; align-items: center; gap: 6px; flex-shrink: 0; }
.model-default-tag { font-size: 12px; font-weight: 600; color: #7C3AED; }
.model-empty { font-size: 13px; color: #9CA3AF; text-align: center; padding: 16px; }

/* ── Cap Chips ── */
.cap-chip {
  display: inline-flex; align-items: center; gap: 4px;
  padding: 4px 10px; border-radius: 8px;
  font-size: 12px; font-weight: 600;
}
.cap-chip-sm {
  display: inline-flex; align-items: center; gap: 3px;
  padding: 3px 8px; border-radius: 6px;
  font-size: 11px; font-weight: 600;
}

/* ── Key Actions ── */
.key-actions {
  display: flex; align-items: center; gap: 6px;
  padding-top: 16px; border-top: 1px solid #F3F4F6;
}
.flex-1 { flex: 1; }

/* ── Logout ── */
.btn-logout {
  display: flex; align-items: center; justify-content: center; gap: 10px;
  width: 100%; padding: 14px; border-radius: 14px;
  font-size: 14px; font-weight: 600; color: #6B7280;
  background: #fff; border: 1.5px solid #E5E7EB;
  cursor: pointer; transition: all 0.2s;
}
.btn-logout:hover { color: #DC2626; border-color: #FCA5A5; background: #FEF2F2; }

/* ── Modal ── */
.modal-mask {
  position: fixed; inset: 0; z-index: 100;
  background: rgba(0,0,0,0.45); backdrop-filter: blur(4px);
  display: flex; align-items: flex-end; justify-content: center;
}
@media (min-width: 640px) { .modal-mask { align-items: center; } }
.modal-panel {
  background: #fff; border-radius: 20px 20px 0 0;
  width: 100%; max-height: 90vh; overflow-y: auto;
  box-shadow: 0 -8px 40px rgba(0,0,0,0.15);
}
@media (min-width: 640px) {
  .modal-panel { border-radius: 20px; width: 540px; max-width: 90vw; box-shadow: 0 16px 48px rgba(0,0,0,0.2); }
  .modal-panel-sm { width: 440px; }
}
.modal-header {
  display: flex; align-items: flex-start; justify-content: space-between;
  padding: 24px 28px 0;
}
.modal-title { font-size: 18px; font-weight: 700; color: #111827; }
.modal-subtitle { font-size: 13px; color: #9CA3AF; margin-top: 3px; }
.modal-body { padding: 24px 28px; display: flex; flex-direction: column; gap: 20px; }
.modal-footer {
  display: flex; align-items: center; justify-content: space-between;
  padding: 16px 28px 20px; border-top: 1px solid #F3F4F6;
  background: #FAFAFA; border-radius: 0 0 20px 20px;
}
@media (min-width: 640px) { .modal-footer { border-radius: 0 0 20px 20px; } }
.modal-footer-left { display: flex; gap: 8px; }
.modal-footer-right { display: flex; gap: 8px; }
.modal-enter-active, .modal-leave-active { transition: all 0.25s ease; }
.modal-enter-from, .modal-leave-to { opacity: 0; }
.modal-enter-from .modal-panel, .modal-leave-to .modal-panel { transform: translateY(20px); }

/* ── Form ── */
.form-group { display: flex; flex-direction: column; gap: 8px; }
.form-label { font-size: 13px; font-weight: 600; color: #374151; }
.form-input {
  height: 44px; padding: 0 16px;
  background: #F9FAFB; border: 1.5px solid #E5E7EB; border-radius: 12px;
  font-size: 14px; color: #111827; outline: none;
  transition: all 0.15s;
}
.form-input:focus { border-color: #A78BFA; background: #fff; box-shadow: 0 0 0 3px rgba(167,139,250,0.15); }
.form-input-mono { font-family: ui-monospace, monospace; }

.cap-toggle-group { display: flex; gap: 8px; flex-wrap: wrap; }
.cap-toggle {
  display: flex; align-items: center; gap: 8px;
  padding: 10px 16px; border-radius: 12px;
  font-size: 13px; font-weight: 600;
  background: #F9FAFB; border: 1.5px solid #E5E7EB;
  color: #9CA3AF; cursor: pointer; transition: all 0.15s;
}
.cap-toggle:hover { border-color: #D1D5DB; }
.cap-toggle-on { border-color: transparent; }
.cap-toggle-icon { font-size: 16px; }
.cap-toggle-check { margin-left: 2px; }

/* ── Alert ── */
.alert {
  display: flex; align-items: center; gap: 10px;
  padding: 12px 16px; border-radius: 12px; font-size: 13px;
}
.alert-ok { background: #ECFDF5; color: #059669; }
.alert-err { background: #FEF2F2; color: #DC2626; }
.alert-icon { font-size: 16px; }

/* ── Discover ── */
.discover-panel { border: 1.5px solid #E5E7EB; border-radius: 14px; overflow: hidden; }
.discover-header { padding: 12px 16px; background: #F9FAFB; display: flex; align-items: center; justify-content: space-between; }
.discover-title { font-size: 13px; font-weight: 600; color: #374151; }
.discover-hint { font-size: 11px; color: #9CA3AF; }
.discover-list { max-height: 220px; overflow-y: auto; }
.discover-item {
  display: flex; align-items: center; gap: 10px;
  padding: 10px 16px; cursor: pointer; transition: background 0.15s;
  border-top: 1px solid #F3F4F6;
}
.discover-item:hover { background: #FAF5FF; }
.discover-model-id { flex: 1; font-size: 13px; font-family: ui-monospace, monospace; color: #374151; }
.discover-add { font-size: 12px; font-weight: 600; color: #7C3AED; }

/* ── Spinner ── */
.spinner-sm { width: 14px; height: 14px; border: 2px solid #E5E7EB; border-top-color: #6B7280; border-radius: 50%; animation: spin 0.6s linear infinite; }
.spinner-white { border-color: rgba(255,255,255,0.3); border-top-color: #fff; }
.spinner-lg { width: 24px; height: 24px; border: 3px solid #E5E7EB; border-top-color: #7C3AED; border-radius: 50%; animation: spin 0.6s linear infinite; margin: 0 auto 12px; }
@keyframes spin { to { transform: rotate(360deg); } }

.fade-enter-active, .fade-leave-active { transition: all 0.2s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; transform: translateY(-4px); }
</style>
