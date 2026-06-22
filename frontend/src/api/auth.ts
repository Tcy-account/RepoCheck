import request from './request'
import type {
  LoginReq, LoginResWrapped, RegisterReq,
  CurrentUserRes,
} from './types'

export function register(data: RegisterReq): Promise<LoginResWrapped> {
  return request.post('/auth/register', data)
}

export function login(data: LoginReq): Promise<LoginResWrapped> {
  return request.post('/auth/login', data)
}

export function logout(): Promise<void> {
  return request.post('/auth/logout')
}

export function getCurrentUser(): Promise<CurrentUserRes> {
  return request.get('/auth/me')
}
