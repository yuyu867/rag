<template>
  <div id="app">
    <LoginView v-if="!authStore.isLoggedIn" />
    <div v-else class="layout">
      <ConversationSidebar />
      <ChatWindow />
    </div>
  </div>
</template>

<script setup lang="ts">
import { watch } from 'vue'
import LoginView from './views/LoginView.vue'
import ConversationSidebar from './components/ConversationSidebar.vue'
import ChatWindow from './components/ChatWindow.vue'
import { authStore } from './stores/auth'
import { conversationStore } from './stores/conversations'

// 登录态就绪后拉取会话列表
watch(
  () => authStore.isLoggedIn,
  (ok) => {
    if (ok) conversationStore.refresh()
  },
  { immediate: true },
)
</script>

<style>
body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}
#app {
  background: #f0f2f5;
  height: 100vh;
}
.layout {
  display: flex;
  height: 100vh;
  overflow: hidden;
}
</style>
