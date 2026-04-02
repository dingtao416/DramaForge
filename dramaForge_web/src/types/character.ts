import type { CharacterRole } from './enums'

export interface CharacterDetail {
  id: number
  project_id: number
  name: string
  role: CharacterRole
  description: string
  voice_desc: string
  reference_images: string[]
  created_at: string
}

export interface CharacterUpdate {
  name?: string
  role?: CharacterRole
  description?: string
  voice_desc?: string
  reference_images?: string[]
}

export interface CharacterRegenerateRequest {
  prompt?: string
}