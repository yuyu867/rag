import { authHeaders } from './auth'

export interface Conversation {
  id: number
  thread_id: string
  title: string
  updated_at: string
}

export interface HistoryMessage {
  id: number
  role: 'user' | 'assistant'
  content: string
  created_at: string
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

export async function listConversations(): Promise<Conversation[]> {
  return request<Conversation[]>('/api/conversations')
}

export async function createConversation(title?: string): Promise<Conversation> {
  return request<Conversation>('/api/conversations', {
    method: 'POST',
    body: JSON.stringify({ title: title || null }),
  })
}

export async function deleteConversation(id: number): Promise<void> {
  await request(`/api/conversations/${id}`, { method: 'DELETE' })
}

export async function getMessages(conversationId: number): Promise<HistoryMessage[]> {
  return request<HistoryMessage[]>(`/api/conversations/${conversationId}/messages`)
}
