<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useProjectStore } from '@/stores/project'
import { useScriptStore } from '@/stores/script'
import { VideoStyleLabel } from '@/types/enums'
import LoadingOverlay from '@/components/common/LoadingOverlay.vue'
import EmptyState from '@/components/common/EmptyState.vue'

const route = useRoute()
const router = useRouter()
const projectStore = useProjectStore()
const scriptStore = useScriptStore()

const projectId = Number(route.params.id)
const approving = ref(false)
const rewriting = ref(false)

onMounted(() => {
  scriptStore.fetchScript(projectId)
})

async function handleApprove() {
  approving.value = true
  try {
    await scriptStore.approveScript(projectId)
    await projectStore.fetchProject(projectId)
    router.push(`/projects/${projectId}/assets`)
  } finally {
    approving.value = false
  }
}

async function handleRewrite() {
  rewriting.value = true
  try {
    await scriptStore.rewriteNarration(projectId)
  } finally {
    rewriting.value = false
  }
}
</script>

<template>
  <LoadingOverlay :visible="scriptStore.loading" message="正在加载剧本..." />
  <LoadingOverlay :visible="rewriting" message="正在改写为旁白型..." />

  <div class="max-w-[860px] mx-auto px-8 py-8">
    <!-- Empty state -->
    <EmptyState
      v-if="!scriptStore.loading && !scriptStore.script"
      title="暂无剧本"
      description="请从首页开始创作或上传剧本"
      icon="📝"
    />

    <template v-if="scriptStore.script">
      <!-- Meta info -->
      <div class="mb-8">
        <div class="text-[15px] text-gray-500 mb-1.5">
          视频风格：{{ projectStore.currentProject ? VideoStyleLabel[projectStore.currentProject.style] : '' }}
        </div>
        <div class="text-[15px] text-gray-500">
          画面比例：{{ projectStore.currentProject?.aspect_ratio || '9:16' }}
        </div>
      </div>

      <!-- Script summary card -->
      <div class="mb-8">
        <h2 class="text-[17px] font-bold text-gray-900 mb-4">剧本摘要</h2>
        <div class="bg-white border border-gray-200 rounded-[12px] px-8 py-8">
          <div class="space-y-7">
            <div>
              <div class="text-[15px] font-bold text-gray-900 mb-1.5">主角</div>
              <div class="text-[15px] text-gray-600 leading-[1.8]">{{ scriptStore.script.protagonist || '未设置' }}</div>
            </div>
            <div>
              <div class="text-[15px] font-bold text-gray-900 mb-1.5">故事类型</div>
              <div class="text-[15px] text-gray-600 leading-[1.8]">{{ scriptStore.script.genre || '未设置' }}</div>
            </div>
            <div>
              <div class="text-[15px] font-bold text-gray-900 mb-1.5">故事梗概</div>
              <div class="text-[15px] text-gray-600 leading-[1.8]">{{ scriptStore.script.synopsis || '未设置' }}</div>
            </div>
            <div>
              <div class="text-[15px] font-bold text-gray-900 mb-1.5">故事背景</div>
              <div class="text-[15px] text-gray-600 leading-[1.8]">{{ scriptStore.script.background || '未设置' }}</div>
            </div>
            <div>
              <div class="text-[15px] font-bold text-gray-900 mb-1.5">故事设定</div>
              <div class="text-[15px] text-gray-600 leading-[1.8]">{{ scriptStore.script.setting || '未设置' }}</div>
            </div>
            <div>
              <div class="text-[15px] font-bold text-gray-900 mb-1.5">一句话故事</div>
              <div class="text-[15px] text-gray-600 leading-[1.8]">{{ scriptStore.script.one_liner || '未设置' }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Episodes accordion -->
      <div class="mb-8">
        <h2 class="text-[17px] font-bold text-gray-900 mb-4">剧本内容</h2>
        <div class="space-y-3">
          <details
            v-for="ep in scriptStore.script.episodes"
            :key="ep.id"
            class="bg-white border border-gray-200 rounded-[12px] group"
            :open="scriptStore.script.episodes.length <= 3"
          >
            <summary class="px-6 py-4 cursor-pointer text-[15px] font-semibold text-gray-800 hover:bg-gray-50 rounded-[12px] select-none list-none flex items-center gap-3">
              <svg width="14" height="14" viewBox="0 0 12 12" fill="none" class="text-gray-400 transition-transform group-open:rotate-90 shrink-0">
                <path d="M4.5 2.5L8 6L4.5 9.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              第 {{ ep.number }} 集 · {{ ep.title || '无标题' }}
            </summary>
            <div class="px-6 pb-5 text-[15px] text-gray-600 whitespace-pre-wrap leading-[1.9] border-t border-gray-100 pt-4 mx-2">
              {{ ep.title }}
            </div>
          </details>
        </div>
      </div>

      <!-- Bottom bar -->
      <div class="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 px-8 py-4 flex items-center z-40">
        <div class="flex items-center gap-3 text-[14px] text-gray-500">
          <div class="w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center text-primary-600 text-[12px]">🤖</div>
          <span v-if="scriptStore.script.is_approved">剧本内容整理完毕，可以进行下一步了</span>
          <span v-else>请审核剧本内容，确认后进入资产生成</span>
        </div>
        <div class="flex-1" />
        <div class="flex items-center gap-3">
          <button class="btn btn-outline" :disabled="rewriting" @click="handleRewrite">
            改写为旁白型
          </button>
          <button class="btn btn-primary" :disabled="approving" @click="handleApprove">
            {{ scriptStore.script.is_approved ? '下一步 →' : '确认并下一步 →' }}
          </button>
        </div>
      </div>

      <!-- Bottom spacer -->
      <div class="h-20" />
    </template>
  </div>
</template>