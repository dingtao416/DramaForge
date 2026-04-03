<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { assetsApi } from '@/api/assets'
import type { CharacterDetail } from '@/types/character'
import EmptyState from '@/components/common/EmptyState.vue'

const router = useRouter()
const assets = ref<CharacterDetail[]>([])
const loading = ref(false)
const viewMode = ref<'grid' | 'list'>('grid')
const activeTab = ref<'assets' | 'characters'>('assets')

onMounted(async () => {
  loading.value = true
  try {
    const { data } = await assetsApi.listGlobal()
    assets.value = data
  } finally {
    loading.value = false
  }
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
  return new Date(dateStr).toLocaleString('zh-CN', {
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit',
  })
}
</script>

<template>
  <div class="min-h-screen bg-white">
    <!-- Top bar -->
    <div class="h-[56px] border-b border-gray-200 bg-white flex items-center px-8 shrink-0">
      <button
        class="w-8 h-8 rounded-lg flex items-center justify-center text-gray-400 hover:text-gray-700 hover:bg-gray-100 cursor-pointer transition-colors mr-3"
        @click="router.push('/')"
      >
        <svg width="18" height="18" viewBox="0 0 16 16" fill="none"><path d="M10 3L5 8L10 13" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>
      </button>
      <h1 class="text-[16px] font-bold text-gray-900">资产库</h1>
      <div class="flex-1" />
      <div class="flex items-center gap-3">
        <button class="btn btn-primary btn-sm">
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><line x1="7" y1="2" x2="7" y2="12" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/><line x1="2" y1="7" x2="12" y2="7" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>
          新增
        </button>
        <button class="btn btn-outline btn-sm" @click="handleRefresh">
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M2 7a5 5 0 019.9-.5M12 7a5 5 0 01-9.9.5" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/><path d="M12 3v3.5h-3.5M2 11V7.5h3.5" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/></svg>
          刷新
        </button>
      </div>
    </div>

    <div class="page-container-wide">
      <!-- Tabs + controls -->
      <div class="flex items-center gap-6 mb-8 border-b border-gray-200 pb-0">
        <button
          class="pb-3 text-[14px] font-medium border-b-2 -mb-px transition-colors"
          :class="activeTab === 'assets' ? 'border-gray-900 text-gray-900' : 'border-transparent text-gray-400 hover:text-gray-600'"
          @click="activeTab = 'assets'"
        >
          资产
        </button>
        <button
          class="pb-3 text-[14px] font-medium border-b-2 -mb-px transition-colors"
          :class="activeTab === 'characters' ? 'border-gray-900 text-gray-900' : 'border-transparent text-gray-400 hover:text-gray-600'"
          @click="activeTab = 'characters'"
        >
          人物角色
        </button>
        <div class="flex-1" />
        <span class="text-[12px] text-gray-400 pb-3">按时间倒序展示</span>
        <!-- View mode toggle -->
        <div class="flex border border-gray-200 rounded-lg overflow-hidden mb-3">
          <button
            class="w-8 h-7 flex items-center justify-center text-[12px] transition-colors"
            :class="viewMode === 'grid' ? 'bg-gray-100 text-gray-700' : 'text-gray-400 hover:bg-gray-50'"
            @click="viewMode = 'grid'"
          >
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><rect x="1" y="1" width="5" height="5" rx="1" stroke="currentColor" stroke-width="1.2"/><rect x="8" y="1" width="5" height="5" rx="1" stroke="currentColor" stroke-width="1.2"/><rect x="1" y="8" width="5" height="5" rx="1" stroke="currentColor" stroke-width="1.2"/><rect x="8" y="8" width="5" height="5" rx="1" stroke="currentColor" stroke-width="1.2"/></svg>
          </button>
          <button
            class="w-8 h-7 flex items-center justify-center text-[12px] transition-colors"
            :class="viewMode === 'list' ? 'bg-gray-100 text-gray-700' : 'text-gray-400 hover:bg-gray-50'"
            @click="viewMode = 'list'"
          >
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M2 3h10M2 7h10M2 11h10" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/></svg>
          </button>
        </div>
      </div>

      <!-- Loading -->
      <div v-if="loading" class="flex justify-center py-24">
        <div class="w-8 h-8 border-[3px] border-primary-500 border-t-transparent rounded-full animate-spin" />
      </div>

      <!-- Empty -->
      <EmptyState v-else-if="!assets.length" title="资产库为空" description="创作项目后生成的角色和场景将显示在这里" icon="🎨" />

      <!-- Grid view -->
      <div v-else-if="viewMode === 'grid'" class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-5">
        <div
          v-for="asset in assets"
          :key="asset.id"
          class="card overflow-hidden group hover:shadow-[0_4px_16px_rgba(0,0,0,0.08)] cursor-pointer transition-all"
        >
          <div class="aspect-square bg-gradient-to-br from-gray-50 to-gray-100 overflow-hidden">
            <img
              v-if="asset.reference_images?.[0]"
              :src="asset.reference_images[0]"
              :alt="asset.name"
              class="w-full h-full object-cover transition-transform group-hover:scale-105"
            />
            <div v-else class="w-full h-full flex items-center justify-center text-4xl text-gray-200">👤</div>
          </div>
          <div class="p-3">
            <div class="text-[13px] font-medium text-gray-800 truncate mb-1">{{ asset.name }}</div>
            <div class="text-[11px] text-gray-400">{{ formatDate(asset.created_at) }}</div>
          </div>
        </div>
      </div>

      <!-- List view -->
      <div v-else class="space-y-2">
        <div
          v-for="asset in assets"
          :key="asset.id"
          class="card p-3.5 flex items-center gap-4 hover:shadow-[0_2px_8px_rgba(0,0,0,0.04)] cursor-pointer transition-all"
        >
          <div class="w-12 h-12 bg-gray-100 rounded-[10px] overflow-hidden shrink-0">
            <img v-if="asset.reference_images?.[0]" :src="asset.reference_images[0]" class="w-full h-full object-cover" />
            <div v-else class="w-full h-full flex items-center justify-center text-lg text-gray-300">👤</div>
          </div>
          <div class="flex-1 min-w-0">
            <div class="text-[14px] font-medium text-gray-800 truncate">{{ asset.name }}</div>
            <div class="text-[12px] text-gray-400 mt-0.5">{{ formatDate(asset.created_at) }}</div>
          </div>
        </div>
      </div>

      <!-- Footer -->
      <div v-if="assets.length" class="text-center text-[12px] text-gray-400 mt-10 pb-8">已加载全部</div>
    </div>
  </div>
</template>