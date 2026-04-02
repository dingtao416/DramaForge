<script setup lang="ts">
defineProps<{
  assets: any[]
}>()

const emit = defineEmits<{
  add: [asset: any]
  favorite: [asset: any]
  delete: [asset: any]
}>()

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleString('zh-CN', {
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', second: '2-digit',
  })
}
</script>

<template>
  <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
    <div
      v-for="asset in assets"
      :key="asset.id"
      class="bg-white border border-gray-200 rounded-[12px] overflow-hidden group hover:border-gray-300 hover:shadow-[0_2px_8px_rgba(0,0,0,0.06)] transition-all"
    >
      <!-- Image -->
      <div class="aspect-square bg-gray-100 overflow-hidden">
        <img
          v-if="asset.reference_images?.[0]"
          :src="asset.reference_images[0]"
          :alt="asset.name"
          class="w-full h-full object-cover"
        />
        <div v-else class="w-full h-full flex items-center justify-center text-3xl text-gray-300">
          {{ asset.type === 'scene' ? '🏠' : '👤' }}
        </div>
      </div>

      <!-- Bottom icons -->
      <div class="flex items-center justify-center gap-3 py-2 border-t border-gray-100">
        <button
          class="w-7 h-7 rounded-md flex items-center justify-center text-gray-400 hover:bg-gray-100 hover:text-gray-600 cursor-pointer transition-colors text-[14px]"
          @click.stop="emit('add', asset)"
        >+</button>
        <button
          class="w-7 h-7 rounded-md flex items-center justify-center text-gray-400 hover:bg-gray-100 hover:text-red-400 cursor-pointer transition-colors text-[14px]"
          @click.stop="emit('favorite', asset)"
        >♡</button>
        <button
          class="w-7 h-7 rounded-md flex items-center justify-center text-gray-400 hover:bg-gray-100 hover:text-red-500 cursor-pointer transition-colors text-[14px]"
          @click.stop="emit('delete', asset)"
        >🗑</button>
      </div>

      <!-- Info -->
      <div class="px-3 pb-2.5">
        <div class="text-[12px] text-gray-400 flex items-center gap-1.5">
          <span>创作生成</span>
          <span>{{ asset.created_at ? formatDate(asset.created_at) : '' }}</span>
        </div>
      </div>
    </div>
  </div>
</template>
