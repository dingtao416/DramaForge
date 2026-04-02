<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useProjectStore } from '@/stores/project'
import { useAssetsStore } from '@/stores/assets'
import { assetsApi } from '@/api/assets'
import CharacterCard from '@/components/assets/CharacterCard.vue'
import SceneCard from '@/components/assets/SceneCard.vue'
import LoadingOverlay from '@/components/common/LoadingOverlay.vue'
import EmptyState from '@/components/common/EmptyState.vue'

const route = useRoute()
const router = useRouter()
const projectStore = useProjectStore()
const assetsStore = useAssetsStore()

const projectId = Number(route.params.id)
const activeTab = ref<'characters' | 'scenes'>('characters')
const approving = ref(false)

onMounted(() => {
  assetsStore.fetchAssets(projectId)
})

const charCount = computed(() => assetsStore.characters.length)
const sceneCount = computed(() => assetsStore.scenes.length)

async function handleApprove() {
  approving.value = true
  try {
    await assetsApi.approve(projectId)
    await projectStore.fetchProject(projectId)
    router.push(`/projects/${projectId}/episodes`)
  } finally {
    approving.value = false
  }
}
</script>

<template>
  <LoadingOverlay :visible="assetsStore.loading" message="正在加载资产..." />

  <div class="max-w-[1200px] mx-auto px-8 py-8">
    <!-- Tabs -->
    <div class="flex items-center gap-1 mb-8">
      <button
        class="h-[40px] px-5 rounded-full text-[14px] font-medium transition-all cursor-pointer"
        :class="activeTab === 'characters'
          ? 'bg-gray-900 text-white'
          : 'bg-gray-100 text-gray-500 hover:bg-gray-200'"
        @click="activeTab = 'characters'"
      >
        全部角色 {{ charCount }}
      </button>
      <button
        class="h-[40px] px-5 rounded-full text-[14px] font-medium transition-all cursor-pointer"
        :class="activeTab === 'scenes'
          ? 'bg-gray-900 text-white'
          : 'bg-gray-100 text-gray-500 hover:bg-gray-200'"
        @click="activeTab = 'scenes'"
      >
        全部场景 {{ sceneCount }}
      </button>
    </div>

    <!-- Characters grid — 7列 -->
    <div v-if="activeTab === 'characters'">
      <EmptyState
        v-if="!assetsStore.loading && !charCount"
        title="暂无角色"
        description="生成资产后将在这里显示"
        icon="👤"
      />
      <div v-else class="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-6 xl:grid-cols-7 gap-5">
        <CharacterCard
          v-for="char in assetsStore.characters"
          :key="char.id"
          :character="char"
        />
      </div>
    </div>

    <!-- Scenes grid — 4列 -->
    <div v-if="activeTab === 'scenes'">
      <EmptyState
        v-if="!assetsStore.loading && !sceneCount"
        title="暂无场景"
        description="生成资产后将在这里显示"
        icon="🏠"
      />
      <div v-else class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-5">
        <SceneCard
          v-for="scene in assetsStore.scenes"
          :key="scene.id"
          :scene="scene"
        />
      </div>
    </div>
  </div>

  <!-- Bottom bar -->
  <div class="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 px-8 py-4 flex items-center z-40">
    <div class="flex items-center gap-3 text-[14px] text-gray-500">
      <div class="w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center text-primary-600 text-[12px]">🤖</div>
      <span>角色和场景设定会应用到整部剧集中，建议调整完毕后再继续哦</span>
    </div>
    <div class="flex-1" />
    <div class="flex items-center gap-3">
      <button class="btn btn-outline" @click="router.push(`/projects/${projectId}/script`)">
        ← 上一步
      </button>
      <button class="btn btn-primary" :disabled="approving" @click="handleApprove">
        下一步 →
      </button>
    </div>
  </div>
</template>