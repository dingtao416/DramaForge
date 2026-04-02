import api from './client'
import type { CharacterDetail, CharacterUpdate } from '@/types/character'
import type { SceneDetail, SceneUpdate, AssetsGenerateRequest } from '@/types/scene'

export const assetsApi = {
  /** 生成全部资产 */
  generateAll(projectId: number, data?: AssetsGenerateRequest) {
    return api.post(`/projects/${projectId}/assets/generate`, data || {})
  },

  /** 获取角色列表 */
  getCharacters(projectId: number) {
    return api.get<CharacterDetail[]>(`/projects/${projectId}/characters`)
  },

  /** 更新角色 */
  updateCharacter(projectId: number, charId: number, data: CharacterUpdate) {
    return api.put<CharacterDetail>(`/projects/${projectId}/characters/${charId}`, data)
  },

  /** 重新生成角色形象 */
  regenerateCharacter(projectId: number, charId: number, prompt?: string) {
    return api.post<CharacterDetail>(`/projects/${projectId}/characters/${charId}/regenerate`, { prompt })
  },

  /** 获取场景列表 */
  getScenes(projectId: number) {
    return api.get<SceneDetail[]>(`/projects/${projectId}/scenes`)
  },

  /** 更新场景 */
  updateScene(projectId: number, sceneId: number, data: SceneUpdate) {
    return api.put<SceneDetail>(`/projects/${projectId}/scenes/${sceneId}`, data)
  },

  /** 重新生成场景形象 */
  regenerateScene(projectId: number, sceneId: number, prompt?: string) {
    return api.post<SceneDetail>(`/projects/${projectId}/scenes/${sceneId}/regenerate`, { prompt })
  },

  /** 审核通过全部资产 */
  approve(projectId: number) {
    return api.post(`/projects/${projectId}/assets/approve`)
  },

  // ── 全局资产库 ──

  /** 全局资产列表 */
  listGlobal(params?: { skip?: number; limit?: number }) {
    return api.get<CharacterDetail[]>('/assets', { params })
  },

  /** 全局角色资产 */
  listGlobalCharacters() {
    return api.get<CharacterDetail[]>('/assets/characters')
  },

  /** 删除资产 */
  deleteAsset(assetId: number) {
    return api.delete(`/assets/${assetId}`)
  },
}