import type { SegmentStatus } from './enums'
import type { ShotDetail } from './shot'

export interface SegmentDetail {
  id: number
  episode_id: number
  index: number
  status: SegmentStatus
  video_url: string | null
  audio_url: string | null
  thumbnail_url: string | null
  duration: number | null
  shots: ShotDetail[]
  created_at: string
}