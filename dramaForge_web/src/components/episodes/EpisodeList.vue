<script setup lang="ts">
import type { EpisodeOverview } from '@/types/episode'
import EpisodeCard from './EpisodeCard.vue'

defineProps<{
  episodes: EpisodeOverview[]
}>()

const emit = defineEmits<{
  preview: [episode: EpisodeOverview]
  edit: [episode: EpisodeOverview]
  export: [episode: EpisodeOverview]
}>()
</script>

<template>
  <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
    <EpisodeCard
      v-for="ep in episodes"
      :key="ep.id"
      :episode="ep"
      @preview="emit('preview', ep)"
      @edit="emit('edit', ep)"
      @export="emit('export', ep)"
    />
  </div>
</template>
