import { reactive } from 'vue'
import {
  clearAuth,
  getToken,
  getStoredUser,
  login as apiLogin,
  register as apiRegister,
  fetchMe as apiFetchMe,
  type UserInfo,
} from '../api/auth'

export const authStore = reactive({
  token: getToken() as string | null,
  user: getStoredUser() as UserInfo | null,

  get isLoggedIn(): boolean {
    return !!this.token
  },

  async login(username: string, password: string) {
    this.user = await apiLogin(username, password)
    this.token = getToken()
  },

  async register(username: string, password: string, phone: string, email?: string) {
    this.user = await apiRegister(username, password, phone, email)
    this.token = getToken()
  },

  async refresh() {
    if (!this.token) return
    try {
      this.user = await apiFetchMe()
      this.token = getToken()
    } catch {
      // 401 时 clearAuth 已由 fetchMe 内部处理
    }
  },

  logout() {
    clearAuth()
    this.token = null
    this.user = null
  },
})
