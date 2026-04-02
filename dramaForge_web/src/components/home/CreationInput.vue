<script setup lang="ts">
import { ref, computed } from 'vue'

const props = defineProps<{
  modelValue: string
  loading?: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
  submit: []
}>()

const inputValue = computed({
  get: () => props.modelValue,
  set: (v: string) => emit('update:modelValue', v),
})

const canSend = computed(() => inputValue.value.trim().length > 0 && !props.loading)
</script>

<template>
  <div class="w-full bg-white rounded-[16px] border border-[#D4C5F9] shadow-[0_1px_8px_rgba(124,58,237,0.06)] focus-within:border-primary-500 transition-colors">
    <!-- Textarea -->
    <textarea
      v-model="inputValue"
      rows="3"
      class="w-full pl-[49px] pr-6 pt-5 pb-2 resize-none border-none outline-none text-[14px] text-gray-800 placeholder-gray-400 bg-transparent leading-[1.8]"
      placeholder="告诉我，你今天想创造一点什么？"
      @keydown.ctrl.enter="canSend && emit('submit')"
    />

    <!-- Toolbar -->
    <div class="flex items-center gap-2 pl-[41px] pr-4 pb-4">
      <!-- + 附件按钮 -->
      <button class="w-[36px] h-[36px] rounded-[10px] border border-gray-200 flex items-center justify-center text-gray-500 hover:bg-gray-50 hover:text-gray-700 cursor-pointer transition-colors bg-white">
        <svg width="18" height="18" viewBox="0 0 18 18" fill="none"><line x1="9" y1="4" x2="9" y2="14" stroke="currentColor" stroke-width="2" stroke-linecap="round"/><line x1="4" y1="9" x2="14" y2="9" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
      </button>

      <!-- Agent 模式 -->
      <button class="h-[36px] px-4 rounded-full flex items-center gap-2 text-[13px] text-gray-600 hover:bg-gray-50 cursor-pointer transition-colors border border-gray-200 bg-white">
        <svg width="15" height="15" viewBox="0 0 15 15" fill="none"><circle cx="7.5" cy="7.5" r="6" stroke="currentColor" stroke-width="1.2"/><line x1="1" y1="7.5" x2="14" y2="7.5" stroke="currentColor" stroke-width="1"/><ellipse cx="7.5" cy="7.5" rx="2.8" ry="6" stroke="currentColor" stroke-width="1"/></svg>
        <span>Agent 模式</span>
        <svg width="12" height="12" viewBox="0 0 12 12" fill="none"><path d="M3.5 4.5L6 7L8.5 4.5" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/></svg>
      </button>

      <!-- 模型选择 -->
      <button class="h-[36px] px-3 rounded-full flex items-center gap-1.5 text-gray-500 hover:bg-gray-50 cursor-pointer transition-colors border border-gray-200 bg-white">
        <svg width="15" height="15" viewBox="0 0 15 15" fill="none"><rect x="1.5" y="7" width="3" height="6.5" rx="0.8" stroke="currentColor" stroke-width="1.2"/><rect x="6" y="4" width="3" height="9.5" rx="0.8" stroke="currentColor" stroke-width="1.2"/><rect x="10.5" y="1.5" width="3" height="12" rx="0.8" stroke="currentColor" stroke-width="1.2"/></svg>
        <svg width="12" height="12" viewBox="0 0 12 12" fill="none"><path d="M3.5 4.5L6 7L8.5 4.5" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/></svg>
      </button>

      <!-- 网格 -->
      <button class="w-[36px] h-[36px] rounded-[10px] flex items-center justify-center text-gray-400 hover:bg-gray-50 hover:text-gray-600 cursor-pointer transition-colors">
        <svg width="17" height="17" viewBox="0 0 17 17" fill="none"><rect x="2" y="2" width="5.5" height="5.5" rx="1.2" stroke="currentColor" stroke-width="1.3"/><rect x="9.5" y="2" width="5.5" height="5.5" rx="1.2" stroke="currentColor" stroke-width="1.3"/><rect x="2" y="9.5" width="5.5" height="5.5" rx="1.2" stroke="currentColor" stroke-width="1.3"/><rect x="9.5" y="9.5" width="5.5" height="5.5" rx="1.2" stroke="currentColor" stroke-width="1.3"/></svg>
      </button>

      <!-- 窗口 -->
      <button class="w-[36px] h-[36px] rounded-[10px] flex items-center justify-center text-gray-400 hover:bg-gray-50 hover:text-gray-600 cursor-pointer transition-colors">
        <svg width="17" height="17" viewBox="0 0 17 17" fill="none"><rect x="1.5" y="3.5" width="14" height="10" rx="2" stroke="currentColor" stroke-width="1.3"/><line x1="4.5" y1="10" x2="12.5" y2="10" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/><line x1="6.5" y1="7.5" x2="10.5" y2="7.5" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/></svg>
      </button>

      <div class="flex-1" />

      <!-- 星火/设置 -->
      <button class="w-[36px] h-[36px] rounded-[10px] flex items-center justify-center text-gray-400 hover:bg-gray-50 hover:text-primary-500 cursor-pointer transition-colors">
        <svg width="18" height="18" viewBox="0 0 18 18" fill="none"><path d="M9 2L10.5 7L15.5 8.5L10.5 10L9 15L7.5 10L2.5 8.5L7.5 7L9 2Z" stroke="currentColor" stroke-width="1.2" stroke-linejoin="round"/></svg>
      </button>

      <!-- 发送按钮 -->
      <button
        class="w-[40px] h-[40px] rounded-full flex items-center justify-center transition-all cursor-pointer"
        :class="canSend
          ? 'bg-primary-600 text-white hover:bg-primary-700 shadow-[0_2px_10px_rgba(124,58,237,0.35)]'
          : 'bg-gray-200 text-gray-400 cursor-not-allowed'"
        :disabled="!canSend"
        @click="emit('submit')"
      >
        <span v-if="loading" class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
        <svg v-else width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M8 13V3M8 3L4 7M8 3L12 7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
      </button>
    </div>
  </div>
</template>
