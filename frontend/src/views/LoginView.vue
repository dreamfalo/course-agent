<template>
  <div class="login-page">
    <div class="login-card">
      <!-- Logo -->
      <div class="login-logo">
        <div class="logo-icon">
          <el-icon :size="40" color="#2981fd"><Notebook /></el-icon>
        </div>
        <h1>智能课程助手</h1>
        <p class="text-caption">基于 DeepSeek AI 的智能学习伴侣</p>
      </div>

      <!-- 表单 -->
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        class="login-form"
        @keyup.enter="handleLogin"
      >
        <el-form-item prop="username">
          <el-input
            v-model="form.username"
            placeholder="用户名"
            :prefix-icon="User"
            size="large"
          />
        </el-form-item>

        <el-form-item prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="密码"
            :prefix-icon="Lock"
            size="large"
            show-password
          />
        </el-form-item>

        <el-form-item>
          <BlueButton
            block
            size="large"
            :loading="loading"
            @click="handleLogin"
          >
            登 录
          </BlueButton>
        </el-form-item>
      </el-form>

      <!-- 注册链接 -->
      <div class="login-footer text-caption">
        <span>还没有账号？</span>
        <a href="#" @click.prevent="showRegister = true">立即注册</a>
      </div>

      <!-- 提示 -->
      <div class="login-hint text-muted" style="margin-top:16px">
        测试账号：student01 / pass1234
      </div>
    </div>

    <!-- ===== 注册弹窗 ===== -->
    <el-dialog v-model="showRegister" title="用户注册" width="400px">
      <el-form :model="regForm" :rules="regRules" ref="regFormRef" label-width="80px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="regForm.username" placeholder="4-20位字母或数字" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="regForm.password" type="password" show-password placeholder="至少6位" />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="regForm.email" placeholder="选填" />
        </el-form-item>
        <el-form-item label="角色">
          <el-radio-group v-model="regForm.role">
            <el-radio value="student">学生</el-radio>
            <el-radio value="admin">管理员</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showRegister = false">取消</el-button>
        <BlueButton @click="handleRegister" :loading="regLoading">注册</BlueButton>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { Notebook, User, Lock } from '@element-plus/icons-vue'
import BlueButton from '@/components/BlueButton.vue'
import { useUserStore } from '@/stores/user'
import request from '@/utils/request'

const router = useRouter()
const userStore = useUserStore()

const formRef = ref<FormInstance>()
const loading = ref(false)
const form = reactive({ username: 'student01', password: 'pass1234' })
const rules: FormRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

// 注册
const showRegister = ref(false)
const regFormRef = ref<FormInstance>()
const regLoading = ref(false)
const regForm = reactive({ username: '', password: '', email: '', role: 'student' })
const regRules: FormRules = {
  username: [{ required: true, min: 4, max: 20, message: '4-20位', trigger: 'blur' }],
  password: [{ required: true, min: 6, message: '至少6位', trigger: 'blur' }],
}

async function handleLogin() {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    loading.value = true
    try {
      const res: any = await request.post('/auth/login/', {
        username: form.username,
        password: form.password,
      })
      userStore.setAuth(res.access, res.refresh)
      // 获取用户信息
      const me: any = await request.get('/config/user/me/')
      if (me.data) {
        userStore.setUser(me.data)
      }
      ElMessage.success(`欢迎回来，${userStore.username}`)
      router.push('/home')
    } catch {
      ElMessage.error('用户名或密码错误')
    } finally {
      loading.value = false
    }
  })
}

async function handleRegister() {
  if (!regFormRef.value) return
  await regFormRef.value.validate(async (valid) => {
    if (!valid) return
    regLoading.value = true
    try {
      await request.post('/config/user/register/', regForm)
      ElMessage.success('注册成功，请登录')
      showRegister.value = false
    } catch { /* 已全局处理 */ }
    finally { regLoading.value = false }
  })
}

// 已登录则直接跳转
onMounted(() => {
  userStore.restore()
  if (userStore.isLoggedIn) {
    router.push('/home')
  }
})
</script>

<style scoped>
.login-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #e8f1fe 0%, #f0f7ff 50%, #f5f7fa 100%);
}

.login-card {
  width: 400px;
  padding: 40px;
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(41, 129, 253, 0.1);
}

.login-logo {
  text-align: center;
  margin-bottom: 32px;
}

.logo-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 72px;
  height: 72px;
  border-radius: 50%;
  background: var(--color-bg-selected);
  margin-bottom: 12px;
}

.login-logo h1 {
  font-size: 24px;
  font-weight: 700;
  color: var(--color-text-primary);
  margin-bottom: 4px;
}

.login-form {
  margin-bottom: 16px;
}

.login-footer {
  text-align: center;
}

.login-footer a {
  color: var(--color-primary);
  margin-left: 4px;
}

.login-hint {
  text-align: center;
}
</style>
