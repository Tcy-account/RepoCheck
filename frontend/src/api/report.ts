import request from './request'
import axios from 'axios'
import type {
  ReportScoresRes, SystemHealthRes, AiHealthRes, SystemConfigRes,
  BatchExportMarkdownReq,
} from './types'

export function getReportScores(taskId: number): Promise<ReportScoresRes> {
  return request.get(`/reports/${taskId}/scores`)
}

export function regenerateReport(taskId: number): Promise<void> {
  return request.post(`/reports/${taskId}/regenerate`)
}

export function getSystemHealth(): Promise<SystemHealthRes> {
  return request.get('/system/health')
}

export function getAiHealth(): Promise<AiHealthRes> {
  return request.get('/system/ai-health')
}

export function getSystemConfig(): Promise<SystemConfigRes> {
  return request.get('/system/config')
}

/**
 * 导出 Markdown 报告并触发浏览器下载
 */
export async function exportMarkdownReport(taskId: number): Promise<void> {
  const response = await axios.get(`/api/reports/${taskId}/export/markdown`, {
    responseType: 'blob',
  })

  // 从 Content-Disposition 获取文件名
  let filename = `repocheck-report-${taskId}.md`
  const disposition = response.headers['content-disposition']
  if (disposition) {
    const match = disposition.match(/filename\*?=(?:UTF-8''|"|'?)([^";\r\n]+)/i)
    if (match && match[1]) {
      filename = decodeURIComponent(match[1])
    } else {
      const simpleMatch = disposition.match(/filename="?([^";\r\n]+)"?/i)
      if (simpleMatch && simpleMatch[1]) {
        filename = simpleMatch[1]
      }
    }
  }

  // 触发下载
  const url = window.URL.createObjectURL(new Blob([response.data]))
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  window.URL.revokeObjectURL(url)
}

/** 批量导出 Markdown 报告（ZIP 下载） */
export async function batchExportMarkdownReports(data: BatchExportMarkdownReq): Promise<void> {
  const response = await axios.post('/api/reports/export/markdown/batch', data, {
    responseType: 'blob',
  })

  const blob = new Blob([response.data], { type: 'application/zip' })
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = 'repocheck-reports.zip'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  window.URL.revokeObjectURL(url)
}
