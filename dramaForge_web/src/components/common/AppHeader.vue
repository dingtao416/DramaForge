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
  <header class="h-14 border-b border-[#E8E8E8] bg-white flex items-center px-5 shrink-0 sticky top-0 z-50">
    <!-- Logo -->
    <div class="flex items-center gap-2 cursor-pointer" @click="router.push('/')">
      <div class="w-7 h-7 bg-primary-600 rounded-lg flex items-center justify-center text-white text-xs font-bold">D</div>
      <span class="text-[15px] font-semibold text-gray-900">DramaForge</span>
    </div>

    <div class="flex-1" />

    <!-- Right actions -->
    <div class="flex items-center gap-3">
      <button class="h-8 px-3 rounded-full border border-gray-200 text-[13px] text-gray-700 flex items-center gap-1.5 hover:bg-gray-50 transition-colors cursor-pointer">
        <span class="text-primary-500">⚡</span>
        <span>0</span>
        <span class="text-gray-400 text-[10px]">▾</span>
      </button>
      <button class="text-[13px] text-primary-600 font-medium hover:text-primary-700 cursor-pointer">订阅</button>
      <button class="w-7 h-7 rounded-full flex items-center justify-center text-gray-400 hover:bg-gray-100 cursor-pointer transition-colors">💬</button>
      <button class="w-7 h-7 rounded-full flex items-center justify-center text-gray-400 hover:bg-gray-100 cursor-pointer transition-colors">🔔</button>
      <div class="w-8 h-8 rounded-full bg-gray-800 flex items-center justify-center text-white text-[13px] cursor-pointer">U</div>
    </div>
  </header>
</template>