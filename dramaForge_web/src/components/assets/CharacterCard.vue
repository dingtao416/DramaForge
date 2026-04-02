<script setup lang="ts">
import { CharacterRoleLabel, CharacterRole } from '@/types/enums'
import type { CharacterDetail } from '@/types/character'

const props = defineProps<{
  character: CharacterDetail
}>()

const emit = defineEmits<{
  edit: [CharacterDetail]
  regenerate: [CharacterDetail]
}>()

const mainImage = props.character.reference_images?.[0]
</script>

<template>
  <div class="group cursor-pointer">
    <!-- Image — 无边框，纯圆角 -->
    <div class="aspect-[3/4] bg-gray-100 rounded-[12px] relative overflow-hidden">
      <img
        v-if="mainImage"
        :src="mainImage"
        :alt="character.name"
        class="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
      />
      <div v-else class="w-full h-full flex items-center justify-center text-4xl text-gray-300">
        👤
      </div>

      <!-- Hover overlay with actions -->
      <div class="absolute inset-0 bg-black/0 group-hover:bg-black/30 transition-colors flex items-end justify-center pb-3 opacity-0 group-hover:opacity-100">
        <div class="flex items-center gap-1.5">
          <button
            class="h-[28px] px-2.5 rounded-md bg-white/90 text-[12px] text-gray-700 hover:bg-white cursor-pointer transition-colors"
            @click.stop="emit('edit', character)"
          >编辑</button>
          <button
            class="h-[28px] px-2.5 rounded-md bg-white/90 text-[12px] text-gray-700 hover:bg-white cursor-pointer transition-colors"
            @click.stop="emit('regenerate', character)"
          >重新生成</button>
        </div>
      </div>

      <!-- Role badge -->
      <span
        v-if="character.role === CharacterRole.PROTAGONIST"
        class="absolute top-2 left-2 badge badge-primary text-[11px]"
      >
        主角
      </span>
    </div>

    <!-- Info — 简洁文字 -->
    <div class="mt-2.5 px-0.5">
      <div class="text-[14px] font-medium text-gray-900 truncate">{{ character.name }}</div>
      <div class="text-[12px] text-gray-400 mt-0.5">
        共{{ character.reference_images?.length || 0 }}个形象
      </div>
    </div>
  </div>
</template>