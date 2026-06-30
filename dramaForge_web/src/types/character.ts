import type { CharacterRole } from './enums'

/** 形象类型 */
export const CharacterAppearanceType = {
  STANDARD: 'standard',
  TURNAROUND_FRONT: 'turnaround_front',
  TURNAROUND_SIDE: 'turnaround_side',
  TURNAROUND_BACK: 'turnaround_back',
  STAGE_EARLY: 'stage_early',
  STAGE_MID: 'stage_mid',
  STAGE_LATE: 'stage_late',
} as const
export type CharacterAppearanceType = typeof CharacterAppearanceType[keyof typeof CharacterAppearanceType]

export const CharacterAppearanceTypeLabel: Record<string, string> = {
  [CharacterAppearanceType.STANDARD]: '标准形象',
  [CharacterAppearanceType.TURNAROUND_FRONT]: '正面',
  [CharacterAppearanceType.TURNAROUND_SIDE]: '侧面',
  [CharacterAppearanceType.TURNAROUND_BACK]: '背面',
  [CharacterAppearanceType.STAGE_EARLY]: '前期形象',
  [CharacterAppearanceType.STAGE_MID]: '转折后',
  [CharacterAppearanceType.STAGE_LATE]: '结局形象',
}

/** 三视图类型组 */
export const TURNAROUND_TYPES = [
  CharacterAppearanceType.TURNAROUND_FRONT,
  CharacterAppearanceType.TURNAROUND_SIDE,
  CharacterAppearanceType.TURNAROUND_BACK,
]

/** 阶段形象类型组 */
export const STAGE_TYPES = [
  CharacterAppearanceType.STAGE_EARLY,
  CharacterAppearanceType.STAGE_MID,
  CharacterAppearanceType.STAGE_LATE,
]

/** 单张形象图 */
export interface RefImage {
  url: string
  name: string
  is_primary?: boolean
  /** 形象描述 — 作为AI生成的prompt */
  description?: string
  /** 形象类型 — 区分标准形象/三视图/阶段形象 */
  appearance_type?: string
  /** 场景状态类型 — 场景资产使用 */
  state_type?: string
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
