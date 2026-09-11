<template>
  <div id="app">
    <LoginView v-if="!authStore.isLoggedIn" />
    <div v-else class="layout">
      <ConversationSidebar @open-admin="showAdmin = true" />
      <AdminPanel v-if="showAdmin" @back="showAdmin = false" />
      <ChatWindow v-else />
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import LoginView from './views/LoginView.vue'
import AdminPanel from './views/AdminPanel.vue'
import ConversationSidebar from './components/ConversationSidebar.vue'
import ChatWindow from './components/ChatWindow.vue'
import { authStore } from './stores/auth'
import { conversationStore } from './stores/conversations'

const showAdmin = ref(false)

// 登录态就绪后拉取会话列表
watch(
  () => authStore.isLoggedIn,
  (ok) => {
    if (ok) conversationStore.refresh()
    else showAdmin.value = false
  },
  { immediate: true },
)

// 刷新用户信息（补齐 is_admin 等字段；登录过期时 fetchMe 内部会清除凭证）
onMounted(() => {
  if (authStore.isLoggedIn) authStore.refresh()
})
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
