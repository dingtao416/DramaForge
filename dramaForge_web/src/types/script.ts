export interface ScriptGenerateRequest {
  user_input: string
  genre?: string
  total_episodes?: number
  duration_per_episode?: number
  preserve_episodes?: boolean
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
  // Story Bible fields
  premise?: string
  world_rules?: string
  character_relationships?: string
  timeline?: string
  episode_arc?: string
  visual_style_rules?: string
  continuity_notes?: string
}

export interface StoryBible {
  premise: string
  world_rules: string
  character_relationships: string
  timeline: string
  episode_arc: string
  visual_style_rules: string
  continuity_notes: string
}

export type StoryBibleUpdate = Partial<StoryBible>

export interface StoryBibleDraftRequest {
  user_input?: string
  genre?: string
  total_episodes?: number
  duration_per_episode?: number
  overwrite?: boolean
}

export interface EpisodeBrief {
  id: number
  number: number
  title: string
  content: string
  is_approved: boolean
}

export interface EpisodeUpdate {
  title?: string
  content?: string
}

export interface ScriptDetail extends StoryBible {
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
  warnings?: string[]
}
