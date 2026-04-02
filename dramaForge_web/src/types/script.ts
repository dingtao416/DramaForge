export interface ScriptGenerateRequest {
  user_input: string
  genre?: string
  total_episodes?: number
  duration_per_episode?: number
}

export interface ScriptUploadRequest {
  total_episodes?: number
}

export interface ScriptUpdate {
  protagonist?: string
  genre?: string
  synopsis?: string
  background?: string
  setting?: string
  one_liner?: string
  raw_content?: string
}

export interface EpisodeBrief {
  id: number
  number: number
  title: string
  is_approved: boolean
}

export interface EpisodeUpdate {
  title?: string
  content?: string
}

export interface ScriptDetail {
  id: number
  project_id: number
  protagonist: string
  genre: string
  synopsis: string
  background: string
  setting: string
  one_liner: string
  raw_content: string
  is_approved: boolean
  created_at: string
  episodes: EpisodeBrief[]
}