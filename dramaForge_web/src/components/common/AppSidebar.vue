<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps<{
  collapsed?: boolean
}>()

const emit = defineEmits<{
  'update:collapsed': [value: boolean]
  newDialog: []
}>()

const router = useRouter()
</script>

<template>
  <aside
    class="border-r border-[#EBEBEB] bg-white flex flex-col shrink-0 transition-all duration-200"
    :class="collapsed ? 'w-0 overflow-hidden border-r-0' : 'w-[240px]'"
  >
    <!-- Top: Logo + collapse -->
    <div class="flex items-center justify-between pl-5 pr-4 h-[56px] shrink-0">
      <div class="flex items-center gap-2.5 cursor-pointer" @click="router.push('/')">
        <div class="w-7 h-7 bg-primary-600 rounded-lg flex items-center justify-center text-white text-[11px] font-bold">D</div>
        <span class="text-[15px] font-semibold text-gray-900 whitespace-nowrap">DramaForge</span>
      </div>
      <button
        class="w-7 h-7 rounded-md flex items-center justify-center text-gray-400 hover:bg-gray-100 hover:text-gray-600 cursor-pointer transition-colors"
        @click="emit('update:collapsed', true)"
      >
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><rect x="2" y="2" width="12" height="12" rx="2" stroke="currentColor" stroke-width="1.5"/><line x1="6" y1="2" x2="6" y2="14" stroke="currentColor" stroke-width="1.5"/></svg>
      </button>
    </div>

    <!-- + New dialog -->
    <div class="px-4 mb-2">
      <button
        class="w-full h-[48px] rounded-[12px] bg-gray-50 border border-gray-200 text-[14px] text-gray-700 flex items-center gap-3 px-4 hover:bg-gray-100 transition-colors cursor-pointer"
        @click="emit('newDialog')"
      >
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><line x1="8" y1="3" x2="8" y2="13" stroke="currentColor" stroke-width="2" stroke-linecap="round"/><line x1="3" y1="8" x2="13" y2="8" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
        新对话
      </button>
    </div>

    <!-- Asset library link -->
    <div class="px-4 mb-6">
      <div
        class="h-[48px] rounded-[12px] text-[14px] text-gray-600 flex items-center gap-3 px-4 hover:bg-gray-50 cursor-pointer transition-colors"
        @click="router.push('/assets')"
      >
        <svg width="18" height="18" viewBox="0 0 18 18" fill="none"><path d="M2.5 5.5C2.5 4.4 3.4 3.5 4.5 3.5H7L8.75 5.25H13.5C14.6 5.25 15.5 6.15 15.5 7.25V12.5C15.5 13.6 14.6 14.5 13.5 14.5H4.5C3.4 14.5 2.5 13.6 2.5 12.5V5.5Z" stroke="currentColor" stroke-width="1.4"/></svg>
        资产库
      </div>
    </div>

    <!-- Slot for custom content (e.g., ProjectHistory) -->
    <div class="flex-1 overflow-hidden flex flex-col">
      <slot />
    </div>
  </aside>

  <!-- Expand button when collapsed -->
  <button
    v-if="collapsed"
    class="absolute left-3 top-4 z-20 w-8 h-8 rounded-lg bg-white border border-gray-200 flex items-center justify-center text-gray-400 hover:text-gray-600 hover:bg-gray-50 cursor-pointer shadow-sm transition-colors"
    @click="emit('update:collapsed', false)"
  >
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><rect x="2" y="2" width="12" height="12" rx="2" stroke="currentColor" stroke-width="1.5"/><line x1="6" y1="2" x2="6" y2="14" stroke="currentColor" stroke-width="1.5"/></svg>
  </button>
</template>
