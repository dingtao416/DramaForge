import api from './client'
import type { ScriptGenerateRequest, ScriptUpdate, ScriptDetail, EpisodeUpdate } from '@/types/script'

export const scriptsApi = {
  /** AI 生成剧本 */
  generate(projectId: number, data: ScriptGenerateRequest) {
    return api.post<ScriptDetail>(`/projects/${projectId}/script/generate`, data)
  },

  /** 上传 .docx 剧本 */
  upload(projectId: number, file: File, totalEpisodes = 1) {
    const form = new FormData()
    form.append('file', file)
    form.append('total_episodes', String(totalEpisodes))
    return api.post<ScriptDetail>(`/projects/${projectId}/script/upload`, form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  /** 获取剧本 */
  get(projectId: number) {
    return api.get<ScriptDetail>(`/projects/${projectId}/script`)
  },

  /** 更新剧本 */
  update(projectId: number, data: ScriptUpdate) {
    return api.put<ScriptDetail>(`/projects/${projectId}/script`, data)
  },

  /** 更新单集 */
  updateEpisode(projectId: number, episodeId: number, data: EpisodeUpdate) {
    return api.put<ScriptDetail>(`/projects/${projectId}/episodes/${episodeId}`, data)
  },

  /** 改写为旁白型 */
  rewriteNarration(projectId: number) {
    return api.post<ScriptDetail>(`/projects/${projectId}/script/rewrite-narration`)
  },

  /** 审核通过 */
  approve(projectId: number) {
    return api.post<ScriptDetail>(`/projects/${projectId}/script/approve`)
  },
}