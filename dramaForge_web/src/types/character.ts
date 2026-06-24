import type { CharacterRole } from './enums'

/** 单张形象图 */
export interface RefImage {
  url: string
  name: string
  is_primary?: boolean
  /** 形象描述 — 作为AI生成的prompt */
  description?: string
}

export interface CharacterDetail {
  id: number
  project_id: number
  name: string
  role: CharacterRole
  description: string
  voice_desc: string
  reference_images: RefImage[]
  created_at: string
}

export interface CharacterUpdate {
  name?: string
  role?: CharacterRole
  description?: string
  voice_desc?: string
  reference_images?: RefImage[]
}

export interface CharacterRegenerateRequest {
  prompt?: string
}
