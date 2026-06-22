export type MediaCapability = 'chat' | 'image' | 'video'

export type MediaJobStatus = 'created' | 'queued' | 'running' | 'succeeded' | 'failed' | 'cancelled'

export interface ModelConfig {
  id: number
  provider_id: number
  capability: MediaCapability
  capability_type?: MediaCapability
  model_id: string
  display_name: string
  is_default: boolean
  enabled: boolean
  default_params_json: Record<string, any>
  param_schema_json: Record<string, any>
  capabilities_json: Record<string, any>
}

export interface ProviderConfig {
  id: number
  name: string
  provider_type: string
  auth_type: string
  base_url: string
  api_key_masked: string
  enabled: boolean
  priority: number
  headers_json: Record<string, any>
  config_json: Record<string, any>
  models: ModelConfig[]
  created_at?: string
}

export interface ProviderCreate {
  name: string
  provider_type: string
  auth_type: string
  base_url: string
  api_key: string
  enabled?: boolean
  priority?: number
  headers_json?: Record<string, any>
  config_json?: Record<string, any>
}

export interface ProviderUpdate {
  name?: string
  provider_type?: string
  auth_type?: string
  base_url?: string
  api_key?: string
  enabled?: boolean
  priority?: number
  headers_json?: Record<string, any>
  config_json?: Record<string, any>
}

export interface ModelConfigCreate {
  capability: MediaCapability
  capability_type?: MediaCapability
  model_id: string
  display_name: string
  is_default?: boolean
  enabled?: boolean
  default_params_json?: Record<string, any>
  param_schema_json?: Record<string, any>
  capabilities_json?: Record<string, any>
}

export interface TestResult {
  success: boolean
  message: string
  models_found: number
}

export interface DefaultsMap {
  [capability: string]: {
    model_id: string
    display_name: string
    provider_name: string
    provider_type: string
    base_url: string
  }
}

export interface MediaJob {
  id: number
  capability: MediaCapability
  provider_id: number | null
  model_id: string
  provider_job_id: string | null
  status: MediaJobStatus
  progress: number
  request_json: Record<string, any>
  response_json: Record<string, any>
  result_assets_json: any[]
  error: string | null
  created_at?: string
  updated_at?: string
}

export interface CatalogProvider {
  name: string
  provider_type: string
  auth_type: string
  base_url: string
  priority?: number
  config_json?: Record<string, any>
  models: Array<{
    model_id: string
    display_name: string
    capability: MediaCapability
    is_default?: boolean
  }>
}
