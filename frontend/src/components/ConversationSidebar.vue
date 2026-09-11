<template>
  <aside class="sidebar">
    <div class="sidebar-header">
      <div class="app-name">🥗 AI 营养师 · 小营</div>
      <div class="user-row">
        <span class="username" :title="authStore.user?.username">
          👤 {{ authStore.user?.username }}
        </span>
        <span class="user-actions">
          <button class="link-btn" @click="pwdDialogVisible = true">改密</button>
          <button class="link-btn" @click="logout">退出</button>
        </span>
      </div>
    </div>

    <div class="new-chat">
      <el-button type="primary" class="new-btn" :loading="creating" @click="createConversation">
        ＋ 新对话
      </el-button>
      <el-button
        v-if="authStore.user?.is_admin"
        class="new-btn admin-btn"
        @click="emit('open-admin')"
      >⚙ 管理后台</el-button>
    </div>

    <el-scrollbar class="conv-scroll">
      <div
        v-for="conv in conversationStore.list"
        :key="conv.id"
        class="conv-item"
        :class="{ active: conv.id === conversationStore.currentId }"
        @click="conversationStore.select(conv.id)"
      >
        <div class="conv-title">{{ conv.title }}</div>
        <div class="conv-meta">
          <span>{{ formatTime(conv.updated_at) }}</span>
          <span class="del-btn" title="删除会话" @click.stop="removeConversation(conv.id)">🗑</span>
        </div>
      </div>
      <div v-if="!conversationStore.list.length" class="empty-tip">暂无历史会话</div>
    </el-scrollbar>

    <!-- 修改密码对话框 -->
    <el-dialog v-model="pwdDialogVisible" title="修改密码" width="360px">
      <el-form ref="pwdFormRef" :model="pwdForm" :rules="pwdRules" label-position="top">
        <el-form-item label="原密码" prop="old_password">
          <el-input v-model="pwdForm.old_password" type="password" show-password />
        </el-form-item>
        <el-form-item label="新密码（至少 6 位）" prop="new_password">
          <el-input v-model="pwdForm.new_password" type="password" show-password />
        </el-form-item>
        <el-form-item label="确认新密码" prop="confirm">
          <el-input v-model="pwdForm.confirm" type="password" show-password @keyup.enter="submitChangePassword" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="pwdDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="changingPwd" @click="submitChangePassword">确定</el-button>
      </template>
    </el-dialog>
  </aside>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { authStore } from '../stores/auth'
import { conversationStore } from '../stores/conversations'
import { changePassword } from '../api/auth'

const emit = defineEmits<{ (e: 'open-admin'): void }>()

const creating = ref(false)

// ---- 修改密码 ----
const pwdDialogVisible = ref(false)
const changingPwd = ref(false)
const pwdFormRef = ref<FormInstance>()
const pwdForm = reactive({ old_password: '', new_password: '', confirm: '' })
const pwdRules: FormRules = {
  old_password: [{ required: true, message: '请输入原密码', trigger: 'blur' }],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '新密码至少 6 位', trigger: 'blur' },
    {
      validator: (_rule, value, callback) => {
        if (value === pwdForm.old_password) callback(new Error('新密码不能与原密码相同'))
        else callback()
      },
      trigger: 'blur',
    },
  ],
  confirm: [
    { required: true, message: '请再次输入新密码', trigger: 'blur' },
    {
      validator: (_rule, value, callback) => {
        if (value !== pwdForm.new_password) callback(new Error('两次输入的密码不一致'))
        else callback()
      },
      trigger: 'blur',
    },
  ],
}

async function submitChangePassword() {
  const ok = await pwdFormRef.value?.validate().catch(() => false)
  if (!ok) return
  changingPwd.value = true
  try {
    await changePassword(pwdForm.old_password, pwdForm.new_password)
    ElMessage.success('密码修改成功，下次登录请使用新密码')
    pwdDialogVisible.value = false
    pwdFormRef.value?.resetFields()
  } catch (e) {
    ElMessage.error(e instanceof Error ? e.message : '修改失败')
  } finally {
    changingPwd.value = false
  }
}

async function createConversation() {
  creating.value = true
  const conv = await conversationStore.create()
  creating.value = false
  if (!conv) ElMessage.error('创建会话失败')
}

async function removeConversation(id: number) {
  try {
    await ElMessageBox.confirm('删除后该会话的聊天记录将无法恢复，确定删除？', '删除会话', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消',
    })
  } catch {
    return // 用户取消
  }
  await conversationStore.remove(id)
}

function logout() {
  authStore.logout()
  conversationStore.reset()
}

function formatTime(iso: string): string {
  const d = new Date(iso)
  if (isNaN(d.getTime())) return ''
  const now = new Date()
  const sameDay = d.toDateString() === now.toDateString()
  if (sameDay) {
    return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
  }
  return `${d.getMonth() + 1}-${String(d.getDate()).padStart(2, '0')}`
}
</script>

<style scoped>
.sidebar {
  width: 260px;
  height: 100vh;
  background: #1f2d21;
  color: #e5ece6;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}
.sidebar-header {
  padding: 16px 16px 10px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}
.app-name {
  font-size: 15px;
  font-weight: bold;
  margin-bottom: 10px;
}
.user-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}
.username {
  font-size: 13px;
  color: #a8c2ab;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.user-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}
.link-btn {
  background: none;
  border: none;
  color: #8fae93;
  font-size: 12px;
  cursor: pointer;
  padding: 0;
  flex-shrink: 0;
}
.link-btn:hover {
  color: #fff;
  text-decoration: underline;
}
.new-chat {
  padding: 12px;
}
.new-btn {
  width: 100%;
}
.admin-btn {
  margin-left: 0;
  margin-top: 8px;
}
.conv-scroll {
  flex: 1;
}
.conv-item {
  padding: 10px 14px;
  cursor: pointer;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  transition: background 0.15s;
}
.conv-item:hover {
  background: rgba(255, 255, 255, 0.06);
}
.conv-item.active {
  background: #2d4a31;
}
.conv-title {
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.conv-meta {
  display: flex;
  justify-content: space-between;
  margin-top: 4px;
  font-size: 11px;
  color: #7d9481;
}
.del-btn {
  cursor: pointer;
  opacity: 0;
  transition: opacity 0.15s;
}
.conv-item:hover .del-btn {
  opacity: 1;
}
.del-btn:hover {
  color: #f56c6c;
}
.empty-tip {
  text-align: center;
  color: #6b7f6e;
  font-size: 12px;
  padding: 24px 0;
}
</style>
