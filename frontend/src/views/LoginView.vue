<template>
  <div class="login-page">
    <el-card class="login-card" shadow="always">
      <div class="brand">
        <div class="logo">🥗</div>
        <h1>AI 智能营养师 · 小营</h1>
        <p>登录后开始你的个性化健康饮食之旅</p>
      </div>

      <el-tabs v-model="activeTab" stretch>
        <el-tab-pane label="登录" name="login">
          <el-form
            ref="loginFormRef"
            :model="loginForm"
            :rules="loginRules"
            label-position="top"
            @submit.prevent
          >
            <el-form-item label="用户名" prop="username">
              <el-input v-model="loginForm.username" placeholder="请输入用户名" size="large" />
            </el-form-item>
            <el-form-item label="密码" prop="password">
              <el-input
                v-model="loginForm.password"
                type="password"
                placeholder="请输入密码"
                size="large"
                show-password
                @keyup.enter="submitLogin"
              />
            </el-form-item>
            <el-button
              type="primary"
              size="large"
              class="submit-btn"
              :loading="loading"
              @click="submitLogin"
            >登 录</el-button>
          </el-form>
        </el-tab-pane>

        <el-tab-pane label="注册" name="register">
          <el-form
            ref="registerFormRef"
            :model="registerForm"
            :rules="registerRules"
            label-position="top"
            @submit.prevent
          >
            <el-form-item label="用户名" prop="username">
              <el-input v-model="registerForm.username" placeholder="2-50 个字符" size="large" />
            </el-form-item>
            <el-form-item label="手机号" prop="phone">
              <el-input v-model="registerForm.phone" placeholder="11 位手机号，用于账号找回" size="large" maxlength="11" />
            </el-form-item>
            <el-form-item label="邮箱（可选）" prop="email">
              <el-input v-model="registerForm.email" placeholder="选填" size="large" />
            </el-form-item>
            <el-form-item label="密码" prop="password">
              <el-input
                v-model="registerForm.password"
                type="password"
                placeholder="至少 6 位"
                size="large"
                show-password
              />
            </el-form-item>
            <el-form-item label="确认密码" prop="confirm">
              <el-input
                v-model="registerForm.confirm"
                type="password"
                placeholder="再输入一次密码"
                size="large"
                show-password
                @keyup.enter="submitRegister"
              />
            </el-form-item>
            <el-button
              type="primary"
              size="large"
              class="submit-btn"
              :loading="loading"
              @click="submitRegister"
            >注 册</el-button>
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { authStore } from '../stores/auth'
import { conversationStore } from '../stores/conversations'

const activeTab = ref<'login' | 'register'>('login')
const loading = ref(false)

const loginFormRef = ref<FormInstance>()
const loginForm = reactive({ username: '', password: '' })
const loginRules: FormRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

const registerFormRef = ref<FormInstance>()
const registerForm = reactive({ username: '', phone: '', email: '', password: '', confirm: '' })
const registerRules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 2, max: 50, message: '用户名需 2-50 个字符', trigger: 'blur' },
  ],
  phone: [
    { required: true, message: '请输入手机号', trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的 11 位手机号', trigger: 'blur' },
  ],
  email: [
    {
      pattern: /^[\w.+-]+@[\w-]+\.[\w.-]+$/,
      message: '邮箱格式不正确',
      trigger: 'blur',
    },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少 6 位', trigger: 'blur' },
  ],
  confirm: [
    { required: true, message: '请再次输入密码', trigger: 'blur' },
    {
      validator: (_rule, value, callback) => {
        if (value !== registerForm.password) callback(new Error('两次输入的密码不一致'))
        else callback()
      },
      trigger: 'blur',
    },
  ],
}

async function submitLogin() {
  const ok = await loginFormRef.value?.validate().catch(() => false)
  if (!ok) return
  loading.value = true
  try {
    await authStore.login(loginForm.username.trim(), loginForm.password)
    ElMessage.success(`欢迎回来，${authStore.user?.username}！`)
    conversationStore.refresh()
  } catch (e) {
    ElMessage.error(e instanceof Error ? e.message : '登录失败')
  } finally {
    loading.value = false
  }
}

async function submitRegister() {
  const ok = await registerFormRef.value?.validate().catch(() => false)
  if (!ok) return
  loading.value = true
  try {
    await authStore.register(
      registerForm.username.trim(),
      registerForm.password,
      registerForm.phone.trim(),
      registerForm.email.trim() || undefined,
    )
    ElMessage.success('注册成功，已自动登录！')
    conversationStore.refresh()
  } catch (e) {
    ElMessage.error(e instanceof Error ? e.message : '注册失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #e8f7e5 0%, #f0f2f5 60%);
}
.login-card {
  width: 400px;
  border-radius: 12px;
}
.brand {
  text-align: center;
  margin-bottom: 12px;
}
.logo {
  font-size: 44px;
}
.brand h1 {
  font-size: 20px;
  margin: 6px 0 4px;
  color: #303133;
}
.brand p {
  font-size: 13px;
  color: #909399;
  margin: 0 0 8px;
}
.submit-btn {
  width: 100%;
  margin-top: 4px;
}
</style>
