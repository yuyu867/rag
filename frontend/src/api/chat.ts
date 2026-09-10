import { authHeaders, clearAuth } from './auth'

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  imageUrl?: string
}

export async function uploadImage(file: File): Promise<string> {
  const formData = new FormData()
  formData.append('file', file)
  const res = await fetch('/api/chat/upload', {
    method: 'POST',
    headers: { ...authHeaders() },
    body: formData,
  })
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new Error(data.detail || `上传失败（${res.status}）`)
  }
  const data = await res.json()
  return data.image_base64
}

export async function* sendMessage(
  text: string,
  imageBase64: string | undefined,
  conversationId: number,
): AsyncGenerator<string> {
  const res = await fetch('/api/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...authHeaders(),
    },
    body: JSON.stringify({
      text,
      image_base64: imageBase64 || null,
      conversation_id: conversationId,
    }),
  })

  // 登录过期：清除本地凭证并回到登录页
  if (res.status === 401) {
    clearAuth()
    location.reload()
    return
  }
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    yield data.detail || `请求失败（${res.status}）`
    return
  }

  const reader = res.body?.getReader()
  if (!reader) return

  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() || ''
    for (const line of lines) {
      // 去掉 SSE 的 \r\n 里的 \r
      const clean = line.endsWith('\r') ? line.slice(0, -1) : line
      if (clean.startsWith('data: ')) {
        const data = clean.slice(6)
        if (data === '[DONE]') return
        yield data
      }
    }
  }
}
