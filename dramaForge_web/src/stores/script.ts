import { defineStore } from 'pinia'
import { ref } from 'vue'
import { scriptsApi } from '@/api/scripts'
import type { ScriptDetail } from '@/types/script'

export const useScriptStore = defineStore('script', () => {
  const script = ref<ScriptDetail | null>(null)
  const loading = ref(false)

  async function fetchScript(projectId: number) {
    loading.value = true
    try {
      const { data } = await scriptsApi.get(projectId)
      script.value = data
    } catch {
      script.value = null
    } finally {
      loading.value = false
    }
  }

  async function approveScript(projectId: number) {
    const { data } = await scriptsApi.approve(projectId)
    script.value = data
  }

  async function rewriteNarration(projectId: number) {
    loading.value = true
    try {
      const { data } = await scriptsApi.rewriteNarration(projectId)
      script.value = data
    } finally {
      loading.value = false
    }
  }

  return { script, loading, fetchScript, approveScript, rewriteNarration }
})