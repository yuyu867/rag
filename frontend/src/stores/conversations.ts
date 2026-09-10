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
