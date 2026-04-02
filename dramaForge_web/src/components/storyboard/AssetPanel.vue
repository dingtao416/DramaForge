<script setup lang="ts">
import type { CharacterDetail } from '@/types/character'
import type { SceneDetail } from '@/types/scene'

defineProps<{
  characters: CharacterDetail[]
  scenes: SceneDetail[]
}>()

const emit = defineEmits<{
  selectCharacter: [char: CharacterDetail]
  selectScene: [scene: SceneDetail]
}>()
</script>

<template>
  <aside class="w-52 border-r border-gray-200 bg-white overflow-y-auto shrink-0 flex flex-col">
    <!-- Header -->
    <div class="flex items-center justify-between px-3 pt-3 pb-2">
      <span class="text-[14px] font-medium text-gray-900">资产库</span>
      <button class="w-7 h-7 rounded-md flex items-center justify-center text-gray-400 hover:bg-gray-100 hover:text-gray-600 cursor-pointer transition-colors">
        <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><line x1="7" y1="3" x2="7" y2="11" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/><line x1="3" y1="7" x2="11" y2="7" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>
      </button>
    </div>

    <div class="flex-1 overflow-y-auto px-3 pb-3">
      <!-- Characters -->
      <div class="mb-4">
        <div class="text-[12px] text-gray-400 mb-2 flex items-center gap-1">
          <span>👤</span>
          <span>角色 ({{ characters.length }})</span>
        </div>
        <div class="grid grid-cols-2 gap-2">
          <div
            v-for="char in characters"
            :key="char.id"
            class="text-center cursor-pointer group"
            @click="emit('selectCharacter', char)"
          >
            <div class="w-full aspect-square bg-gray-100 rounded-[8px] overflow-hidden mb-1 group-hover:ring-2 ring-primary-400 transition-all">
              <img
                v-if="char.reference_images?.[0]"
                :src="char.reference_images[0]"
                :alt="char.name"
                class="w-full h-full object-cover"
              />
              <div v-else class="w-full h-full flex items-center justify-center text-xl text-gray-300">👤</div>
            </div>
            <div class="text-[10px] text-gray-600 truncate leading-tight px-0.5">{{ char.name }}</div>
          </div>
        </div>
      </div>

      <!-- Scenes -->
      <div class="mb-4">
        <div class="text-[12px] text-gray-400 mb-2 flex items-center gap-1">
          <span>🏠</span>
          <span>场景 ({{ scenes.length }})</span>
        </div>
        <div class="space-y-2">
          <div
            v-for="scene in scenes"
            :key="scene.id"
            class="cursor-pointer group"
            @click="emit('selectScene', scene)"
          >
            <div class="w-full aspect-[16/10] bg-gray-100 rounded-[8px] overflow-hidden mb-1 group-hover:ring-2 ring-primary-400 transition-all">
              <img
                v-if="scene.reference_images?.[0]"
                :src="scene.reference_images[0]"
                :alt="scene.name"
                class="w-full h-full object-cover"
              />
              <div v-else class="w-full h-full flex items-center justify-center text-xl text-gray-300">🏠</div>
            </div>
            <div class="text-[10px] text-gray-600 truncate">{{ scene.name }}</div>
          </div>
        </div>
      </div>

      <!-- Narrator -->
      <div>
        <div class="text-[12px] text-gray-400 mb-2">旁白</div>
        <div class="flex items-center gap-2 px-2 py-2 rounded-[8px] bg-gray-50 hover:bg-gray-100 cursor-pointer transition-colors">
          <div class="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center text-[12px] text-gray-500">🎙</div>
          <span class="text-[12px] text-gray-600">旁白</span>
        </div>
      </div>
    </div>
  </aside>
</template>
