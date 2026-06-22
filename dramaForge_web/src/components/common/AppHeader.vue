<script setup lang="ts">
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()

function isActive(path: string) {
  if (path === '/') return route.path === '/'
  return route.path.startsWith(path)
}
</script>

<template>
  <header class="h-16 border-b-2 border-[#D4C898] flex items-center px-5 shrink-0 sticky top-0 z-50" style="background: #FDF5D6;">
    <!-- Logo -->
    <div class="flex items-center gap-2 cursor-pointer" @click="router.push('/')">
      <div class="w-7 h-7 rounded-[2px] flex items-center justify-center text-white text-xs font-bold" style="background: #E8A317;">D</div>
      <span class="text-[15px] font-semibold text-gray-900">DramaForge</span>
    </div>

    <div class="flex-1" />

    <!-- Right actions -->
    <div class="flex items-center gap-3">
      <button class="h-8 px-3 rounded-[2px] border-2 border-[#D4C898] text-[13px] text-gray-600 flex items-center gap-1.5 hover:bg-black/5 transition-colors cursor-pointer bg-transparent">
        <span style="color: #E8A317;">⚡</span>
        <span>0</span>
        <span class="text-gray-500 text-[10px]">▾</span>
      </button>
      <button class="text-[13px] font-medium hover:opacity-80 cursor-pointer" style="color: #E8A317;">订阅</button>
      <button class="w-7 h-7 rounded-[2px] flex items-center justify-center text-gray-500 hover:bg-black/5 cursor-pointer transition-colors">💬</button>
      <button class="w-7 h-7 rounded-[2px] flex items-center justify-center text-gray-500 hover:bg-black/5 cursor-pointer transition-colors">🔔</button>
      <div class="w-8 h-8 rounded-[2px] flex items-center justify-center text-white text-[13px] cursor-pointer" style="background: #E8A317;">U</div>
    </div>
  </header>
</template>