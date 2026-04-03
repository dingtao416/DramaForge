import api from './client'
import type { ProjectCreate, ProjectUpdate, ProjectList, ProjectDetail } from '@/types/project'

export const projectsApi = {
  /** 创建项目 */
  create(data: ProjectCreate) {
    return api.post<ProjectDetail>('/projects', data)
  },

  /** 项目列表 */
  list(params?: { skip?: number; limit?: number }) {
    return api.get<ProjectList[]>('/projects', { params })
  },

  /** 项目详情 */
  get(id: number) {
    return api.get<ProjectDetail>(`/projects/${id}`)
  },

  /** 更新项目 */
  update(id: number, data: ProjectUpdate) {
    return api.put<ProjectDetail>(`/projects/${id}`, data)
  },

  /** 删除项目 */
  delete(id: number) {
    return api.delete(`/projects/${id}`)
  },

  /** 创建示例项目 */
  seedExamples() {
    return api.post<ProjectDetail[]>('/projects/seed-examples')
  },
}
