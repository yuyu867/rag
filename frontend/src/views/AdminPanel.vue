<template>
  <div class="admin-panel">
    <div class="admin-header">
      <div class="title">⚙ 账号管理后台</div>
      <div class="actions">
        <el-button size="small" @click="load">刷新</el-button>
        <el-button size="small" type="primary" plain @click="emit('back')">返回聊天</el-button>
      </div>
    </div>

    <el-table :data="users" v-loading="loading" border stripe style="width: 100%">
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="username" label="用户名" min-width="120" />
      <el-table-column prop="phone" label="手机号" min-width="130">
        <template #default="{ row }">{{ row.phone || '—' }}</template>
      </el-table-column>
      <el-table-column prop="email" label="邮箱" min-width="150">
        <template #default="{ row }">{{ row.email || '—' }}</template>
      </el-table-column>
      <el-table-column label="角色" width="90">
        <template #default="{ row }">
          <el-tag v-if="row.is_admin" type="danger" size="small">管理员</el-tag>
          <el-tag v-else type="info" size="small">普通用户</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="conversation_count" label="会话数" width="80" />
      <el-table-column label="注册时间" min-width="160">
        <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="230" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" size="small" @click="resetPassword(row)">重置密码</el-button>
          <el-button link type="primary" size="small" @click="editPhone(row)">改手机号</el-button>
          <el-button
            link
            :type="row.is_admin ? 'warning' : 'success'"
            size="small"
            @click="toggleAdmin(row)"
          >{{ row.is_admin ? '取消管理员' : '设为管理员' }}</el-button>
          <el-button
            v-if="row.id !== authStore.user?.id"
            link
            type="danger"
            size="small"
            @click="removeUser(row)"
          >删除</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { listUsers, updateUser, deleteUser, type AdminUser } from '../api/admin'
import { authStore } from '../stores/auth'

const emit = defineEmits<{ (e: 'back'): void }>()

const users = ref<AdminUser[]>([])
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    users.value = await listUsers()
  } catch (e) {
    ElMessage.error(e instanceof Error ? e.message : '加载失败')
  } finally {
    loading.value = false
  }
}

async function resetPassword(row: AdminUser) {
  let value: string
  try {
    const { value: v } = await ElMessageBox.prompt(
      `为「${row.username}」设置新密码（至少 6 位）`,
      '重置密码',
      { inputType: 'password', inputPattern: /^.{6,}$/, inputErrorMessage: '密码至少 6 位' },
    )
    value = v
  } catch {
    return
  }
  try {
    await updateUser(row.id, { password: value })
    ElMessage.success('密码已重置')
  } catch (e) {
    ElMessage.error(e instanceof Error ? e.message : '操作失败')
  }
}

async function editPhone(row: AdminUser) {
  let value: string
  try {
    const { value: v } = await ElMessageBox.prompt(
      `修改「${row.username}」的手机号`,
      '修改手机号',
      { inputValue: row.phone || '', inputPattern: /^1[3-9]\d{9}$/, inputErrorMessage: '请输入正确的 11 位手机号' },
    )
    value = v
  } catch {
    return
  }
  try {
    await updateUser(row.id, { phone: value })
    ElMessage.success('手机号已更新')
    load()
  } catch (e) {
    ElMessage.error(e instanceof Error ? e.message : '操作失败')
  }
}

async function toggleAdmin(row: AdminUser) {
  const action = row.is_admin ? '取消' : '设为'
  try {
    await ElMessageBox.confirm(
      `确定要${action}「${row.username}」的管理员权限吗？`,
      `${action}管理员`,
      { type: 'warning' },
    )
  } catch {
    return
  }
  try {
    await updateUser(row.id, { is_admin: !row.is_admin })
    ElMessage.success(`${action}管理员成功`)
    load()
  } catch (e) {
    ElMessage.error(e instanceof Error ? e.message : '操作失败')
  }
}

async function removeUser(row: AdminUser) {
  try {
    await ElMessageBox.confirm(
      `删除用户「${row.username}」会同时删除其所有会话与聊天记录，且不可恢复。确定删除？`,
      '删除用户',
      { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' },
    )
  } catch {
    return
  }
  try {
    await deleteUser(row.id)
    ElMessage.success('已删除')
    load()
  } catch (e) {
    ElMessage.error(e instanceof Error ? e.message : '删除失败')
  }
}

function formatTime(iso: string): string {
  const d = new Date(iso)
  return isNaN(d.getTime()) ? iso : d.toLocaleString('zh-CN')
}

onMounted(load)
</script>

<style scoped>
.admin-panel {
  flex: 1;
  min-width: 0;
  padding: 20px;
  overflow: auto;
  background: #fff;
}
.admin-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}
.title {
  font-size: 18px;
  font-weight: bold;
}
</style>
