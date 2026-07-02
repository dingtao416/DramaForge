import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import type {
  DefaultsMap,
  MediaJob,
  ModelConfig,
  ModelConfigCreate,
  ProviderConfig,
  ProviderCreate,
  VideoModelPreset,
} from '@/types/user-ai-config'
import * as aiConfigApi from '@/api/user-ai-config'

export const useUserAIConfigStore = defineStore('user-ai-config', () => {
  const providers = ref<ProviderConfig[]>([])
  const videoModelPresets = ref<VideoModelPreset[]>([])
  const defaults = ref<DefaultsMap>({})
  const jobs = ref<MediaJob[]>([])
  const loading = ref(false)

  const keys = providers

  const modelsByType = computed(() => {
    const result: Record<string, (ModelConfig & { provider_name: string; capability_type: string })[]> = {
      image: [],
      video: [],
      chat: [],
      tts: [],
    }
    for (const provider of providers.value) {
      if (!provider.enabled) continue
      for (const model of provider.models) {
        if (!model.enabled) continue
        const capability = model.capability || model.capability_type
        result[capability]?.push({
          ...model,
          capability_type: capability,
          provider_name: provider.name,
        })
      }
    }
    return result
  })

  async function fetchKeys() {
    return fetchProviders()
  }

  async function fetchProviders() {
    loading.value = true
    try {
      providers.value = await aiConfigApi.listProviders()
    } finally {
      loading.value = false
    }
  }

  async function fetchDefaults() {
    defaults.value = await aiConfigApi.getDefaults()
  }

  async function fetchVideoModelPresets() {
    videoModelPresets.value = await aiConfigApi.listVideoModelPresets()
  }

  async function addKey(data: ProviderCreate) {
    return addProvider(data)
  }

  async function addProvider(data: ProviderCreate) {
    const provider = await aiConfigApi.createProvider(data)
    providers.value.push(provider)
    return provider
  }

  async function updateKey(id: number, data: Record<string, any>) {
    return updateProvider(id, data)
  }

  async function updateProvider(id: number, data: Record<string, any>) {
    const updated = await aiConfigApi.updateProvider(id, data)
    const idx = providers.value.findIndex((p) => p.id === id)
    if (idx >= 0) providers.value[idx] = updated
    return updated
  }

  async function removeKey(id: number) {
    return removeProvider(id)
  }

  async function removeProvider(id: number) {
    await aiConfigApi.deleteProvider(id)
    providers.value = providers.value.filter((p) => p.id !== id)
  }

  async function testKey(id: number) {
    return aiConfigApi.testProvider(id)
  }

  async function discoverModels(providerId: number) {
    return aiConfigApi.discoverModels(providerId)
  }

  async function discoverModelsFromUrl(payload: {
    provider_type: string
    auth_type: string
    base_url: string
    api_key: string
  }) {
    return aiConfigApi.discoverModelsFromUrl(payload)
  }

  async function addModel(providerId: number, data: ModelConfigCreate) {
    const model = await aiConfigApi.createModel(providerId, data)
    const provider = providers.value.find((p) => p.id === providerId)
    if (provider) provider.models.push(model)
    return model
  }

  async function updateModel(modelId: number, data: Partial<ModelConfigCreate>) {
    const model = await aiConfigApi.updateModel(modelId, data)
    for (const provider of providers.value) {
      const idx = provider.models.findIndex((m) => m.id === modelId)
      if (idx >= 0) provider.models[idx] = model
    }
    return model
  }

  async function removeModel(modelId: number) {
    await aiConfigApi.deleteModel(modelId)
    for (const provider of providers.value) {
      provider.models = provider.models.filter((m) => m.id !== modelId)
    }
  }

  async function setDefault(modelId: number) {
    const updated = await aiConfigApi.setDefaultModel(modelId)
    const capability = updated.capability || updated.capability_type
    for (const provider of providers.value) {
      for (const model of provider.models) {
        if ((model.capability || model.capability_type) === capability) {
          model.is_default = model.id === modelId
        }
      }
    }
    await fetchDefaults()
    return updated
  }

  function getModelsForType(type: string) {
    return modelsByType.value[type] || []
  }

  async function fetchJobs() {
    jobs.value = await aiConfigApi.listJobs()
  }

  async function cancelJob(jobId: number) {
    const job = await aiConfigApi.cancelJob(jobId)
    const idx = jobs.value.findIndex((item) => item.id === job.id)
    if (idx >= 0) jobs.value[idx] = job
    return job
  }

  return {
    providers,
    videoModelPresets,
    keys,
    defaults,
    jobs,
    loading,
    modelsByType,
    fetchKeys,
    fetchProviders,
    fetchDefaults,
    fetchVideoModelPresets,
    addKey,
    addProvider,
    updateKey,
    updateProvider,
    removeKey,
    removeProvider,
    testKey,
    discoverModels,
    discoverModelsFromUrl,
    addModel,
    updateModel,
    removeModel,
    setDefault,
    getModelsForType,
    fetchJobs,
    cancelJob,
  }
})
