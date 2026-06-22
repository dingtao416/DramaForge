<script setup lang="ts">
import { ref } from 'vue'

export interface FeatureCard {
  title: string
  desc: string
  isNew?: boolean
  bg: string
}

defineProps<{
  cards: FeatureCard[]
}>()

const scrollContainer = ref<HTMLElement | null>(null)

function scrollRight() {
  scrollContainer.value?.scrollBy({ left: 260, behavior: 'smooth' })
}
</script>

<template>
  <div class="w-full">
    <h2 class="text-[16px] font-semibold text-white mb-4" style="font-family: 'Press Start 2P', monospace; font-size: 13px; letter-spacing: 1px; color: #F5C34B;">常用功能</h2>
    <div class="relative">
      <div
        ref="scrollContainer"
        class="flex gap-3 overflow-x-auto pb-2 scrollbar-hide"
      >
        <div
          v-for="card in cards"
          :key="card.title"
          class="shrink-0 w-[23%] min-w-[170px] aspect-[16/10] rounded-[2px] overflow-hidden relative cursor-pointer group hover:shadow-lg transition-shadow border-2 border-[#D4C898]"
          :style="{ background: card.bg }"
        >
          <!-- 暗色渐变蒙层 -->
          <div class="absolute inset-0 bg-gradient-to-t from-black/55 via-black/5 to-transparent" />

          <!-- New 标签 -->
          <span
            v-if="card.isNew"
            class="absolute top-3 left-3 text-white text-[10px] px-2 py-0.5 rounded-[2px] font-semibold z-10 border-2 border-[#B87D08]"
            style="background: #E8A317; font-family: 'Press Start 2P', monospace;"
          >New</span>

          <!-- 卡片文字 -->
          <div class="absolute bottom-3 left-3.5 z-10">
            <div class="text-white text-[14px] font-semibold leading-tight">{{ card.title }}</div>
            <div class="text-white/70 text-[11px] mt-1 leading-snug">{{ card.desc }}</div>
          </div>
        </div>
      </div>

      <!-- 右箭头 -->
      <button
        class="absolute -right-2 top-1/2 -translate-y-1/2 w-[32px] h-[32px] rounded-[2px] bg-[#FEF9E7] border-2 border-[#D4C898] flex items-center justify-center text-gray-500 hover:text-[#F5C34B] cursor-pointer transition-colors z-10"
        @click="scrollRight"
      >
        <svg width="12" height="12" viewBox="0 0 12 12" fill="none"><path d="M4.5 2.5L8 6L4.5 9.5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>
      </button>
    </div>
  </div>
</template>

<style scoped>
.scrollbar-hide::-webkit-scrollbar { display: none; }
.scrollbar-hide { -ms-overflow-style: none; scrollbar-width: none; }
</style>
