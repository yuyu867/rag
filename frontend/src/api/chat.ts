export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  imageUrl?: string
}

export async function uploadImage(file: File): Promise<string> {
  const formData = new FormData()
  formData.append('file', file)
  const res = await fetch('/api/chat/upload', { method: 'POST', body: formData })
  const data = await res.json()
  return data.image_base64
}

export async function* sendMessage(text: string, imageBase64?: string): AsyncGenerator<string> {
  const res = await fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, image_base64: imageBase64 || null }),
  })

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
      if (line.startsWith('data: ')) {
        const data = line.slice(6)
        if (data === '[DONE]') return
        yield data
      }
    }
  }
}
