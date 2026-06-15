/**
 * DramaForge — User AI Configuration API
 */
import apiClient from './client'
import type {
  UserAPIKey,
  APIKeyCreate,
  APIKeyUpdate,
  ModelConfig,
  ModelConfigCreate,
  TestResult,
  DiscoveredModel,
  DefaultsMap,
} from '@/types/user-ai-config'

// ── API Keys ──

export async function listKeys(): Promise<UserAPIKey[]> {
  const { data } = await apiClient.get<UserAPIKey[]>('/user-ai/keys')
  return data
}

export async function createKey(payload: APIKeyCreate): Promise<UserAPIKey> {
  const { data } = await apiClient.post<UserAPIKey>('/user-ai/keys', payload)
  return data
}

export async function updateKey(id: number, payload: APIKeyUpdate): Promise<UserAPIKey> {
  const { data } = await apiClient.put<UserAPIKey>(`/user-ai/keys/${id}`, payload)
  return data
}

export async function deleteKey(id: number): Promise<void> {
  await apiClient.delete(`/user-ai/keys/${id}`)
}

export async function testConnection(id: number): Promise<TestResult> {
  const { data } = await apiClient.post<TestResult>(`/user-ai/keys/${id}/test`)
  return data
}

// ── Models ──

export async function listModels(keyId: number): Promise<ModelConfig[]> {
  const { data } = await apiClient.get<ModelConfig[]>(`/user-ai/keys/${keyId}/models`)
  return data
}

export async function createModel(keyId: number, payload: ModelConfigCreate): Promise<ModelConfig> {
  const { data } = await apiClient.post<ModelConfig>(`/user-ai/keys/${keyId}/models`, payload)
  return data
}

export async function updateModel(id: number, payload: Partial<ModelConfigCreate>): Promise<ModelConfig> {
  const { data } = await apiClient.put<ModelConfig>(`/user-ai/models/${id}`, payload)
  return data
}

export async function deleteModel(id: number): Promise<void> {
  await apiClient.delete(`/user-ai/models/${id}`)
}

export async function setDefaultModel(id: number): Promise<ModelConfig> {
  const { data } = await apiClient.put<ModelConfig>(`/user-ai/models/${id}/set-default`)
  return data
}

// ── Defaults & Discovery ──

export async function getDefaults(): Promise<DefaultsMap> {
  const { data } = await apiClient.get<DefaultsMap>('/user-ai/defaults')
  return data
}

export async function discoverModels(keyId: number): Promise<{ discovered: number; models: DiscoveredModel[] }> {
  const { data } = await apiClient.post(`/user-ai/keys/${keyId}/discover`)
  return data
}
