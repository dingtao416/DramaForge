<script setup lang="ts">
defineProps<{
  visible: boolean
  message?: string
}>()
</script>

<template>
  <Transition name="fade">
    <div v-if="visible" class="fixed inset-0 z-[100] flex items-center justify-center bg-black/30 backdrop-blur-sm">
      <div class="bg-white rounded-2xl p-8 flex flex-col items-center gap-4 shadow-xl">
        <div class="w-10 h-10 border-3 border-primary-500 border-t-transparent rounded-full animate-spin" />
        <p class="text-sm text-gray-600">{{ message || '正在处理中...' }}</p>
      </div>
    </div>
  </Transition>
</template>