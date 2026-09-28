<template>
  <div class="chat-window">
    <div class="header">
      <button class="menu-btn" title="会话列表" @click="uiStore.toggleSidebar()">
        <span class="menu-icon">☰</span>
      </button>
      <span class="header-title">AI 智能营养师 - 小营</span>
      <el-button size="small" class="new-btn" @click="newConversation">新对话</el-button>
    </div>
    <div class="messages" ref="msgContainer">
      <ChatMessage v-for="(msg, i) in messages" :key="i" v-bind="msg" />
      <div v-if="loading" class="typing">小营正在思考...</div>
    </div>
    <div class="input-area">
      <ImageUpload @image="onImage" @clear="imageBase64 = undefined" />
      <el-input
        v-model="input"
        placeholder="输入你的问题，例如：身高175体重80kg，高血糖前期能吃香蕉吗？"
        @keyup.enter="handleSend"
        :disabled="loading"
      />
      <el-button
        v-if="speechSupported"
        class="voice-btn"
        :class="{ listening: recognizing }"
        :title="recognizing ? '停止语音' : '语音输入'"
        @click="toggleVoice"
      >🎤</el-button>
      <el-button type="primary" @click="handleSend" :disabled="loading || !input.trim()">
        发送
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, watch } from 'vue'
import { ElMessage } from 'element-plus'
import ChatMessage from './ChatMessage.vue'
import ImageUpload from './ImageUpload.vue'
import { sendMessage, type ChatMessage as Msg } from '../api/chat'
import { getMessages } from '../api/conversations'
import { conversationStore } from '../stores/conversations'
import { uiStore } from '../stores/ui'

const messages = ref<(Msg & { imageUrl?: string })[]>([])
const input = ref('')
const loading = ref(false)
const imageBase64 = ref<string>()
const msgContainer = ref<HTMLElement>()

// 切换会话时从 PostgreSQL 加载历史消息
watch(
  () => conversationStore.currentId,
  async (id) => {
    if (!id) {
      messages.value = []
      return
    }
    try {
      const history = await getMessages(id)
      messages.value = history.map((m) => ({ role: m.role, content: m.content }))
    } catch {
      messages.value = []
    }
    await nextTick()
    scrollToBottom()
  },
  { immediate: true },
)

// ---- 语音输入（Web Speech API） ----
const recognizing = ref(false)
let recognition: any = null

const speechSupported = !!(
  (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
)

function toggleVoice() {
  const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
  if (!SR) {
    ElMessage.warning('当前浏览器不支持语音输入（请使用 Chrome/Edge 且需 HTTPS 或 localhost）')
    return
  }
  if (recognizing.value) {
    recognition?.stop()
    return
  }
  const rec = new SR()
  rec.lang = 'zh-CN'
  rec.interimResults = true
  rec.continuous = false
  rec.onresult = (e: any) => {
    let transcript = ''
    for (let i = 0; i < e.results.length; i++) transcript += e.results[i][0].transcript
    input.value = transcript
  }
  rec.onend = () => {
    recognizing.value = false
  }
  rec.onerror = () => {
    recognizing.value = false
    ElMessage.warning('语音识别出错或未授权麦克风')
  }
  recognition = rec
  recognizing.value = true
  rec.start()
}

function onImage(b64: string) {
  imageBase64.value = b64
}

function newConversation() {
  // 创建新会话；currentId 变化会触发上面的 watch 清空并加载消息
  conversationStore.create()
}

async function handleSend() {
  const text = input.value.trim()
  if (!text || loading.value) return

  // 没有会话时先创建一个（新建页面直接发消息的场景）
  if (!conversationStore.currentId) {
    const conv = await conversationStore.create()
    if (!conv) return
  }
  const conversationId = conversationStore.currentId!

  const userMsg: Msg & { imageUrl?: string } = { role: 'user', content: text }
  if (imageBase64.value) {
    userMsg.imageUrl = `data:image/jpeg;base64,${imageBase64.value}`
  }
  messages.value.push(userMsg)
  input.value = ''
  loading.value = true

  await nextTick()
  scrollToBottom()

  const assistantMsg: Msg & { imageUrl?: string } = { role: 'assistant', content: '' }
  messages.value.push(assistantMsg)

  try {
    let fullText = ''
    for await (const chunk of sendMessage(text, imageBase64.value, conversationId)) {
      fullText += chunk
      assistantMsg.content = fullText
      await nextTick()
      scrollToBottom()
    }
  } catch (e) {
    assistantMsg.content =
      e instanceof Error && e.message ? e.message : '抱歉，服务暂时不可用，请稍后重试。'
  }

  // 后端已把本轮问答落库；刷新左侧列表（标题 / 排序）
  conversationStore.refresh()

  imageBase64.value = undefined
  loading.value = false
}

function scrollToBottom() {
  if (msgContainer.value) {
    msgContainer.value.scrollTop = msgContainer.value.scrollHeight
  }
}
</script>

<style scoped>
.chat-window {
  flex: 1;
  max-width: 900px;
  margin: 0 auto;
  height: 100vh;
  display: flex;
  flex-direction: column;
  min-width: 0;
}
.header {
  padding: 12px 16px;
  font-size: 18px;
  font-weight: bold;
  background: #67c23a;
  color: #fff;
  display: flex;
  align-items: center;
  gap: 10px;
}
.header-title {
  flex: 1;
  text-align: center;
  font-size: 16px;
}
.menu-btn {
  display: none;
  background: none;
  border: none;
  color: #fff;
  font-size: 18px;
  cursor: pointer;
  padding: 4px 6px;
  border-radius: 6px;
}
.menu-btn:hover {
  background: rgba(255, 255, 255, 0.2);
}
.new-btn {
  margin-left: auto;
}
.messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}
.input-area {
  display: flex;
  gap: 8px;
  padding: 12px 16px;
  border-top: 1px solid #eee;
  background: #fff;
  align-items: center;
}
.voice-btn {
  flex-shrink: 0;
}
.voice-btn.listening {
  color: #fff;
  background: #f56c6c;
  border-color: #f56c6c;
  animation: pulse 1s infinite;
}
@keyframes pulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(245, 108, 108, 0.5); }
  50% { box-shadow: 0 0 0 6px rgba(245, 108, 108, 0); }
}
.typing {
  color: #999;
  font-size: 13px;
  padding: 8px 0;
}

/* 移动端 */
@media (max-width: 768px) {
  .menu-btn {
    display: inline-flex;
  }
  .header-title {
    font-size: 15px;
  }
  .messages {
    padding: 12px;
  }
  .input-area {
    padding: 10px 8px;
  }
}
</style>
