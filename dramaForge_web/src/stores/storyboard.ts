import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { storyboardApi } from '@/api/storyboard'
import type { StoryboardDetail, ShotDetail } from '@/types/shot'
import type { SegmentDetail } from '@/types/segment'

export const useStoryboardStore = defineStore('storyboard', () => {
  const storyboard = ref<StoryboardDetail | null>(null)
  const currentSegmentIndex = ref(0)
  const currentShotIndex = ref(0)
  const loading = ref(false)

  const currentSegment = computed<SegmentDetail | null>(() => {
    if (!storyboard.value) return null
    return storyboard.value.segments[currentSegmentIndex.value] || null
  })

  const currentShot = computed<ShotDetail | null>(() => {
    if (!currentSegment.value) return null
    return currentSegment.value.shots[currentShotIndex.value] || null
  })

  async function fetchStoryboard(projectId: number, episodeId: number) {
    loading.value = true
    try {
      const { data } = await storyboardApi.get(projectId, episodeId)
      storyboard.value = data
      currentSegmentIndex.value = 0
      currentShotIndex.value = 0
    } finally {
      loading.value = false
    }
  }

  async function generateStoryboard(projectId: number, episodeId: number) {
    loading.value = true
    try {
      const { data } = await storyboardApi.generate(projectId, episodeId)
      storyboard.value = data
    } finally {
      loading.value = false
    }
  }

  function selectSegment(index: number) {
    currentSegmentIndex.value = index
    currentShotIndex.value = 0
  }

  return {
    storyboard,
    currentSegmentIndex,
    currentShotIndex,
    currentSegment,
    currentShot,
    loading,
    fetchStoryboard,
    generateStoryboard,
    selectSegment,
  }
})