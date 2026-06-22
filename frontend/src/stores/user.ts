import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getCurrentUser } from '@/api/auth'

interface UserInfo {
  id: number
  username: string
  email: string
}

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('token') || '')
  const user = ref<UserInfo | null>(null)
  const isLoggedIn = computed(() => !!token.value && user.value !== null)

  /** 登录/注册成功后保存 token 和用户信息 */
  function setAuth(t: string, u: UserInfo) {
    token.value = t
    user.value = u
    localStorage.setItem('token', t)
  }

  /** 从后端获取当前用户信息 */
  async function fetchUser() {
    if (!token.value) return
    try {
      const res = await getCurrentUser()
      user.value = {
        id: res.data.id,
        username: res.data.username,
        email: res.data.email || '',
      }
    } catch {
      clearAuth()
    }
  }

  /** 退出登录 */
  function clearAuth() {
    token.value = ''
    user.value = null
    localStorage.removeItem('token')
  }

  return {
    token,
    user,
    isLoggedIn,
    setAuth,
    fetchUser,
    clearAuth,
  }
})
