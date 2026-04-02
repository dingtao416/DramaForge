<script setup lang="ts">
defineProps<{
  asset: any
}>()

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleString('zh-CN', {
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', second: '2-digit',
  })
}
</script>

<template>
  <div class="bg-white border border-gray-200 rounded-[12px] p-3 flex items-center gap-4 hover:border-gray-300 hover:shadow-[0_2px_8px_rgba(0,0,0,0.04)] transition-all cursor-pointer">
    <!-- Thumbnail -->
    <div class="w-12 h-12 rounded-[8px] overflow-hidden bg-gray-100 shrink-0">
      <img
        v-if="asset.reference_images?.[0]"
        :src="asset.reference_images[0]"
        :alt="asset.name"
        class="w-full h-full object-cover"
      />
      <div v-else class="w-full h-full flex items-center justify-center text-lg text-gray-300">
        {{ asset.type === 'scene' ? '🏠' : '👤' }}
      </div>
    </div>

    <!-- Info -->
    <div class="flex-1 min-w-0">
      <div class="text-[14px] font-medium text-gray-800 truncate">{{ asset.name }}</div>
      <div class="text-[12px] text-gray-400 mt-0.5">
        {{ asset.created_at ? formatDate(asset.created_at) : '' }}
      </div>
    </div>

    <!-- Actions -->
    <div class="flex items-center gap-1 shrink-0">
      <button class="w-7 h-7 rounded-md flex items-center justify-center text-gray-400 hover:bg-gray-100 hover:text-gray-600 cursor-pointer transition-colors text-[12px]">+</button>
      <button class="w-7 h-7 rounded-md flex items-center justify-center text-gray-400 hover:bg-gray-100 hover:text-red-400 cursor-pointer transition-colors text-[12px]">♡</button>
      <button class="w-7 h-7 rounded-md flex items-center justify-center text-gray-400 hover:bg-gray-100 hover:text-red-500 cursor-pointer transition-colors text-[12px]">🗑</button>
    </div>
  </div>
</template>
