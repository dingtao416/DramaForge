/**
 * DramaForge — User AI Configuration Types
 * Types for user-configured API keys and model preferences.
 */

export interface ModelConfig {
  id: number
  api_key_id: number
  capability_type: 'chat' | 'image' | 'video' | 'tts'
  model_id: string
  display_name: string
  is_default: boolean
  enabled: boolean
}

export interface UserAPIKey {
  id: number
  name: string
  base_url: string
  api_key_masked: string
  capabilities: string[]
  is_default: boolean
  enabled: boolean
  models: ModelConfig[]
  created_at?: string
}

export interface APIKeyCreate {
  name: string
  base_url: string
  api_key: string
  capabilities: string
  is_default?: boolean
}

export interface APIKeyUpdate {
  name?: string
  base_url?: string
  api_key?: string
  capabilities?: string
  is_default?: boolean
  enabled?: boolean
}

export interface ModelConfigCreate {
  capability_type: string
  model_id: string
  display_name: string
  is_default?: boolean
}

export interface TestResult {
  success: boolean
  message: string
  models_found: number
}

export interface DiscoveredModel {
  model_id: string
  capability_type: string
  display_name: string
}

export interface DefaultsMap {
  [capability: string]: {
    model_id: string
    display_name: string
    provider_name: string
    base_url: string
  }
}
