import request from './request'
import type {
  FileUploadRes, FileDownloadRes,
} from './types'

export function uploadFile(file: File, type?: string): Promise<FileUploadRes> {
  const formData = new FormData()
  formData.append('file', file)
  if (type) formData.append('type', type)
  return request.post('/files/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export function getDownloadUrl(fileId: string): Promise<FileDownloadRes> {
  return request.get(`/files/${fileId}/download-url`)
}

export function deleteFile(fileId: string): Promise<void> {
  return request.delete(`/files/${fileId}`)
}
