import api from './client'
import { getToken } from './client'
import type { ScriptGenerateRequest, ScriptUpdate, ScriptDetail, EpisodeUpdate, StoryBible, StoryBibleDraftRequest, StoryBibleUpdate } from '@/types/script'

export interface ScriptParseResult {
  filename: string
  file_type: string
  char_count: number
  full_text: string
  preview: string
}

export interface ScriptGenerateStreamResult {
  script_id: number
  episode_count: number
  character_count: number
  scene_count: number
}

export const scriptsApi = {
  /** 解析上传的剧本文件（预览，不创建项目） */
  parse(file: File) {
    const form = new FormData()
    form.append('file', file)
    return api.post<ScriptParseResult>('/scripts/parse', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  /** AI 生成剧本（超时 10 分钟，生成多集内容耗时较长） */
  generate(projectId: number, data: ScriptGenerateRequest) {
    return api.post<ScriptDetail>(`/projects/${projectId}/script/generate`, data, {
      timeout: 600_000, // 10 minutes for AI script generation
    })
  },

  /** 上传剧本文件（需要先创建项目） */
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

  /** 获取 Story Bible */
  getStoryBible(projectId: number) {
    return api.get<StoryBible>(`/projects/${projectId}/story-bible`)
  },

  /** 更新 Story Bible */
  updateStoryBible(projectId: number, data: StoryBibleUpdate) {
    return api.put<StoryBible>(`/projects/${projectId}/story-bible`, data)
  },

  /** AI 起草 Story Bible */
  draftStoryBible(projectId: number, data: StoryBibleDraftRequest) {
    return api.post<StoryBible>(`/projects/${projectId}/story-bible/draft`, data)
  },

  /** AI 起草生成前 Story Bible（项目创建前） */
  draftStoryBiblePreview(data: StoryBibleDraftRequest) {
    return api.post<StoryBible>('/story-bible/draft', data)
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

  /** 取消正在进行的剧本生成 */
  cancelGeneration(projectId: number) {
    return api.post<{ message: string; status: string }>(`/projects/${projectId}/script/cancel-generation`)
  },

  /** 导出剧本 */
  async exportScript(projectId: number, format: 'docx' | 'txt' = 'docx') {
    const token = getToken()
    const baseURL = import.meta.env.VITE_API_BASE_URL || ''
    const url = `${baseURL}/projects/${projectId}/script/export?format=${format}`

    const res = await fetch(url, {
      headers: { 'Authorization': `Bearer ${token}` },
    })
    if (!res.ok) throw new Error('Export failed')
    const blob = await res.blob()
    const blobUrl = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = blobUrl
    link.download = format === 'txt' ? 'script.txt' : 'script.docx'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(blobUrl)
  },

  /**
   * AI 生成剧本（SSE 流式）
   * SSE events: delta → {content}, done → {script_id, episode_count, ...}, error → {message}
   */
  async generateStream(
    projectId: number,
    data: ScriptGenerateRequest,
    handlers: {
      onContent?: (chunk: string) => void
      onDone?: (result: ScriptGenerateStreamResult) => void
      onError?: (error: string) => void
    },
    signal?: AbortSignal,
  ): Promise<void> {
    const token = getToken()

    const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/projects/${projectId}/script/generate-stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: token ? `Bearer ${token}` : '',
        Accept: 'text/event-stream',
      },
      body: JSON.stringify(data),
      signal,
    })

    if (!response.ok) {
      let errorMsg = '生成失败'
      try {
        const errorData = await response.json()
        errorMsg = errorData?.detail || errorMsg
      } catch { /* ignore */ }
      throw new Error(errorMsg)
    }

    const reader = response.body?.getReader()
    if (!reader) throw new Error('Response body is not readable')

    const decoder = new TextDecoder()
    let buffer = ''

    try {
      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const messages = buffer.split('\n\n')
        buffer = messages.pop() ?? ''

        for (const message of messages) {
          let eventName = ''
          let dataStr = ''

          for (const line of message.split('\n')) {
            if (line.startsWith('event: ')) {
              eventName = line.slice(7).trim()
            } else if (line.startsWith('data: ')) {
              dataStr = line.slice(6).trim()
            }
          }

          if (!dataStr || dataStr === '[DONE]') continue

          try {
            const payload = JSON.parse(dataStr)

            switch (eventName) {
              case 'delta':
                handlers.onContent?.(payload.content ?? '')
                break
              case 'done':
                handlers.onDone?.(payload)
                break
              case 'error':
                handlers.onError?.(payload.message ?? '生成失败')
                break
            }
          } catch (e) {
            console.warn('[SSE] Failed to parse event:', eventName, dataStr)
          }
        }
      }
    } finally {
      reader.releaseLock()
    }
  },

  /**
   * 改写为旁白型（SSE 流式）
   * SSE events: delta → {content}, done → {content}, error → {message}
   */
  async rewriteNarrationStream(
    projectId: number,
    handlers: {
      onContent?: (chunk: string) => void
      onDone?: (content: string) => void
      onError?: (error: string) => void
    },
    signal?: AbortSignal,
  ): Promise<void> {
    const token = getToken()

    const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/projects/${projectId}/script/rewrite-narration-stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: token ? `Bearer ${token}` : '',
        Accept: 'text/event-stream',
      },
      signal,
    })

    if (!response.ok) {
      let errorMsg = '改写失败'
      try {
        const errorData = await response.json()
        errorMsg = errorData?.detail || errorMsg
      } catch { /* ignore */ }
      throw new Error(errorMsg)
    }

    const reader = response.body?.getReader()
    if (!reader) throw new Error('Response body is not readable')

    const decoder = new TextDecoder()
    let buffer = ''

    try {
      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const messages = buffer.split('\n\n')
        buffer = messages.pop() ?? ''

        for (const message of messages) {
          let eventName = ''
          let dataStr = ''

          for (const line of message.split('\n')) {
            if (line.startsWith('event: ')) {
              eventName = line.slice(7).trim()
            } else if (line.startsWith('data: ')) {
              dataStr = line.slice(6).trim()
            }
          }

          if (!dataStr || dataStr === '[DONE]') continue

          try {
            const payload = JSON.parse(dataStr)

            switch (eventName) {
              case 'delta':
                handlers.onContent?.(payload.content ?? '')
                break
              case 'done':
                handlers.onDone?.(payload.content ?? '')
                break
              case 'error':
                handlers.onError?.(payload.message ?? '改写失败')
                break
            }
          } catch (e) {
            console.warn('[SSE] Failed to parse event:', eventName, dataStr)
          }
        }
      }
    } finally {
      reader.releaseLock()
    }
  },
}
