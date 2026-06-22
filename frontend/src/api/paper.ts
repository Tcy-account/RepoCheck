import request from './request'
import type {
  PaperInfo,
} from './types'
import type { ApiResponse } from './types'

export function getPaper(taskId: number): Promise<ApiResponse<PaperInfo>> {
  return request.get(`/tasks/${taskId}/paper`)
}

export function refreshPaper(taskId: number): Promise<void> {
  return request.post(`/tasks/${taskId}/paper/refresh`)
}
