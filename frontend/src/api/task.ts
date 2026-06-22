import request from './request'
import type {
  CreateTaskReq, CreateTaskRes, TaskListRes,
  TaskDetailRes, TaskStatusRes, TaskTimelineRes,
  ReportDetailRes, TaskQueryParams,
  BatchDeleteTaskReq, BatchDeleteTaskRes,
} from './types'

export function createTask(data: CreateTaskReq): Promise<CreateTaskRes> {
  return request.post('/tasks', data)
}

export function getTaskList(params: TaskQueryParams): Promise<TaskListRes> {
  return request.get('/tasks', { params })
}

export function getTaskDetail(id: number): Promise<TaskDetailRes> {
  return request.get(`/tasks/${id}`)
}

export function getTaskStatus(id: number): Promise<TaskStatusRes> {
  return request.get(`/tasks/${id}/status`)
}

export function getTaskTimeline(id: number): Promise<TaskTimelineRes> {
  return request.get(`/tasks/${id}/timeline`)
}

export function getReport(taskId: number): Promise<ReportDetailRes> {
  return request.get(`/reports/${taskId}`)
}

export function retryTask(id: number): Promise<void> {
  return request.post(`/tasks/${id}/retry`)
}

export function cancelTask(id: number): Promise<void> {
  return request.post(`/tasks/${id}/cancel`)
}

export function deleteTask(id: number): Promise<void> {
  return request.delete(`/tasks/${id}`)
}

export function batchDeleteTasks(data: BatchDeleteTaskReq): Promise<BatchDeleteTaskRes> {
  return request.post('/tasks/batch-delete', data)
}
