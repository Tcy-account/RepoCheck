import request from './request'
import type {
  RepoAnalysisRes, ReadmeRes,
} from './types'

export function getAnalysis(taskId: number): Promise<RepoAnalysisRes> {
  return request.get(`/tasks/${taskId}/analysis`)
}

export function rebuildAnalysis(taskId: number): Promise<void> {
  return request.post(`/tasks/${taskId}/analysis/rebuild`)
}

export function getFileList(taskId: number): Promise<{ data: { files: string[] } }> {
  return request.get(`/tasks/${taskId}/analysis/files`)
}

export function getReadme(taskId: number): Promise<ReadmeRes> {
  return request.get(`/tasks/${taskId}/analysis/readme`)
}
