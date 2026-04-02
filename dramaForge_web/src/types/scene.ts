export interface SceneDetail {
  id: number
  project_id: number
  name: string
  description: string
  time_of_day: string
  interior: boolean
  reference_images: string[]
  created_at: string
}

export interface SceneUpdate {
  name?: string
  description?: string
  time_of_day?: string
  interior?: boolean
  reference_images?: string[]
}

export interface SceneRegenerateRequest {
  prompt?: string
}

export interface AssetsGenerateRequest {
  force?: boolean
}