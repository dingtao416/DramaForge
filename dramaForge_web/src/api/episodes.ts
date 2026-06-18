import api from './client'
import type { EpisodeOverview, EpisodeDetail } from '@/types/episode'

export const episodesApi = {
  /** 分集列表（含统计） */
  list(projectId: number) {
    return api.get<EpisodeOverview[]>(`/projects/${projectId}/episodes`)
  },

  /** 分集详情 */
  get(projectId: number, episodeId: number) {
    return api.get<EpisodeDetail>(`/projects/${projectId}/episodes/${episodeId}`)
  },

  /** 重新生成单集内容 */
  regenerate(projectId: number, episodeId: number, data?: { user_prompt?: string; keep_storyboard?: boolean }) {
    return api.post<{ message: string; episode_id: number; title: string; content_length: number }>(
      `/projects/${projectId}/episodes/${episodeId}/regenerate`,
      data || {},
    )
  },
}