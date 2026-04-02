export interface EpisodeOverview {
  id: number
  number: number
  title: string
  is_approved: boolean
  character_count: number
  scene_count: number
  segment_count: number
  total_duration: number
  created_at: string
}

export interface EpisodeDetail extends EpisodeOverview {
  content: string
}