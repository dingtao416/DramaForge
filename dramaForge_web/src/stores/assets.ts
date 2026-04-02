import { defineStore } from 'pinia'
import { ref } from 'vue'
import { assetsApi } from '@/api/assets'
import type { CharacterDetail } from '@/types/character'
import type { SceneDetail } from '@/types/scene'

export const useAssetsStore = defineStore('assets', () => {
  const characters = ref<CharacterDetail[]>([])
  const scenes = ref<SceneDetail[]>([])
  const loading = ref(false)

  async function fetchAssets(projectId: number) {
    loading.value = true
    try {
      const [charRes, sceneRes] = await Promise.all([
        assetsApi.getCharacters(projectId),
        assetsApi.getScenes(projectId),
      ])
      characters.value = charRes.data
      scenes.value = sceneRes.data
    } finally {
      loading.value = false
    }
  }

  async function generateAll(projectId: number) {
    loading.value = true
    try {
      await assetsApi.generateAll(projectId)
      await fetchAssets(projectId)
    } finally {
      loading.value = false
    }
  }

  return { characters, scenes, loading, fetchAssets, generateAll }
})