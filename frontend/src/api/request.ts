import axios from 'axios'
import type { AxiosInstance, AxiosResponse } from 'axios'
import { ElMessage } from 'element-plus'

const instance: AxiosInstance = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器 — 自动携带 token
instance.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = token
    }
    return config
  },
  (error) => Promise.reject(error),
)

// 响应拦截器 — 统一错误处理
instance.interceptors.response.use(
  (response: AxiosResponse) => {
    const res = response.data

    // 401 — 未登录，跳转登录页
    if (res.code === 401) {
      localStorage.removeItem('token')
      const currentPath = window.location.pathname
      if (currentPath !== '/login' && currentPath !== '/register') {
        window.location.href = '/login'
      }
      // 不显示 toast，直接 reject 让调用方感知
      return Promise.reject(new Error(res.message || '未登录'))
    }

    // 业务层非 200 — 统一 toast 提示，使用后端 message
    if (res.code !== 200) {
      ElMessage.error(res.message || '请求失败')
      return Promise.reject(new Error(res.message || '请求失败'))
    }

    return res
  },
  (error) => {
    // HTTP 层错误 — 网络断开 / 超时 / 5xx
    const status = error.response?.status
    const data = error.response?.data

    // 401 跳转登录
    if (status === 401 || data?.code === 401) {
      localStorage.removeItem('token')
      const currentPath = window.location.pathname
      if (currentPath !== '/login' && currentPath !== '/register') {
        window.location.href = '/login'
      }
      return Promise.reject(error)
    }

    // 超时
    if (error.code === 'ECONNABORTED' || status === 0) {
      ElMessage.error('请求超时，请稍后重试')
      return Promise.reject(error)
    }

    // 网络错误（无法连接）
    if (!status || error.message === 'Network Error') {
      ElMessage.error('服务暂时不可用，请检查后端是否启动')
      return Promise.reject(error)
    }

    // 其他 HTTP 错误 — 优先使用后端 message
    const msg = data?.message || error.message || '网络错误'
    ElMessage.error(msg)
    return Promise.reject(error)
  },
)

export default instance
