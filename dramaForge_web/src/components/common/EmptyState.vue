<script setup lang="ts">
defineProps<{
  title?: string
  description?: string
  icon?: string
}>()
</script>

<template>
  <div class="flex flex-col items-center justify-center py-16 text-center">
    <div class="text-4xl mb-4">{{ icon || '📭' }}</div>
    <h3 class="text-base font-medium text-gray-700 mb-1">{{ title || '暂无数据' }}</h3>
    <p class="text-sm text-gray-400">{{ description || '数据将在操作后显示' }}</p>
    <div class="mt-4">
      <slot />
    </div>
  </div>
</template>