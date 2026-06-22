<script setup lang="ts">
defineProps<{
  visible: boolean
  message?: string
}>()
</script>

<template>
  <Transition name="fade">
    <div v-if="visible" class="fixed inset-0 z-[100] flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div class="bg-[#FEF9E7] rounded-[2px] p-8 flex flex-col items-center gap-4 border-2 border-[#F5C34B]" style="box-shadow: 6px 6px 0 0 rgba(0,0,0,0.4);">
        <!-- Pixel coin spinner -->
        <div class="w-10 h-10 border-3 border-[#F5C34B] border-t-transparent rounded-[2px] animate-spin" />
        <p class="text-sm text-gray-600 font-pixel tracking-wider">{{ message || '正在处理中...' }}</p>
      </div>
    </div>
  </Transition>
</template>