<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { assetsApi } from '@/api/assets'
import type { CharacterDetail } from '@/types/character'
import EmptyState from '@/components/common/EmptyState.vue'

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

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleString('zh-CN', {
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', second: '2-digit',
  })
}
</script>

<template>
  <div class="max-w-6xl mx-auto px-6 py-8">
    <!-- Header (参考截图13: 资产库  新增  刷新  网格/列表) -->
    <div class="flex items-center gap-4 mb-6">
      <h1 class="text-xl font-bold text-gray-900">资产库</h1>
      <button class="btn btn-primary btn-sm">📤 新增</button>
      <div class="flex-1" />
      <button class="btn btn-ghost btn-sm" @click="loading = true; assetsApi.listGlobal().then(r => { assets = r.data; loading = false })">
        🔄 刷新
      </button>
      <div class="flex border border-gray-200 rounded-lg overflow-hidden">
        <button
          class="px-2 py-1 text-xs"
          :class="viewMode === 'grid' ? 'bg-gray-100 text-gray-900' : 'text-gray-400'"
          @click="viewMode = 'grid'"
        >
          ⊞
        </button>
        <button
          class="px-2 py-1 text-xs"
          :class="viewMode === 'list' ? 'bg-gray-100 text-gray-900' : 'text-gray-400'"
          @click="viewMode = 'list'"
        >
          ☰
        </button>
      </div>
    </div>

    <!-- Tabs -->
    <div class="flex items-center gap-6 mb-6 border-b border-gray-200">
      <button
        class="pb-2 text-sm font-medium border-b-2 -mb-px transition-colors"
        :class="activeTab === 'assets' ? 'border-gray-900 text-gray-900' : 'border-transparent text-gray-400'"
        @click="activeTab = 'assets'"
      >
        🖼 资产
      </button>
      <button
        class="pb-2 text-sm font-medium border-b-2 -mb-px transition-colors"
        :class="activeTab === 'characters' ? 'border-gray-900 text-gray-900' : 'border-transparent text-gray-400'"
        @click="activeTab = 'characters'"
      >
        👤 人物角色
      </button>
      <div class="flex-1" />
      <span class="text-xs text-gray-400">按时间倒序展示</span>
      <button class="btn btn-ghost btn-sm text-xs">🔽 筛选</button>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex justify-center py-20">
      <div class="w-8 h-8 border-3 border-primary-500 border-t-transparent rounded-full animate-spin" />
    </div>

    <!-- Empty -->
    <EmptyState v-else-if="!assets.length" title="资产库为空" description="创作项目后生成的角色和场景将显示在这里" icon="🎨" />

    <!-- Grid view (参考截图13) -->
    <div v-else-if="viewMode === 'grid'" class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
      <div
        v-for="asset in assets"
        :key="asset.id"
        class="card overflow-hidden group hover:shadow-md transition-all"
      >
        <div class="aspect-square bg-gray-100 overflow-hidden">
          <img
            v-if="asset.reference_images?.[0]"
            :src="asset.reference_images[0]"
            :alt="asset.name"
            class="w-full h-full object-cover"
          />
          <div v-else class="w-full h-full flex items-center justify-center text-3xl text-gray-300">👤</div>
        </div>
        <div class="p-2">
          <div class="flex items-center gap-2 text-xs text-gray-400">
            <span>创作生成</span>
            <span>{{ formatDate(asset.created_at) }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- List view -->
    <div v-else class="space-y-2">
      <div
        v-for="asset in assets"
        :key="asset.id"
        class="card p-3 flex items-center gap-4"
      >
        <div class="w-12 h-12 bg-gray-100 rounded-lg overflow-hidden shrink-0">
          <img v-if="asset.reference_images?.[0]" :src="asset.reference_images[0]" class="w-full h-full object-cover" />
        </div>
        <div class="flex-1">
          <div class="text-sm font-medium text-gray-800">{{ asset.name }}</div>
          <div class="text-xs text-gray-400">{{ formatDate(asset.created_at) }}</div>
        </div>
      </div>
    </div>

    <!-- Footer -->
    <div v-if="assets.length" class="text-center text-xs text-gray-400 mt-8">已加载全部</div>
  </div>
</template>