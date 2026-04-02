import type { SegmentDetail } from './segment'

export interface ShotCharacterRef {
  char_id: number
  appearance_idx: number
  action: string
}

export interface ShotDetail {
  id: number
  segment_id: number
  index: number
  duration: number
  time_of_day: string
  scene_ref: string
  camera_type: string
  camera_angle: string
  camera_movement: string
  characters: ShotCharacterRef[]
  dialogue: string
  voice_style: string
  background: string
  transition: string
  image_prompt: string
  video_prompt: string
  image_url: string | null
  audio_url: string | null
  video_url: string | null
  created_at: string
}

export interface ShotUpdate {
  duration?: number
  time_of_day?: string
  scene_ref?: string
  camera_type?: string
  camera_angle?: string
  camera_movement?: string
  characters?: ShotCharacterRef[]
  dialogue?: string
  voice_style?: string
  background?: string
  transition?: string
  image_prompt?: string
  video_prompt?: string
}

export interface StoryboardDetail {
  episode_id: number
  episode_title: string
  segments: SegmentDetail[]
  total_duration: number
  total_shots: number
}

export interface StoryboardGenerateRequest {
  shots_per_segment?: number
  force?: boolean
}