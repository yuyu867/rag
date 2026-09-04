<template>
  <div class="chat-window">
    <div class="header">AI 智能营养师 - 小营</div>
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
      <el-button type="primary" @click="handleSend" :disabled="loading || !input.trim()">
        发送
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick } from 'vue'
import ChatMessage from './ChatMessage.vue'
import ImageUpload from './ImageUpload.vue'
import { sendMessage, type ChatMessage as Msg } from '../api/chat'

const messages = ref<(Msg & { imageUrl?: string })[]>([])
const input = ref('')
const loading = ref(false)
const imageBase64 = ref<string>()
const msgContainer = ref<HTMLElement>()

function onImage(b64: string) {
  imageBase64.value = b64
}

async function handleSend() {
  const text = input.value.trim()
  if (!text || loading.value) return

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
    for await (const chunk of sendMessage(text, imageBase64.value)) {
      fullText += chunk
      assistantMsg.content = fullText
      await nextTick()
      scrollToBottom()
    }
  } catch (e) {
    assistantMsg.content = '抱歉，服务暂时不可用，请稍后重试。'
  }

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
  max-width: 800px; margin: 0 auto; height: 100vh; display: flex; flex-direction: column;
}
.header { padding: 16px; text-align: center; font-size: 18px; font-weight: bold;
  background: #67c23a; color: #fff; }
.messages { flex: 1; overflow-y: auto; padding: 20px; }
.input-area { display: flex; gap: 8px; padding: 12px 20px; border-top: 1px solid #eee;
  background: #fff; align-items: center; }
.typing { color: #999; font-size: 13px; padding: 8px 0; }
</style>
