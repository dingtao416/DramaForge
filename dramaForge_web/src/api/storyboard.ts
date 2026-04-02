import api from './client'
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
  composeEpisode(projectId: number, episodeId: number) {
    return api.post(`/projects/${projectId}/episodes/${episodeId}/compose`)
  },

  /** 导出项目 */
  exportProject(projectId: number) {
    return api.post(`/projects/${projectId}/export`)
  },
}