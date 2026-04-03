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

  <div class="page-container-wide">
    <!-- Tabs -->
    <div class="assets-tabs">
      <button
        class="assets-tab"
        :class="{ active: activeTab === 'characters' }"
        @click="activeTab = 'characters'"
      >
        全部角色 {{ charCount }}
      </button>
      <button
        class="assets-tab"
        :class="{ active: activeTab === 'scenes' }"
        @click="activeTab = 'scenes'"
      >
        全部场景 {{ sceneCount }}
      </button>
    </div>

    <!-- Characters grid -->
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

    <!-- Scenes grid -->
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
  <div class="bottom-action-bar">
    <div class="bar-hint">
      <div class="bar-icon">🤖</div>
      <span>角色和场景设定会应用到整部剧集中，建议调整完毕后再继续</span>
    </div>
    <div class="bar-actions">
      <button class="btn btn-outline btn-sm" @click="router.push(`/projects/${projectId}/script`)">
        ← 上一步
      </button>
      <button class="btn btn-primary btn-sm" @click="router.push(`/projects/${projectId}/episodes`)">
        下一步 →
      </button>
    </div>
  </div>
</template>

<style scoped>
.assets-tabs {
  display: flex;
  align-items: center;
  gap: 24px;
  margin-bottom: 28px;
  border-bottom: 1px solid #f0f0f0;
}

.assets-tab {
  position: relative;
  padding: 10px 4px;
  font-size: 15px;
  font-weight: 500;
  color: #999;
  background: none;
  border: none;
  cursor: pointer;
  transition: color 0.2s;
}

.assets-tab:hover {
  color: #555;
}

.assets-tab.active {
  color: #1a1a1a;
  font-weight: 600;
}

.assets-tab.active::after {
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  bottom: -1px;
  height: 2px;
  background: #1a1a1a;
  border-radius: 1px;
}
</style>
