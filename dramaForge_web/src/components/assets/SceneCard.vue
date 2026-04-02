<script setup lang="ts">
import type { SceneDetail } from '@/types/scene'

const props = defineProps<{
  scene: SceneDetail
}>()

const emit = defineEmits<{
  edit: [SceneDetail]
  regenerate: [SceneDetail]
}>()

const mainImage = props.scene.reference_images?.[0]
</script>

<template>
  <div class="group cursor-pointer">
    <!-- Image — 无边框，纯圆角 -->
    <div class="aspect-[16/10] bg-gray-100 rounded-[12px] relative overflow-hidden">
      <img
        v-if="mainImage"
        :src="mainImage"
        :alt="scene.name"
        class="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
      />
      <div v-else class="w-full h-full flex items-center justify-center text-4xl text-gray-300">
        🏠
      </div>

      <!-- Hover overlay with actions -->
      <div class="absolute inset-0 bg-black/0 group-hover:bg-black/30 transition-colors flex items-end justify-center pb-3 opacity-0 group-hover:opacity-100">
        <div class="flex items-center gap-1.5">
          <button
            class="h-[28px] px-2.5 rounded-md bg-white/90 text-[12px] text-gray-700 hover:bg-white cursor-pointer transition-colors"
            @click.stop="emit('edit', scene)"
          >编辑</button>
          <button
            class="h-[28px] px-2.5 rounded-md bg-white/90 text-[12px] text-gray-700 hover:bg-white cursor-pointer transition-colors"
            @click.stop="emit('regenerate', scene)"
          >重新生成</button>
        </div>
      </div>
    </div>

    <!-- Info -->
    <div class="mt-2.5 px-0.5">
      <div class="text-[14px] font-medium text-gray-900 truncate">{{ scene.name }}</div>
      <div class="text-[12px] text-gray-400 mt-0.5">
        共{{ scene.reference_images?.length || 0 }}个场景图
      </div>
    </div>
  </div>
</template>