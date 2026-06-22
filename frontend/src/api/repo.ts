import request from './request'
import type {
  RepoInfoRes, RepoCandidateRes, UpdateRepoReq,
} from './types'

export function getRepo(taskId: number): Promise<RepoInfoRes> {
  return request.get(`/tasks/${taskId}/repo`)
}

export function getRepoCandidates(taskId: number): Promise<RepoCandidateRes> {
  return request.get(`/tasks/${taskId}/repo/candidates`)
}

export function updateRepo(taskId: number, data: UpdateRepoReq): Promise<void> {
  return request.put(`/tasks/${taskId}/repo`, data)
}

export function searchRepo(taskId: number): Promise<void> {
  return request.post(`/tasks/${taskId}/repo/search`)
}
