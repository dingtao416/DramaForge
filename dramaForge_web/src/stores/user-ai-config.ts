/**
 * DramaForge — User AI Configuration Store
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { UserAPIKey, ModelConfig, DefaultsMap, DiscoveredModel } from '@/types/user-ai-config'
import * as aiConfigApi from '@/api/user-ai-config'

export const useUserAIConfigStore = defineStore('user-ai-config', () => {
  const keys = ref<UserAPIKey[]>([])
  const defaults = ref<DefaultsMap>({})
  const loading = ref(false)

  // ── Computed ──

  /** All models grouped by capability type */
  const modelsByType = computed(() => {
    const result: Record<string, (ModelConfig & { provider_name: string })[]> = {
      chat: [],
      image: [],
      video: [],
      tts: [],
    }
    for (const key of keys.value) {
      if (!key.enabled) continue
      for (const model of key.models) {
        if (!model.enabled) continue
        result[model.capability_type]?.push({
          ...model,
          provider_name: key.name,
        })
      }
    }
    return result
  })

  // ── Actions ──

  async function fetchKeys() {
    loading.value = true
    try {
      keys.value = await aiConfigApi.listKeys()
    } finally {
      loading.value = false
    }
  }

  async function fetchDefaults() {
    defaults.value = await aiConfigApi.getDefaults()
  }

  async function addKey(data: { name: string; base_url: string; api_key: string; capabilities: string }) {
    const key = await aiConfigApi.createKey(data)
    keys.value.push(key)
    return key
  }

  async function updateKey(id: number, data: Record<string, any>) {
    const updated = await aiConfigApi.updateKey(id, data)
    const idx = keys.value.findIndex(k => k.id === id)
    if (idx >= 0) keys.value[idx] = updated
    return updated
  }

  async function removeKey(id: number) {
    await aiConfigApi.deleteKey(id)
    keys.value = keys.value.filter(k => k.id !== id)
  }

  async function testKey(id: number) {
    return await aiConfigApi.testConnection(id)
  }

  async function discoverModels(keyId: number) {
    return await aiConfigApi.discoverModels(keyId)
  }

  async function addModel(keyId: number, data: { capability_type: string; model_id: string; display_name: string; is_default?: boolean }) {
    const model = await aiConfigApi.createModel(keyId, data)
    const key = keys.value.find(k => k.id === keyId)
    if (key) key.models.push(model)
    return model
  }

  async function removeModel(modelId: number) {
    await aiConfigApi.deleteModel(modelId)
    for (const key of keys.value) {
      key.models = key.models.filter(m => m.id !== modelId)
    }
  }

  async function setDefault(modelId: number) {
    const updated = await aiConfigApi.setDefaultModel(modelId)
    // Unset other defaults of the same type
    for (const key of keys.value) {
      for (const m of key.models) {
        if (m.capability_type === updated.capability_type) {
          m.is_default = m.id === modelId
        }
      }
    }
    await fetchDefaults()
    return updated
  }

  /** Get models for a capability type (for HomePage model selector) */
  function getModelsForType(type: string) {
    return modelsByType.value[type] || []
  }

  return {
    keys,
    defaults,
    loading,
    modelsByType,
    fetchKeys,
    fetchDefaults,
    addKey,
    updateKey,
    removeKey,
    testKey,
    discoverModels,
    addModel,
    removeModel,
    setDefault,
    getModelsForType,
  }
})
