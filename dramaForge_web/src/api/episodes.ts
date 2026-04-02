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
}