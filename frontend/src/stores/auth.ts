import { reactive } from 'vue'
import {
  clearAuth,
  getToken,
  getStoredUser,
  login as apiLogin,
  register as apiRegister,
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

  async register(username: string, password: string) {
    this.user = await apiRegister(username, password)
    this.token = getToken()
  },

  logout() {
    clearAuth()
    this.token = null
    this.user = null
  },
})
