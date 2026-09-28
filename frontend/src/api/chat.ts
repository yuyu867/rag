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
    // 统一换行，便于按空行切分事件
    buffer = buffer.replace(/\r\n/g, '\n')

    // SSE 以「空行」分隔事件；一个事件内可能有多行 data:，按规范需用 \n 拼回。
    // 若像以前那样把每行 data: 当独立片段直接拼接，token 中的换行符会丢失，
    // 导致模型输出的 Markdown 表格被压成一行、无法渲染成卡片。
    let sep: number
    while ((sep = buffer.indexOf('\n\n')) !== -1) {
      const rawEvent = buffer.slice(0, sep)
      buffer = buffer.slice(sep + 2)

      const dataLines: string[] = []
      for (const line of rawEvent.split('\n')) {
        if (line.startsWith('data:')) {
          // 按 SSE 规范去掉 "data:" 后的一个可选空格
          dataLines.push(line.slice(5).replace(/^ /, ''))
        }
      }
      if (!dataLines.length) continue

      const data = dataLines.join('\n')
      if (data === '[DONE]') return
      yield data
    }
  }
}
