<script setup lang="ts">
defineProps<{
  title?: string
  description?: string
  icon?: string
}>()
</script>

<template>
  <div class="flex flex-col items-center justify-center py-16 text-center">
    <div class="w-16 h-16 rounded-[2px] border-2 border-[#D4C898] flex items-center justify-center text-3xl mb-4" style="background: rgba(0,0,0,0.03);">
      {{ icon || '📭' }}
    </div>
    <h3 class="text-base font-medium text-gray-600 mb-1">{{ title || '暂无数据' }}</h3>
    <p class="text-sm text-gray-500">{{ description || '数据将在操作后显示' }}</p>
    <div class="mt-4">
      <slot />
    </div>
  </div>
</template>