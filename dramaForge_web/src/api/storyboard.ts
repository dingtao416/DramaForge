import api, { getToken } from './client'
import type { ShotUpdate, ShotDetail, StoryboardDetail, StoryboardGenerateRequest } from '@/types/shot'

export const storyboardApi = {
  /** 生成分镜脚本 */
  generate(projectId: number, episodeId: number, data?: StoryboardGenerateRequest) {
    return api.post<StoryboardDetail>(`/projects/${projectId}/episodes/${episodeId}/storyboard`, data || {})
  },

  /** 获取分镜 */
  get(projectId: number, episodeId: number) {
    return api.get<StoryboardDetail>(`/projects/${projectId}/episodes/${episodeId}/storyboard`)
  },

  /** 编辑分镜 */
  updateShot(projectId: number, episodeId: number, shotId: number, data: ShotUpdate) {
    return api.put<ShotDetail>(`/projects/${projectId}/episodes/${episodeId}/shots/${shotId}`, data)
  },

  /** 生成单片段视频 */
  generateSegment(projectId: number, episodeId: number, segmentId: number) {
    return api.post(`/projects/${projectId}/episodes/${episodeId}/segments/${segmentId}/generate`)
  },

  /** 重新生成片段 */
  regenerateSegment(projectId: number, episodeId: number, segmentId: number) {
    return api.post(`/projects/${projectId}/episodes/${episodeId}/segments/${segmentId}/regenerate`)
  },

  /** 合成全集视频 */
  composeEpisode(projectId: number, episodeId: number, options?: {
    quality?: string
    resolution?: string
    subtitle_text?: string
    subtitle_font_size?: number
    subtitle_position?: string
    bgm_volume?: number
  }) {
    return api.post(`/projects/${projectId}/episodes/${episodeId}/compose`, options || {})
  },

  /** 导出项目 */
  exportProject(projectId: number) {
    return api.post(`/projects/${projectId}/export`)
  },

  /** 下载剧集视频 */
  async downloadEpisode(projectId: number, episodeId: number) {
    const token = getToken()
    const baseURL = import.meta.env.VITE_API_BASE_URL || ''
    const url = `${baseURL}/projects/${projectId}/episodes/${episodeId}/download`

    const res = await fetch(url, {
      headers: { 'Authorization': `Bearer ${token}` },
    })
    if (!res.ok) {
      const errData = await res.json().catch(() => ({}))
      throw new Error((errData as any).detail || 'Download failed')
    }
    const blob = await res.blob()
    const blobUrl = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = blobUrl
    link.download = `episode_video.mp4`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(blobUrl)
  },

  /** 手动添加分镜 */
  createShot(projectId: number, episodeId: number, segmentId: number) {
    return api.post<ShotDetail>(`/projects/${projectId}/episodes/${episodeId}/segments/${segmentId}/shots`)
  },

  /** 删除分镜 */
  deleteShot(projectId: number, episodeId: number, shotId: number) {
    return api.delete(`/projects/${projectId}/episodes/${episodeId}/shots/${shotId}`)
  },

  /** 上传BGM */
  uploadBgm(projectId: number, file: File) {
    const form = new FormData()
    form.append('file', file)
    return api.post(`/projects/${projectId}/bgm/upload`, form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  /** 批量更新分镜 */
  batchUpdateShots(projectId: number, episodeId: number, data: { shot_ids: number[]; camera_type?: string; camera_angle?: string; camera_movement?: string; transition?: string; time_of_day?: string; voice_style?: string }) {
    return api.put(`/projects/${projectId}/episodes/${episodeId}/shots/batch`, data)
  },
}