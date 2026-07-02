import apiClient from './client'
import type {
  CatalogProvider,
  DefaultsMap,
  MediaJob,
  ModelConfig,
  ModelConfigCreate,
  ProviderConfig,
  ProviderCreate,
  ProviderUpdate,
  TestResult,
  VideoModelPreset,
} from '@/types/user-ai-config'

export async function listProviders(): Promise<ProviderConfig[]> {
  const { data } = await apiClient.get<ProviderConfig[]>('/user-ai/providers')
  return data
}

export async function createProvider(payload: ProviderCreate): Promise<ProviderConfig> {
  const { data } = await apiClient.post<ProviderConfig>('/user-ai/providers', payload)
  return data
}

export async function updateProvider(id: number, payload: ProviderUpdate): Promise<ProviderConfig> {
  const { data } = await apiClient.put<ProviderConfig>(`/user-ai/providers/${id}`, payload)
  return data
}

export async function deleteProvider(id: number): Promise<void> {
  await apiClient.delete(`/user-ai/providers/${id}`)
}

export async function testProvider(id: number): Promise<TestResult> {
  const { data } = await apiClient.post<TestResult>(`/user-ai/providers/${id}/test`)
  return data
}

export async function discoverModels(id: number): Promise<{ models: string[]; count: number }> {
  const { data } = await apiClient.post(`/user-ai/providers/${id}/discover`)
  return data
}

export async function discoverModelsFromUrl(payload: {
  provider_type: string
  auth_type: string
  base_url: string
  api_key: string
}): Promise<{ models: string[]; count: number }> {
  const { data } = await apiClient.post('/user-ai/discover', payload)
  return data
}

export async function createModel(providerId: number, payload: ModelConfigCreate): Promise<ModelConfig> {
  const body = { ...payload, capability: payload.capability ?? payload.capability_type }
  delete (body as any).capability_type
  const { data } = await apiClient.post<ModelConfig>(`/user-ai/providers/${providerId}/models`, body)
  return data
}

export async function updateModel(id: number, payload: Partial<ModelConfigCreate>): Promise<ModelConfig> {
  const body = { ...payload, capability: payload.capability ?? payload.capability_type }
  delete (body as any).capability_type
  const { data } = await apiClient.put<ModelConfig>(`/user-ai/models/${id}`, body)
  return data
}

export async function deleteModel(id: number): Promise<void> {
  await apiClient.delete(`/user-ai/models/${id}`)
}

export async function setDefaultModel(id: number): Promise<ModelConfig> {
  const { data } = await apiClient.put<ModelConfig>(`/user-ai/models/${id}/set-default`)
  return data
}

export async function getDefaults(): Promise<DefaultsMap> {
  const { data } = await apiClient.get<DefaultsMap>('/user-ai/defaults')
  return data
}

export async function listJobs(limit = 50): Promise<MediaJob[]> {
  const { data } = await apiClient.get<MediaJob[]>('/user-ai/jobs', { params: { limit } })
  return data
}

export async function getJob(id: number): Promise<MediaJob> {
  const { data } = await apiClient.get<MediaJob>(`/user-ai/jobs/${id}`)
  return data
}

export async function cancelJob(id: number): Promise<MediaJob> {
  const { data } = await apiClient.post<MediaJob>(`/user-ai/jobs/${id}/cancel`)
  return data
}

export async function listCatalog(): Promise<CatalogProvider[]> {
  const { data } = await apiClient.get<CatalogProvider[]>('/user-ai/catalog')
  return data
}

export async function listVideoModelPresets(): Promise<VideoModelPreset[]> {
  const { data } = await apiClient.get<VideoModelPreset[]>('/user-ai/video-model-presets')
  return data
}

export async function importCatalog(index: number): Promise<ProviderConfig> {
  const { data } = await apiClient.post<ProviderConfig>(`/user-ai/catalog/import?catalog_index=${index}`)
  return data
}
