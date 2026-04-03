<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { assetsApi } from '@/api/assets'
import type { CharacterDetail } from '@/types/character'
import EmptyState from '@/components/common/EmptyState.vue'
import TopbarActions from '@/components/common/TopbarActions.vue'
import { useBillingStore } from '@/stores/billing'

const router = useRouter()
const billingStore = useBillingStore()

const assets = ref<CharacterDetail[]>([])
const loading = ref(false)
const viewMode = ref<'grid' | 'list'>('grid')
const activeTab = ref<'assets' | 'characters'>('assets')
const filterOpen = ref(false)
const filterType = ref<'all' | 'image' | 'video'>('all')

const filteredAssets = computed(() => {
  if (filterType.value === 'all') return assets.value
  return assets.value.filter(a => {
    if (filterType.value === 'video') return a.reference_images?.[0]?.endsWith('.mp4')
    return !a.reference_images?.[0]?.endsWith('.mp4')
  })
})

onMounted(async () => {
  loading.value = true
  try {
    const { data } = await assetsApi.listGlobal()
    assets.value = data
  } finally {
    loading.value = false
  }
  billingStore.fetchBalance()
})

async function handleRefresh() {
  loading.value = true
  try {
    const { data } = await assetsApi.listGlobal()
    assets.value = data
  } finally {
    loading.value = false
  }
}

function formatDate(dateStr: string) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const h = String(d.getHours()).padStart(2, '0')
  const min = String(d.getMinutes()).padStart(2, '0')
  const sec = String(d.getSeconds()).padStart(2, '0')
  return `${y}/${m}/${day} ${h}:${min}:${sec}`
}

function isVideo(asset: any) {
  const url = asset.reference_images?.[0] || ''
  return url.endsWith('.mp4') || url.endsWith('.webm') || url.endsWith('.mov')
}

function getAssetSource(asset: any) {
  return asset.source || '创作生成'
}

const showSubscribeSheet = ref(false)

function handleSubscribe() {
  showSubscribeSheet.value = true
}

// ── 新增下拉菜单 ──
const showAddMenu = ref(false)

function toggleAddMenu() {
  showAddMenu.value = !showAddMenu.value
}

// ── 上传资产 ──
const uploadInput = ref<HTMLInputElement | null>(null)

function handleUploadAsset() {
  showAddMenu.value = false
  uploadInput.value?.click()
}

async function onAssetFileSelected(e: Event) {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  input.value = ''
  // TODO: call upload API
  alert(`资产上传: ${file.name} (接口对接中)`)
  await handleRefresh()
}

// ── 新建角色弹窗 ──
const showCreateCharacter = ref(false)
const charForm = ref({
  name: '',
  description: '',
  gender: '',
  age: '',
})
const charImage = ref<File | null>(null)
const charImagePreview = ref('')
const charCreating = ref(false)

function openCreateCharacter() {
  showAddMenu.value = false
  charForm.value = { name: '', description: '', gender: '', age: '' }
  charImage.value = null
  charImagePreview.value = ''
  showCreateCharacter.value = true
}

function onCharImageSelect(e: Event) {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  input.value = ''
  charImage.value = file
  charImagePreview.value = URL.createObjectURL(file)
}

async function handleCreateCharacter() {
  if (!charForm.value.name.trim()) return
  charCreating.value = true
  try {
    // TODO: call create character API with FormData
    // const fd = new FormData()
    // fd.append('name', charForm.value.name)
    // fd.append('description', charForm.value.description)
    // fd.append('gender', charForm.value.gender)
    // fd.append('age', charForm.value.age)
    // if (charImage.value) fd.append('image', charImage.value)
    // await assetsApi.createCharacter(fd)
    await new Promise(r => setTimeout(r, 1000))
    showCreateCharacter.value = false
    await handleRefresh()
  } finally {
    charCreating.value = false
  }
}
</script>

<template>
  <div class="asset-page">
    <!-- ══════ Top Navigation Bar ══════ -->
    <header class="topbar">
      <div class="topbar-left">
        <button class="back-btn" @click="router.push('/')" title="返回首页">
          <svg width="18" height="18" viewBox="0 0 16 16" fill="none"><path d="M10 3L5 8L10 13" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>
        </button>
        <h2 class="topbar-page-title">资产库</h2>
      </div>
      <TopbarActions @subscribe="handleSubscribe" />
    </header>

    <!-- ══════ Page Content ══════ -->
    <main class="page-main">
      <!-- Title row -->
      <div class="title-row">
        <div class="title-left">
          <h1 class="page-title">资产库</h1>
          <div class="add-wrapper">
            <button class="add-btn" @click="toggleAddMenu">
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M7 1v12M1 7h12" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>
              新增
              <svg width="10" height="10" viewBox="0 0 10 10" fill="none"><path d="M3 4l2 2 2-2" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/></svg>
            </button>
            <!-- Dropdown -->
            <div v-if="showAddMenu" class="add-dropdown">
              <button class="add-dropdown-item" @click="handleUploadAsset">
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M8 2v8M5 5l3-3 3 3" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/><path d="M2 10v3a1 1 0 001 1h10a1 1 0 001-1v-3" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/></svg>
                上传资产
              </button>
              <button class="add-dropdown-item" @click="openCreateCharacter">
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><circle cx="8" cy="5.5" r="3" stroke="currentColor" stroke-width="1.3"/><path d="M2.5 14c0-3 2.5-5 5.5-5s5.5 2 5.5 5" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/></svg>
                新建角色
              </button>
            </div>
            <!-- Hidden file input for upload -->
            <input ref="uploadInput" type="file" accept="image/*,video/*" hidden @change="onAssetFileSelected" />
          </div>
        </div>
        <div class="title-right">
          <button class="action-btn" @click="handleRefresh">
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M2 7a5 5 0 019.9-.5M12 7a5 5 0 01-9.9.5" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/><path d="M12 3v3.5h-3.5M2 11V7.5h3.5" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/></svg>
            刷新
          </button>
          <div class="view-toggle">
            <button
              class="toggle-item"
              :class="{ active: viewMode === 'grid' }"
              @click="viewMode = 'grid'"
            >
              <svg width="15" height="15" viewBox="0 0 15 15" fill="none"><rect x="1.5" y="1.5" width="5" height="5" rx="1.2" stroke="currentColor" stroke-width="1.2"/><rect x="8.5" y="1.5" width="5" height="5" rx="1.2" stroke="currentColor" stroke-width="1.2"/><rect x="1.5" y="8.5" width="5" height="5" rx="1.2" stroke="currentColor" stroke-width="1.2"/><rect x="8.5" y="8.5" width="5" height="5" rx="1.2" stroke="currentColor" stroke-width="1.2"/></svg>
            </button>
            <button
              class="toggle-item"
              :class="{ active: viewMode === 'list' }"
              @click="viewMode = 'list'"
            >
              <svg width="15" height="15" viewBox="0 0 15 15" fill="none"><path d="M2 3.5h11M2 7.5h11M2 11.5h11" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/></svg>
            </button>
          </div>
        </div>
      </div>

      <!-- Tabs + filter row -->
      <div class="tabs-row">
        <div class="tabs-left">
          <button
            class="tab-item"
            :class="{ active: activeTab === 'assets' }"
            @click="activeTab = 'assets'"
          >
            <svg width="15" height="15" viewBox="0 0 15 15" fill="none"><rect x="1.5" y="1.5" width="12" height="12" rx="2" stroke="currentColor" stroke-width="1.2"/><circle cx="5.5" cy="5.5" r="1.5" stroke="currentColor" stroke-width="1"/><path d="M1.5 11l3.5-4.5 2 2 3-3.5 3.5 4.5" stroke="currentColor" stroke-width="1.1" stroke-linecap="round" stroke-linejoin="round"/></svg>
            资产
          </button>
          <button
            class="tab-item"
            :class="{ active: activeTab === 'characters' }"
            @click="activeTab = 'characters'"
          >
            <svg width="15" height="15" viewBox="0 0 15 15" fill="none"><circle cx="7.5" cy="4.5" r="2.8" stroke="currentColor" stroke-width="1.2"/><path d="M2.5 13.5c0-2.8 2.2-4.5 5-4.5s5 1.7 5 4.5" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/></svg>
            人物角色
          </button>
        </div>
        <div class="tabs-right">
          <span class="sort-label">按时间倒序展示</span>
          <div class="filter-dropdown" @click="filterOpen = !filterOpen">
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M2 3h10M4 7h6M6 11h2" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/></svg>
            筛选
            <svg width="10" height="10" viewBox="0 0 10 10" fill="none"><path d="M2.5 4l2.5 2.5L7.5 4" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/></svg>
            <!-- Dropdown -->
            <div v-if="filterOpen" class="filter-menu" @click.stop>
              <button :class="{ selected: filterType === 'all' }" @click="filterType = 'all'; filterOpen = false">全部</button>
              <button :class="{ selected: filterType === 'image' }" @click="filterType = 'image'; filterOpen = false">图片</button>
              <button :class="{ selected: filterType === 'video' }" @click="filterType = 'video'; filterOpen = false">视频</button>
            </div>
          </div>
        </div>
      </div>

      <!-- ══════ Loading ══════ -->
      <div v-if="loading" class="loading-area">
        <div class="spinner" />
      </div>

      <!-- ══════ Empty ══════ -->
      <EmptyState v-else-if="!filteredAssets.length" title="资产库为空" description="创作项目后生成的角色和场景将显示在这里" icon="🎨" />

      <!-- ══════ Grid View ══════ -->
      <div v-else-if="viewMode === 'grid'" class="asset-grid">
        <div
          v-for="asset in filteredAssets"
          :key="asset.id"
          class="asset-card"
        >
          <!-- Thumbnail area -->
          <div class="card-thumb">
            <img
              v-if="asset.reference_images?.[0] && !isVideo(asset)"
              :src="asset.reference_images[0]"
              :alt="asset.name"
              class="thumb-img"
            />
            <div v-else-if="isVideo(asset)" class="thumb-video">
              <video :src="asset.reference_images?.[0]" class="thumb-img" muted />
              <span class="video-badge">0:10</span>
            </div>
            <div v-else class="thumb-placeholder">
              <svg width="32" height="32" viewBox="0 0 32 32" fill="none"><rect x="4" y="4" width="24" height="24" rx="4" stroke="#d4d4d8" stroke-width="1.5"/><circle cx="12" cy="12" r="3" stroke="#d4d4d8" stroke-width="1.3"/><path d="M4 24l6-8 4 4 6-6 8 10" stroke="#d4d4d8" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/></svg>
            </div>

            <!-- Action buttons overlay -->
            <div class="card-actions">
              <button class="card-action-btn" title="添加到项目">
                <svg width="13" height="13" viewBox="0 0 13 13" fill="none"><line x1="6.5" y1="2" x2="6.5" y2="11" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/><line x1="2" y1="6.5" x2="11" y2="6.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
              </button>
              <button class="card-action-btn" title="标签">
                <svg width="13" height="13" viewBox="0 0 13 13" fill="none"><path d="M1.5 7.2l4.3 4.3a1 1 0 001.4 0l4.3-4.3a1 1 0 000-1.4L7.2 1.5A1 1 0 006.5 1.2H2.5a1 1 0 00-1 1v4a1 1 0 00.3.7z" stroke="currentColor" stroke-width="1.1" stroke-linecap="round"/><circle cx="4.2" cy="4.2" r="0.7" fill="currentColor"/></svg>
              </button>
              <button class="card-action-btn danger" title="删除">
                <svg width="13" height="13" viewBox="0 0 13 13" fill="none"><path d="M2 3.5h9M4.5 3.5V2.5a1 1 0 011-1h2a1 1 0 011 1v1M5.5 6v3.5M7.5 6v3.5M3.5 3.5l.5 7a1 1 0 001 1h3a1 1 0 001-1l.5-7" stroke="currentColor" stroke-width="1.1" stroke-linecap="round" stroke-linejoin="round"/></svg>
              </button>
            </div>
          </div>

          <!-- Info area -->
          <div class="card-info">
            <span class="card-source">{{ getAssetSource(asset) }}</span>
            <span class="card-date">{{ formatDate(asset.created_at) }}</span>
          </div>
        </div>
      </div>

      <!-- ══════ List View ══════ -->
      <div v-else class="asset-list">
        <div
          v-for="asset in filteredAssets"
          :key="asset.id"
          class="list-item"
        >
          <div class="list-thumb">
            <img v-if="asset.reference_images?.[0]" :src="asset.reference_images[0]" class="list-thumb-img" />
            <div v-else class="list-thumb-placeholder">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none"><rect x="2" y="2" width="16" height="16" rx="3" stroke="#d4d4d8" stroke-width="1.3"/></svg>
            </div>
            <span v-if="isVideo(asset)" class="video-badge-sm">0:10</span>
          </div>
          <div class="list-info">
            <div class="list-name">{{ asset.name }}</div>
            <div class="list-meta">
              <span class="list-source">{{ getAssetSource(asset) }}</span>
              <span class="list-date">{{ formatDate(asset.created_at) }}</span>
            </div>
          </div>
          <div class="list-actions">
            <button class="card-action-btn" title="添加到项目">
              <svg width="13" height="13" viewBox="0 0 13 13" fill="none"><line x1="6.5" y1="2" x2="6.5" y2="11" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/><line x1="2" y1="6.5" x2="11" y2="6.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
            </button>
            <button class="card-action-btn" title="标签">
              <svg width="13" height="13" viewBox="0 0 13 13" fill="none"><path d="M1.5 7.2l4.3 4.3a1 1 0 001.4 0l4.3-4.3a1 1 0 000-1.4L7.2 1.5A1 1 0 006.5 1.2H2.5a1 1 0 00-1 1v4a1 1 0 00.3.7z" stroke="currentColor" stroke-width="1.1" stroke-linecap="round"/><circle cx="4.2" cy="4.2" r="0.7" fill="currentColor"/></svg>
            </button>
            <button class="card-action-btn danger" title="删除">
              <svg width="13" height="13" viewBox="0 0 13 13" fill="none"><path d="M2 3.5h9M4.5 3.5V2.5a1 1 0 011-1h2a1 1 0 011 1v1M5.5 6v3.5M7.5 6v3.5M3.5 3.5l.5 7a1 1 0 001 1h3a1 1 0 001-1l.5-7" stroke="currentColor" stroke-width="1.1" stroke-linecap="round" stroke-linejoin="round"/></svg>
            </button>
          </div>
        </div>
      </div>

      <!-- Footer -->
      <div v-if="filteredAssets.length" class="page-footer">已加载全部</div>
    </main>

    <!-- ═══════ 新建角色弹窗 ═══════ -->
    <Teleport to="body">
      <div v-if="showCreateCharacter" class="modal-overlay" @click.self="showCreateCharacter = false">
        <div class="modal-box">
          <!-- Header -->
          <div class="modal-header">
            <h2 class="modal-title">新建角色</h2>
            <button class="modal-close" @click="showCreateCharacter = false">✕</button>
          </div>

          <!-- Body: two columns -->
          <div class="modal-body">
            <!-- Left: Form -->
            <div class="modal-form">
              <!-- 角色名称 -->
              <div class="form-group">
                <label class="form-label">角色名称</label>
                <input
                  v-model="charForm.name"
                  type="text"
                  class="form-input"
                  placeholder="角色名称"
                />
              </div>

              <!-- 角色描述 -->
              <div class="form-group">
                <label class="form-label">角色描述</label>
                <div class="textarea-wrap">
                  <textarea
                    v-model="charForm.description"
                    class="form-textarea"
                    placeholder="描述角色特征或用途"
                    maxlength="200"
                    rows="4"
                  />
                  <span class="textarea-count">{{ charForm.description.length }}/200</span>
                </div>
                <span class="form-hint">用于标记和搜索角色，建议填写易于识别的描述</span>
              </div>

              <!-- 性别 -->
              <div class="form-group">
                <label class="form-label">性别</label>
                <select v-model="charForm.gender" class="form-select">
                  <option value="" disabled>选择性别</option>
                  <option value="male">男</option>
                  <option value="female">女</option>
                  <option value="other">其他</option>
                </select>
              </div>

              <!-- 年龄 -->
              <div class="form-group">
                <label class="form-label">年龄</label>
                <input
                  v-model="charForm.age"
                  type="text"
                  class="form-input"
                  placeholder="角色年龄"
                />
              </div>

              <!-- 角色图片 -->
              <div class="form-group">
                <label class="form-label">角色图片</label>
                <label class="form-upload-btn">
                  选择图片
                  <input type="file" accept="image/*" hidden @change="onCharImageSelect" />
                </label>
                <span class="form-hint">选择图片后可预览，提交时自动上传</span>
              </div>
            </div>

            <!-- Right: Preview -->
            <div class="modal-preview">
              <div class="preview-label">新增预览</div>
              <div class="preview-box">
                <img v-if="charImagePreview" :src="charImagePreview" class="preview-img" />
                <div v-else class="preview-empty">
                  <svg width="28" height="28" viewBox="0 0 28 28" fill="none"><rect x="3" y="3" width="22" height="22" rx="4" stroke="#d4d4d8" stroke-width="1.4"/><circle cx="10" cy="11" r="2.5" stroke="#d4d4d8" stroke-width="1.2"/><path d="M3 22l5-6 3.5 3 4.5-5.5L24 22" stroke="#d4d4d8" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/></svg>
                  <span>暂无封面</span>
                </div>
              </div>
              <div class="preview-hint">选择图片后实时查看角色素材预览</div>
            </div>
          </div>

          <!-- Footer -->
          <div class="modal-footer">
            <button class="modal-btn-cancel" @click="showCreateCharacter = false">取消</button>
            <button
              class="modal-btn-submit"
              :disabled="!charForm.name.trim() || charCreating"
              @click="handleCreateCharacter"
            >
              {{ charCreating ? '创建中...' : '创建' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- 点击其他区域关闭新增下拉 -->
    <div v-if="showAddMenu" class="backdrop-close" @click="showAddMenu = false" />
  </div>
</template>

<style scoped>
/* ══════════════════════════════════════════════════════
   Layout
   ══════════════════════════════════════════════════════ */
.asset-page {
  min-height: 100vh;
  background: #fff;
}

/* ── Top Bar ── */
.topbar {
  height: 56px;
  border-bottom: 1px solid #f0f0f0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 28px;
  background: #fff;
  position: sticky;
  top: 0;
  z-index: 50;
}

.topbar-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.back-btn {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  border: none;
  background: transparent;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #999;
  cursor: pointer;
  transition: all 0.15s;
}
.back-btn:hover {
  background: #f5f5f5;
  color: #333;
}

.topbar-page-title {
  font-size: 15px;
  font-weight: 700;
  color: #1a1a1a;
  margin: 0;
  letter-spacing: -0.2px;
}

/* ── Page Main ── */
.page-main {
  max-width: 1440px;
  margin: 0 auto;
  padding: 28px 40px 60px;
}

/* ── Title Row ── */
.title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
}

.title-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.page-title {
  font-size: 26px;
  font-weight: 800;
  color: #1a1a1a;
  letter-spacing: -0.5px;
  margin: 0;
}

.add-wrapper {
  position: relative;
}

.add-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 18px;
  background: #1a1a1a;
  color: #fff;
  border: none;
  border-radius: 22px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s;
}
.add-btn:hover {
  background: #333;
}

.add-dropdown {
  position: absolute;
  top: calc(100% + 6px);
  left: 0;
  background: #fff;
  border: 1px solid #e5e5e5;
  border-radius: 12px;
  box-shadow: 0 4px 24px rgba(0,0,0,0.1);
  padding: 6px;
  z-index: 20;
  min-width: 160px;
}
.add-dropdown-item {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 10px 14px;
  background: none;
  border: none;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  color: #333;
  cursor: pointer;
  transition: background 0.12s;
}
.add-dropdown-item:hover {
  background: #f5f5f5;
}
.add-dropdown-item svg {
  color: #888;
}

.backdrop-close {
  position: fixed;
  inset: 0;
  z-index: 15;
}

.title-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 6px 14px;
  background: transparent;
  border: none;
  color: #666;
  font-size: 13px;
  cursor: pointer;
  border-radius: 8px;
  transition: all 0.15s;
}
.action-btn:hover {
  background: #f5f5f5;
  color: #333;
}

.view-toggle {
  display: flex;
  border: 1px solid #e5e5e5;
  border-radius: 10px;
  overflow: hidden;
}
.toggle-item {
  width: 34px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fff;
  border: none;
  color: #bbb;
  cursor: pointer;
  transition: all 0.15s;
}
.toggle-item.active {
  background: #f5f5f5;
  color: #333;
}
.toggle-item:hover:not(.active) {
  color: #666;
}

/* ── Tabs Row ── */
.tabs-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #f0f0f0;
  margin-bottom: 24px;
}

.tabs-left {
  display: flex;
  gap: 0;
}

.tab-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 12px 20px 12px 16px;
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  font-size: 14px;
  font-weight: 500;
  color: #999;
  cursor: pointer;
  transition: all 0.15s;
  margin-bottom: -1px;
}
.tab-item.active {
  color: #1a1a1a;
  border-bottom-color: #1a1a1a;
}
.tab-item:hover:not(.active) {
  color: #666;
}

.tabs-right {
  display: flex;
  align-items: center;
  gap: 16px;
  padding-bottom: 10px;
}

.sort-label {
  font-size: 12px;
  color: #bbb;
}

.filter-dropdown {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 5px 12px;
  border: 1px solid #e5e5e5;
  border-radius: 8px;
  font-size: 13px;
  color: #666;
  cursor: pointer;
  position: relative;
  transition: all 0.15s;
  background: #fff;
}
.filter-dropdown:hover {
  border-color: #ccc;
}

.filter-menu {
  position: absolute;
  top: calc(100% + 6px);
  right: 0;
  background: #fff;
  border: 1px solid #e5e5e5;
  border-radius: 10px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.08);
  padding: 6px;
  z-index: 10;
  min-width: 100px;
}
.filter-menu button {
  display: block;
  width: 100%;
  padding: 7px 14px;
  text-align: left;
  background: none;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  color: #666;
  cursor: pointer;
  transition: background 0.1s;
}
.filter-menu button:hover {
  background: #f5f5f5;
}
.filter-menu button.selected {
  color: #7c3aed;
  font-weight: 600;
  background: #F9F5FF;
}

/* ══════════════════════════════════════════════════════
   Asset Grid
   ══════════════════════════════════════════════════════ */
.asset-grid {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 18px;
}

@media (max-width: 1280px) { .asset-grid { grid-template-columns: repeat(5, 1fr); } }
@media (max-width: 1024px) { .asset-grid { grid-template-columns: repeat(4, 1fr); } }
@media (max-width: 768px)  { .asset-grid { grid-template-columns: repeat(3, 1fr); } }
@media (max-width: 520px)  { .asset-grid { grid-template-columns: repeat(2, 1fr); } }

.asset-card {
  border: 1px solid #ececec;
  border-radius: 12px;
  overflow: hidden;
  background: #fff;
  transition: all 0.2s;
}
.asset-card:hover {
  border-color: #ddd;
  box-shadow: 0 2px 12px rgba(0,0,0,0.06);
}

/* ── Thumbnail ── */
.card-thumb {
  position: relative;
  aspect-ratio: 1 / 1;
  background: #fafafa;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.thumb-img {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}

.thumb-video {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}

.thumb-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  color: #e5e5e5;
}

.video-badge {
  position: absolute;
  bottom: 8px;
  left: 8px;
  background: rgba(0,0,0,0.65);
  color: #fff;
  font-size: 11px;
  font-weight: 600;
  padding: 2px 7px;
  border-radius: 4px;
  letter-spacing: 0.3px;
}
.video-badge-sm {
  position: absolute;
  bottom: 4px;
  left: 4px;
  background: rgba(0,0,0,0.6);
  color: #fff;
  font-size: 10px;
  padding: 1px 5px;
  border-radius: 3px;
}

/* ── Card Actions (overlay on hover) ── */
.card-actions {
  position: absolute;
  bottom: 8px;
  right: 8px;
  display: flex;
  gap: 4px;
  opacity: 0;
  transform: translateY(4px);
  transition: all 0.2s;
}
.asset-card:hover .card-actions,
.list-item:hover .list-actions {
  opacity: 1;
  transform: translateY(0);
}

.card-action-btn {
  width: 26px;
  height: 26px;
  border-radius: 7px;
  border: none;
  background: rgba(255,255,255,0.92);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #555;
  cursor: pointer;
  transition: all 0.15s;
  box-shadow: 0 1px 4px rgba(0,0,0,0.1);
}
.card-action-btn:hover {
  background: #fff;
  color: #333;
  box-shadow: 0 2px 8px rgba(0,0,0,0.12);
}
.card-action-btn.danger:hover {
  color: #ef4444;
  background: #FEF2F2;
}

/* ── Card Info ── */
.card-info {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
}

.card-source {
  font-size: 12px;
  color: #888;
}

.card-date {
  font-size: 11px;
  color: #bbb;
}

/* ══════════════════════════════════════════════════════
   List View
   ══════════════════════════════════════════════════════ */
.asset-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.list-item {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 10px 14px;
  border: 1px solid #f0f0f0;
  border-radius: 12px;
  transition: all 0.15s;
  cursor: pointer;
}
.list-item:hover {
  background: #fafafa;
  border-color: #e5e5e5;
}

.list-thumb {
  width: 52px;
  height: 52px;
  border-radius: 10px;
  overflow: hidden;
  background: #f5f5f5;
  flex-shrink: 0;
  position: relative;
}
.list-thumb-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.list-thumb-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.list-info {
  flex: 1;
  min-width: 0;
}
.list-name {
  font-size: 14px;
  font-weight: 600;
  color: #333;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.list-meta {
  display: flex;
  gap: 12px;
  margin-top: 3px;
}
.list-source {
  font-size: 12px;
  color: #999;
}
.list-date {
  font-size: 12px;
  color: #ccc;
}

.list-actions {
  display: flex;
  gap: 4px;
  opacity: 0;
  transition: opacity 0.2s;
}
.list-item:hover .list-actions {
  opacity: 1;
}

/* ══════════════════════════════════════════════════════
   Misc
   ══════════════════════════════════════════════════════ */
.loading-area {
  display: flex;
  justify-content: center;
  padding: 80px 0;
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #7c3aed;
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.page-footer {
  text-align: center;
  font-size: 12px;
  color: #ccc;
  margin-top: 48px;
  padding-bottom: 20px;
}

/* ══════════════════════════════════════════════════════
   Create Character Modal
   ══════════════════════════════════════════════════════ */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 24px;
}

.modal-box {
  background: #fff;
  border-radius: 20px;
  width: 100%;
  max-width: 720px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 20px 60px rgba(0,0,0,0.15);
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24px 28px 0;
}
.modal-title {
  font-size: 20px;
  font-weight: 800;
  color: #1a1a1a;
  margin: 0;
}
.modal-close {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  border: none;
  background: transparent;
  color: #999;
  font-size: 16px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s;
}
.modal-close:hover { background: #f5f5f5; color: #333; }

.modal-body {
  display: flex;
  gap: 32px;
  padding: 24px 28px;
}

.modal-form {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 18px;
  min-width: 0;
}

/* ── Form Elements ── */
.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.form-label {
  font-size: 13px;
  font-weight: 700;
  color: #1a1a1a;
}
.form-input {
  height: 42px;
  padding: 0 14px;
  border: 1.5px solid #e5e5e5;
  border-radius: 10px;
  font-size: 14px;
  color: #333;
  outline: none;
  transition: border-color 0.15s;
  font-family: inherit;
}
.form-input::placeholder { color: #ccc; }
.form-input:focus { border-color: #4f46e5; }

.textarea-wrap {
  position: relative;
}
.form-textarea {
  width: 100%;
  padding: 12px 14px;
  border: 1.5px solid #e5e5e5;
  border-radius: 10px;
  font-size: 14px;
  color: #333;
  outline: none;
  resize: vertical;
  font-family: inherit;
  line-height: 1.5;
  transition: border-color 0.15s;
}
.form-textarea::placeholder { color: #ccc; }
.form-textarea:focus { border-color: #4f46e5; }
.textarea-count {
  position: absolute;
  bottom: 10px;
  right: 14px;
  font-size: 11px;
  color: #ccc;
}

.form-hint {
  font-size: 12px;
  color: #bbb;
}

.form-select {
  height: 42px;
  padding: 0 14px;
  border: 1.5px solid #e5e5e5;
  border-radius: 10px;
  font-size: 14px;
  color: #333;
  outline: none;
  background: #fff;
  cursor: pointer;
  font-family: inherit;
  appearance: auto;
  transition: border-color 0.15s;
}
.form-select:focus { border-color: #4f46e5; }

.form-upload-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 42px;
  border: 1.5px solid #e5e5e5;
  border-radius: 10px;
  background: #fafafa;
  font-size: 14px;
  font-weight: 600;
  color: #333;
  cursor: pointer;
  transition: all 0.15s;
}
.form-upload-btn:hover { background: #f0f0f0; border-color: #ccc; }

/* ── Preview Panel ── */
.modal-preview {
  width: 220px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.preview-label {
  font-size: 13px;
  font-weight: 700;
  color: #1a1a1a;
}
.preview-box {
  width: 220px;
  height: 220px;
  border: 1px solid #e5e5e5;
  border-radius: 12px;
  overflow: hidden;
  background: #fafafa;
  display: flex;
  align-items: center;
  justify-content: center;
}
.preview-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.preview-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  color: #ccc;
  font-size: 13px;
}
.preview-hint {
  font-size: 12px;
  color: #bbb;
  text-align: center;
}

/* ── Footer ── */
.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 0 28px 24px;
}
.modal-btn-cancel {
  padding: 10px 24px;
  border: 1px solid #e5e5e5;
  border-radius: 10px;
  background: #fff;
  font-size: 14px;
  font-weight: 600;
  color: #666;
  cursor: pointer;
  transition: all 0.15s;
}
.modal-btn-cancel:hover { background: #f5f5f5; }

.modal-btn-submit {
  padding: 10px 28px;
  border: none;
  border-radius: 10px;
  background: #1a1a1a;
  color: #fff;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s;
}
.modal-btn-submit:hover { background: #333; }
.modal-btn-submit:disabled { opacity: 0.4; cursor: not-allowed; }
</style>
