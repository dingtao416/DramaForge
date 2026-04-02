import type { ProjectStep, VideoStyle, DramaGenre } from './enums'

export interface ProjectCreate {
  title: string
  description?: string
  style?: VideoStyle
  aspect_ratio?: string
  genre?: DramaGenre
  script_type?: string
}

export interface ProjectUpdate {
  title?: string
  description?: string
  style?: VideoStyle
  aspect_ratio?: string
  genre?: DramaGenre
  script_type?: string
  status?: ProjectStep
}

export interface ProjectList {
  id: number
  title: string
  description: string
  style: VideoStyle
  genre: DramaGenre
  status: ProjectStep
  created_at: string
  updated_at: string
}

export interface ProjectDetail extends ProjectList {
  aspect_ratio: string
  script_type: string
}