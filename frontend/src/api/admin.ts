import { authHeaders } from './auth'

export interface AdminUser {
  id: number
  username: string
  phone: string | null
  email: string | null
  is_admin: boolean
  created_at: string
  conversation_count: number
}

export interface AdminUpdateBody {
  password?: string
  phone?: string
  email?: string | null
  is_admin?: boolean
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(path, {
    ...options,
    headers: { 'Content-Type': 'application/json', ...authHeaders(), ...(options.headers || {}) },
  })
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new Error(data.detail || `请求失败（${res.status}）`)
  }
  return res.json()
}

export function listUsers(): Promise<AdminUser[]> {
  return request<AdminUser[]>('/api/admin/users')
}

export function updateUser(id: number, body: AdminUpdateBody): Promise<AdminUser> {
  return request<AdminUser>(`/api/admin/users/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(body),
  })
}

export function deleteUser(id: number): Promise<void> {
  return request(`/api/admin/users/${id}`, { method: 'DELETE' })
}
