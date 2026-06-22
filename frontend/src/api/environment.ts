import request from './request'
import type { EnvironmentAnalysisRes, DependencyListRes, EnvironmentReportRes } from './types'

/** 查询环境分析汇总 */
export function getEnvironmentAnalysis(taskId: number): Promise<EnvironmentAnalysisRes> {
  return request.get(`/tasks/${taskId}/environment`)
}

/** 查询依赖列表 */
export function getDependencies(taskId: number): Promise<DependencyListRes> {
  return request.get(`/tasks/${taskId}/environment/dependencies`)
}

/** 重新执行环境分析 */
export function rebuildEnvironmentAnalysis(taskId: number): Promise<EnvironmentReportRes> {
  return request.post(`/tasks/${taskId}/environment/rebuild`)
}
