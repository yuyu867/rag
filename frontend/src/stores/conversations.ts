import { reactive } from 'vue'
import * as api from '../api/conversations'

export const conversationStore = reactive({
  list: [] as api.Conversation[],
  currentId: null as number | null,
  loading: false,

  get current(): api.Conversation | null {
    return this.list.find((c) => c.id === this.currentId) ?? null
  },

  async refresh() {
    try {
      this.list = await api.listConversations()
      // 当前会话被清空（例如在其他设备删除）时回退到第一个
      if (this.currentId && !this.current) {
        this.currentId = this.list[0]?.id ?? null
      }
    } catch {
      this.list = []
    }
  },

  async create(title?: string): Promise<api.Conversation | null> {
    try {
      const conv = await api.createConversation(title)
      this.list.unshift(conv)
      this.currentId = conv.id
      return conv
    } catch {
      return null
    }
  },

  select(id: number) {
    this.currentId = id
  },

  async rename(id: number, title: string) {
    const conv = await api.updateConversation(id, { title })
    const target = this.list.find((c) => c.id === id)
    if (target) target.title = conv.title
    return conv
  },

  async togglePin(id: number) {
    const target = this.list.find((c) => c.id === id)
    if (!target) return
    const conv = await api.updateConversation(id, { pinned: !target.pinned })
    await this.refresh()
    return conv
  },

  async remove(id: number) {
    try {
      await api.deleteConversation(id)
    } finally {
      await this.refresh()
    }
  },

  reset() {
    this.list = []
    this.currentId = null
  },
})
