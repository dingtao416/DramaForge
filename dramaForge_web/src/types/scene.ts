import type { RefImage } from './character'

export type SceneReferenceImage = string | RefImage

/** 场景状态类型 */
export const SceneStateType = {
  DEFAULT: 'default',
  DAY: 'day',
  NIGHT: 'night',
  DAMAGED: 'damaged',
  CELEBRATION: 'celebration',
  REMINISCENCE: 'reminiscence',
  FESTIVE: 'festive',
} as const
export type SceneStateType = typeof SceneStateType[keyof typeof SceneStateType]

export const SceneStateTypeLabel: Record<string, string> = {
  [SceneStateType.DEFAULT]: '默认',
  [SceneStateType.DAY]: '白天',
  [SceneStateType.NIGHT]: '夜晚',
  [SceneStateType.DAMAGED]: '破损',
  [SceneStateType.CELEBRATION]: '庆典',
  [SceneStateType.REMINISCENCE]: '回忆',
  [SceneStateType.FESTIVE]: '节日',
}

/** Available scene states for quick generation */
export const SCENE_STATE_OPTIONS = [
  { type: SceneStateType.DAY, label: '☀️ 白天', prompt: 'daytime, bright sunlight, clear atmosphere' },
  { type: SceneStateType.NIGHT, label: '🌙 夜晚', prompt: 'night scene, moonlight, atmospheric darkness, ambient lighting' },
  { type: SceneStateType.DAMAGED, label: '💥 破损', prompt: 'damaged, ruined, post-conflict, debris scattered' },
  { type: SceneStateType.CELEBRATION, label: '🎉 庆典', prompt: 'festive celebration, decorations, joyful crowd, bright colors' },
  { type: SceneStateType.REMINISCENCE, label: '💭 回忆', prompt: 'nostalgic, soft focus, warm vintage tones, dreamlike haze' },
]

export interface SceneDetail {
  id: number
  project_id: number
  name: string
  description: string
  time_of_day: string
  interior: boolean
  reference_images: SceneReferenceImage[]
  created_at: string
}

export interface SceneUpdate {
  name?: string
  description?: string
  time_of_day?: string
  interior?: boolean
  reference_images?: SceneReferenceImage[]
}

export interface SceneRegenerateRequest {
  prompt?: string
}

export interface AssetsGenerateRequest {
  force?: boolean
}
