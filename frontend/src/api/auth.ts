export interface UserInfo {
  id: number
  username: string
}

const TOKEN_KEY = 'nutrition_token'
const USER_KEY = 'nutrition_user'

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

export function getStoredUser(): UserInfo | null {
  try {
    const raw = localStorage.getItem(USER_KEY)
    return raw ? (JSON.parse(raw) as UserInfo) : null
  } catch {
    return null
  }
}

export function saveAuth(token: string, user: UserInfo) {
  localStorage.setItem(TOKEN_KEY, token)
  localStorage.setItem(USER_KEY, JSON.stringify(user))
}

export function clearAuth() {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(USER_KEY)
}

/** 带 token 的请求头 */
export function authHeaders(): Record<string, string> {
  const token = getToken()
  return token ? { Authorization: `Bearer ${token}` } : {}
}

async function requestAuth(path: string, username: string, password: string): Promise<UserInfo> {
  const res = await fetch(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  })
  const data = await res.json().catch(() => ({}))
  if (!res.ok) {
    throw new Error(data.detail || `请求失败（${res.status}）`)
  }
  saveAuth(data.token, data.user)
  return data.user
}

export async function login(username: string, password: string): Promise<UserInfo> {
  return requestAuth('/api/auth/login', username, password)
}

export async function register(username: string, password: string): Promise<UserInfo> {
  return requestAuth('/api/auth/register', username, password)
}

export async function changePassword(oldPassword: string, newPassword: string): Promise<void> {
  const res = await fetch('/api/auth/change-password', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify({ old_password: oldPassword, new_password: newPassword }),
  })
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new Error(data.detail || `修改失败（${res.status}）`)
  }
}
