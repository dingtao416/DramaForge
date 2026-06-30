import { defineStore } from 'pinia'
import { ref } from 'vue'
import { scriptsApi } from '@/api/scripts'
import type { ScriptDetail, ScriptUpdate, StoryBible, StoryBibleDraftRequest, StoryBibleUpdate } from '@/types/script'

export const useScriptStore = defineStore('script', () => {
  const script = ref<ScriptDetail | null>(null)
  const storyBible = ref<StoryBible | null>(null)
  const loading = ref(false)

  async function fetchScript(projectId: number) {
    loading.value = true
    try {
      const { data } = await scriptsApi.get(projectId)
      script.value = data
      storyBible.value = pickStoryBible(data)
    } catch {
      script.value = null
    } finally {
      loading.value = false
    }
  }

  async function updateScript(projectId: number, data: ScriptUpdate) {
    const { data: updated } = await scriptsApi.update(projectId, data)
    script.value = updated
  }

  async function updateStoryBible(projectId: number, data: StoryBibleUpdate) {
    const { data: bible } = await scriptsApi.updateStoryBible(projectId, data)
    storyBible.value = bible
    if (script.value) {
      script.value = { ...script.value, ...bible }
    }
  }

  async function fetchStoryBible(projectId: number) {
    const { data: bible } = await scriptsApi.getStoryBible(projectId)
    storyBible.value = bible
    if (script.value) {
      script.value = { ...script.value, ...bible }
    }
    return bible
  }

  async function draftStoryBible(projectId: number, data: StoryBibleDraftRequest) {
    const { data: bible } = await scriptsApi.draftStoryBible(projectId, data)
    storyBible.value = bible
    if (script.value) {
      script.value = { ...script.value, ...bible }
    }
    return bible
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

  /**
   * Rewrite narration with SSE streaming.
   * Returns the accumulated content so the UI can display it in real-time.
   */
  async function rewriteNarrationStream(
    projectId: number,
    handlers: {
      onContent?: (chunk: string) => void
      onDone?: (content: string) => void
      onError?: (error: string) => void
    },
    signal?: AbortSignal,
  ) {
    await scriptsApi.rewriteNarrationStream(projectId, handlers, signal)
  }

  return {
    script,
    storyBible,
    loading,
    fetchScript,
    fetchStoryBible,
    updateScript,
    updateStoryBible,
    draftStoryBible,
    approveScript,
    rewriteNarration,
    rewriteNarrationStream,
  }
})

function pickStoryBible(script: ScriptDetail): StoryBible {
  return {
    premise: script.premise || '',
    world_rules: script.world_rules || '',
    character_relationships: script.character_relationships || '',
    timeline: script.timeline || '',
    episode_arc: script.episode_arc || '',
    visual_style_rules: script.visual_style_rules || '',
    continuity_notes: script.continuity_notes || '',
  }
}
