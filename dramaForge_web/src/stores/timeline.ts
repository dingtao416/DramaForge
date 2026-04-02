import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useTimelineStore = defineStore('timeline', () => {
  const currentTime = ref(0)
  const isPlaying = ref(false)
  const selectedIndices = ref<number[]>([])

  function play() { isPlaying.value = true }
  function pause() { isPlaying.value = false }
  function seek(time: number) { currentTime.value = time }
  function toggleSelect(index: number) {
    const idx = selectedIndices.value.indexOf(index)
    if (idx === -1) selectedIndices.value.push(index)
    else selectedIndices.value.splice(idx, 1)
  }
  function clearSelection() { selectedIndices.value = [] }

  return { currentTime, isPlaying, selectedIndices, play, pause, seek, toggleSelect, clearSelection }
})