<script setup lang="ts">
import { ref } from 'vue'

export interface EpisodeItem {
  id: number
  number: number
  title: string
  content?: string
}

const props = defineProps<{
  episodes: EpisodeItem[]
  defaultOpen?: boolean
}>()

const openEpisodes = ref<Set<number>>(
  props.defaultOpen ? new Set(props.episodes.map(e => e.id)) : new Set()
)

function toggle(id: number) {
  if (openEpisodes.value.has(id)) {
    openEpisodes.value.delete(id)
  } else {
    openEpisodes.value.add(id)
  }
}
</script>

<template>
  <div class="space-y-2">
    <div
      v-for="ep in episodes"
      :key="ep.id"
      class="bg-white border border-gray-200 rounded-[12px] overflow-hidden transition-all"
    >
      <!-- Header -->
      <div
        class="px-5 py-3.5 flex items-center gap-3 cursor-pointer hover:bg-gray-50 select-none transition-colors"
        @click="toggle(ep.id)"
      >
        <!-- 展开/折叠箭头 -->
        <svg
          width="12" height="12" viewBox="0 0 12 12" fill="none"
          class="text-gray-400 transition-transform shrink-0"
          :class="{ 'rotate-90': openEpisodes.has(ep.id) }"
        >
          <path d="M4.5 2.5L8 6L4.5 9.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>

        <span class="text-[14px] font-medium text-gray-800">
          第 {{ ep.number }} 集 · {{ ep.title || '无标题' }}
        </span>
      </div>

      <!-- Content -->
      <Transition name="accordion">
        <div v-if="openEpisodes.has(ep.id)" class="border-t border-gray-100">
          <div class="px-5 py-4 text-[14px] text-gray-600 whitespace-pre-wrap leading-[1.9]">
            {{ ep.content || ep.title }}
          </div>
        </div>
      </Transition>
    </div>
  </div>
</template>

<style scoped>
.accordion-enter-active,
.accordion-leave-active {
  transition: all 0.25s ease;
  overflow: hidden;
}
.accordion-enter-from,
.accordion-leave-to {
  opacity: 0;
  max-height: 0;
}
.accordion-enter-to,
.accordion-leave-from {
  opacity: 1;
  max-height: 800px;
}
</style>
