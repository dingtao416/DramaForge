<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { projectsApi } from '@/api/projects'
import { VideoStyleLabel, DramaGenreLabel, ProjectStepLabel } from '@/types/enums'
import type { ProjectList } from '@/types/project'
import EmptyState from '@/components/common/EmptyState.vue'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'

const router = useRouter()
const projects = ref<ProjectList[]>([])
const loading = ref(false)
const duplicatingId = ref<number | null>(null)

// ── Rename state ──
const editingId = ref<number | null>(null)
const editTitle = ref('')
const editInputRef = ref<HTMLInputElement | null>(null)

// ── Delete state ──
const showDeleteConfirm = ref(false)
const deletingProject = ref<ProjectList | null>(null)
const showDeleteAllConfirm = ref(false)
const deleting = ref(false)

// ── Toast ──
const toastMsg = ref('')
const toastType = ref<'success' | 'error'>('success')
let toastTimer: ReturnType<typeof setTimeout> | null = null
function showToast(msg: string, type: 'success' | 'error' = 'success') {
  toastMsg.value = msg; toastType.value = type
  if (toastTimer) clearTimeout(toastTimer)
  toastTimer = setTimeout(() => { toastMsg.value = '' }, 3000)
}

async function refreshList() {
  const { data } = await projectsApi.list()
  projects.value = data
}

onMounted(async () => {
  loading.value = true
  try { await refreshList() } finally { loading.value = false }
})

// ── Rename ──
function startRename(p: ProjectList) {
  editingId.value = p.id
  editTitle.value = p.title
  nextTick(() => editInputRef.value?.focus())
}
async function saveRename(id: number) {
  const title = editTitle.value.trim()
  if (!title) { cancelRename(); return }
  try {
    await projectsApi.update(id, { title })
    await refreshList()
    showToast('标题已修改')
  } catch { showToast('修改失败', 'error') }
  editingId.value = null
}
function cancelRename() { editingId.value = null }

// ── Delete single ──
function confirmDelete(p: ProjectList) {
  deletingProject.value = p
  showDeleteConfirm.value = true
}
async function handleDelete() {
  if (!deletingProject.value) return
  deleting.value = true
  try {
    await projectsApi.delete(deletingProject.value.id)
    await refreshList()
    showToast(`「${deletingProject.value.title}」已删除`)
  } catch { showToast('删除失败', 'error') }
  showDeleteConfirm.value = false
  deletingProject.value = null
  deleting.value = false
}

// ── Delete all ──
async function handleDeleteAll() {
  deleting.value = true
  let count = 0
  for (const p of projects.value) {
    try { await projectsApi.delete(p.id); count++ } catch { /* skip */ }
  }
  await refreshList()
  showToast(`已删除 ${count} 个项目`)
  showDeleteAllConfirm.value = false
  deleting.value = false
}

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}

async function handleDuplicate(id: number) {
  duplicatingId.value = id
  try { await projectsApi.duplicate(id); await refreshList() }
  catch { showToast('复制失败', 'error') }
  finally { duplicatingId.value = null }
}
</script>

<template>
  <div class="page-container-wide">
    <!-- Header -->
    <div class="flex items-center justify-between mb-8">
      <div>
        <h1 class="page-title">我的项目</h1>
        <p class="page-subtitle">管理你的短剧创作项目</p>
      </div>
      <div class="flex items-center gap-3">
        <!-- 删除全部 -->
        <button
          v-if="projects.length"
          class="btn btn-outline text-error border-[#E74C3C] hover:bg-[rgba(231,76,60,0.06)]"
          @click="showDeleteAllConfirm = true"
        >
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M2 4h10M5 4V2.5a.5.5 0 01.5-.5h3a.5.5 0 01.5.5V4M11 4v6.5a1.5 1.5 0 01-1.5 1.5h-5A1.5 1.5 0 013 10.5V4" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/></svg>
          删除全部
        </button>
        <button class="btn btn-primary" @click="router.push('/')">
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><line x1="7" y1="2" x2="7" y2="12" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/><line x1="2" y1="7" x2="12" y2="7" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>
          新建项目
        </button>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex justify-center py-24">
      <div class="w-8 h-8 border-[3px] border-primary-500 border-t-transparent rounded-[2px] animate-spin" />
    </div>

    <!-- Empty -->
    <EmptyState
      v-else-if="!projects.length"
      title="还没有项目"
      description="点击上方按钮创建你的第一个短剧项目"
      icon="🎬"
    />

    <!-- Grid -->
    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
      <div
        v-for="p in projects"
        :key="p.id"
        class="card overflow-hidden group transition-all relative"
        :class="editingId === p.id ? 'cursor-default' : 'cursor-pointer'"
        @click="editingId === p.id ? undefined : router.push(`/projects/${p.id}`)"
      >
        <!-- Thumbnail -->
        <div class="h-[140px] bg-gradient-to-br from-[#FDF4D8] to-[#FEF9E7] flex items-center justify-center text-4xl group-hover:from-[rgba(232,163,23,0.08)] group-hover:to-[rgba(232,163,23,0.15)] transition-colors">
          🎬
        </div>

        <div class="p-4">
          <div class="flex items-center justify-between mb-2">
            <!-- Title (inline-edit or display) -->
            <div class="flex-1 min-w-0 mr-2">
              <input
                v-if="editingId === p.id"
                ref="editInputRef"
                v-model="editTitle"
                class="w-full text-[14px] font-semibold text-gray-900 border-2 border-[#E8A317] rounded-[2px] px-2 py-0.5 outline-none bg-[#FEF9E7]"
                style="font-family: 'Press Start 2P', monospace; font-size: 10px;"
                @keydown.enter="saveRename(p.id)"
                @keydown.escape="cancelRename()"
                @blur="saveRename(p.id)"
                @click.stop
              />
              <h3
                v-else
                class="text-[14px] font-semibold text-gray-900 truncate hover:text-[#E8A317] transition-colors"
                @click.stop="startRename(p)"
                title="点击修改标题"
              >{{ p.title }}</h3>
            </div>

            <!-- Action buttons -->
            <div class="flex items-center gap-1 shrink-0">
              <!-- Duplicate -->
              <button
                class="action-btn"
                :disabled="duplicatingId === p.id"
                title="复制项目"
                @click.stop="handleDuplicate(p.id)"
              >
                <svg v-if="duplicatingId === p.id" class="animate-spin" width="14" height="14" viewBox="0 0 14 14" fill="none">
                  <circle cx="7" cy="7" r="5.5" stroke="currentColor" stroke-width="1.5" opacity="0.3"/>
                  <path d="M7 1.5a5.5 5.5 0 015.1 3.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                </svg>
                <svg v-else width="14" height="14" viewBox="0 0 14 14" fill="none">
                  <rect x="4" y="4" width="8" height="8" rx="1.5" stroke="currentColor" stroke-width="1.2"/>
                  <path d="M2 10V2.5A.5.5 0 012.5 2H10" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
                </svg>
              </button>
              <!-- Delete -->
              <button
                class="action-btn action-btn-delete"
                title="删除项目"
                @click.stop="confirmDelete(p)"
              >
                <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                  <path d="M2.5 4h9M5 4V2.5a.5.5 0 01.5-.5h3a.5.5 0 01.5.5V4M10.5 4v6a2 2 0 01-2 2h-3a2 2 0 01-2-2V4" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </button>
            </div>
          </div>

          <div class="flex items-center gap-2 mb-3">
            <span class="badge badge-primary">{{ VideoStyleLabel[p.style] }}</span>
            <span class="badge" style="background:#FDF4D8;color:#6B5D40">{{ DramaGenreLabel[p.genre] }}</span>
          </div>

          <div class="flex items-center justify-between text-[12px] text-gray-400">
            <span class="flex items-center gap-1">
              <svg width="12" height="12" viewBox="0 0 12 12" fill="none"><circle cx="6" cy="6" r="5" stroke="currentColor" stroke-width="1"/><path d="M6 3v3l2 1" stroke="currentColor" stroke-width="1" stroke-linecap="round"/></svg>
              {{ formatDate(p.created_at) }}
            </span>
            <span class="px-2 py-0.5 rounded-[2px] bg-[#FDF4D8] text-gray-500 text-[11px]">{{ ProjectStepLabel[p.status] }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- ═══ Confirm: Delete single ═══ -->
    <ConfirmDialog
      :visible="showDeleteConfirm"
      title="删除项目"
      :message="`确定要删除「${deletingProject?.title || ''}」吗？此操作无法撤销。`"
      confirm-text="确认删除"
      danger
      @confirm="handleDelete"
      @cancel="showDeleteConfirm = false"
    />

    <!-- ═══ Confirm: Delete all ═══ -->
    <ConfirmDialog
      :visible="showDeleteAllConfirm"
      title="删除全部"
      :message="`确定要删除全部 ${projects.length} 个项目吗？此操作无法撤销，请谨慎操作。`"
      confirm-text="全部删除"
      danger
      @confirm="handleDeleteAll"
      @cancel="showDeleteAllConfirm = false"
    />

    <!-- ═══ Toast ═══ -->
    <Transition name="fade">
      <div
        v-if="toastMsg"
        class="fixed bottom-8 left-1/2 -translate-x-1/2 z-[200] px-5 py-3 rounded-[2px] text-[13px] font-semibold border-2"
        :class="toastType === 'success'
          ? 'bg-[#2D2515] text-[#2ECC71] border-[#1E8449]'
          : 'bg-[#2D2515] text-[#E74C3C] border-[#C0392B]'"
        style="box-shadow: 4px 4px 0 0 rgba(0,0,0,0.2);"
      >
        {{ toastMsg }}
      </div>
    </Transition>
  </div>
</template>

<style scoped>
/* ── Action buttons (hover-visible) ── */
.action-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: none;
  background: none;
  cursor: pointer;
  border-radius: 2px;
  color: #A89870;
  transition: all 0.15s;
  flex-shrink: 0;
  opacity: 0;
}
.group:hover .action-btn { opacity: 1; }
.action-btn:hover {
  background: #FDF4D8;
  color: #6B5D40;
}
.action-btn:disabled {
  opacity: 1;
  cursor: not-allowed;
}
.action-btn-delete:hover {
  background: rgba(231, 76, 60, 0.1);
  color: #E74C3C;
}
</style>
