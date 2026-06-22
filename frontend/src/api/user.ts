import request from './request'
import type {
  UserInfoRes, UpdateUserReq, UpdatePasswordReq,
} from './types'

export function getMe(): Promise<UserInfoRes> {
  return request.get('/users/me')
}

export function updateMe(data: UpdateUserReq): Promise<void> {
  return request.put('/users/me', data)
}

export function updatePassword(data: UpdatePasswordReq): Promise<void> {
  return request.put('/users/me/password', data)
}
