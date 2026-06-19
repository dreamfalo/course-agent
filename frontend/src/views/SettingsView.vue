<template>
  <Layout>
    <!-- ========== 左侧菜单 ========== -->
    <template #sidebar>
      <div class="sidebar-section">
        <h4 class="sidebar-title">系统设置</h4>
        <div class="menu-list">
          <div
            v-for="item in menuItems"
            :key="item.key"
            class="menu-item"
            :class="{ active: activeMenu === item.key }"
            @click="activeMenu = item.key"
          >
            <el-icon :size="16"><component :is="item.icon" /></el-icon>
            <span class="menu-text">{{ item.label }}</span>
          </div>
        </div>
      </div>
    </template>

    <!-- ========== 右侧表单卡片 ========== -->
    <template #default>
      <div class="settings-page">
        <h2 class="text-title mb-16">{{ currentMenu?.label }}</h2>
        <div class="divider" />

        <!-- ===== DeepSeek 模型配置 ===== -->
        <div v-if="activeMenu === 'deepseek'" class="config-section">
          <div class="card-base">
            <h5 class="config-title">
              <el-icon><Cpu /></el-icon> DeepSeek API 配置
            </h5>
            <el-form label-width="140px" label-position="left">
              <el-form-item label="API 密钥">
                <el-input v-model="deepseekForm.api_key" type="password" show-password placeholder="sk-..." />
                <span class="form-hint text-caption">密钥将以加密方式存储</span>
              </el-form-item>
              <el-form-item label="API 地址">
                <el-input v-model="deepseekForm.api_base" placeholder="https://api.deepseek.com/v1" />
              </el-form-item>
              <el-form-item label="默认模型">
                <el-select v-model="deepseekForm.model" style="width:100%">
                  <el-option value="deepseek-chat" label="DeepSeek Chat" />
                  <el-option value="deepseek-coder" label="DeepSeek Coder" />
                </el-select>
              </el-form-item>
              <el-form-item label="Temperature">
                <el-slider v-model="deepseekForm.temperature" :min="0" :max="2" :step="0.1" show-input />
              </el-form-item>
              <el-form-item label="Max Tokens">
                <el-input-number v-model="deepseekForm.max_tokens" :min="256" :max="8192" :step="256" />
              </el-form-item>
              <el-form-item label="Top P">
                <el-slider v-model="deepseekForm.top_p" :min="0" :max="1" :step="0.05" show-input />
              </el-form-item>
            </el-form>
          </div>
        </div>

        <!-- ===== 向量库配置 ===== -->
        <div v-if="activeMenu === 'vector'" class="config-section">
          <div class="card-base">
            <h5 class="config-title">
              <el-icon><DataBoard /></el-icon> Chroma 向量库配置
            </h5>
            <el-form label-width="140px" label-position="left">
              <el-form-item label="持久化目录">
                <el-input v-model="vectorForm.persist_dir" placeholder="./chroma_db" />
              </el-form-item>
              <el-form-item label="Collection 名称">
                <el-input v-model="vectorForm.collection_name" placeholder="course_documents" />
              </el-form-item>
              <el-form-item label="文档分块大小">
                <el-input-number v-model="vectorForm.chunk_size" :min="100" :max="2000" :step="50" />
              </el-form-item>
              <el-form-item label="分块重叠大小">
                <el-input-number v-model="vectorForm.chunk_overlap" :min="0" :max="500" :step="10" />
              </el-form-item>
              <el-form-item label="Embedding 模型">
                <el-select v-model="vectorForm.embedding_model" style="width:100%">
                  <el-option value="text-embedding-3-small" label="text-embedding-3-small" />
                  <el-option value="text-embedding-3-large" label="text-embedding-3-large" />
                  <el-option value="text-embedding-ada-002" label="text-embedding-ada-002" />
                </el-select>
              </el-form-item>
            </el-form>
          </div>
        </div>

        <!-- ===== 课表导出设置 ===== -->
        <div v-if="activeMenu === 'export'" class="config-section">
          <div class="card-base">
            <h5 class="config-title">
              <el-icon><Download /></el-icon> 课表导出设置
            </h5>
            <el-form label-width="140px" label-position="left">
              <el-form-item label="默认导出格式">
                <el-radio-group v-model="exportForm.default_format">
                  <el-radio value="csv">CSV</el-radio>
                  <el-radio value="excel">Excel</el-radio>
                  <el-radio value="ics">ICS 日历</el-radio>
                </el-radio-group>
              </el-form-item>
              <el-form-item label="默认学期">
                <el-input v-model="exportForm.default_semester" placeholder="2025-2026-2" />
              </el-form-item>
              <el-form-item label="包含已取消课程">
                <el-switch v-model="exportForm.include_cancelled" />
              </el-form-item>
              <el-form-item label="时间格式">
                <el-select v-model="exportForm.time_format" style="width:200px">
                  <el-option value="24h" label="24小时制 (08:00)" />
                  <el-option value="12h" label="12小时制 (8:00 AM)" />
                </el-select>
              </el-form-item>
            </el-form>
          </div>
        </div>

        <!-- ===== 消息提醒 ===== -->
        <div v-if="activeMenu === 'notification'" class="config-section">
          <div class="card-base">
            <h5 class="config-title">
              <el-icon><Bell /></el-icon> 消息提醒配置
            </h5>
            <el-form label-width="140px" label-position="left">
              <el-form-item label="启用通知">
                <el-switch v-model="notifyForm.enabled" />
              </el-form-item>
              <el-form-item label="上课前提醒">
                <el-switch v-model="notifyForm.class_reminder" />
                <span class="form-hint text-caption ml-8">提前15分钟提醒</span>
              </el-form-item>
              <el-form-item label="任务截止提醒">
                <el-switch v-model="notifyForm.task_reminder" />
                <span class="form-hint text-caption ml-8">任务截止前1天提醒</span>
              </el-form-item>
              <el-form-item label="提醒方式">
                <el-checkbox-group v-model="notifyForm.remind_methods">
                  <el-checkbox value="web" label="站内消息" />
                  <el-checkbox value="email" label="邮件" />
                  <el-checkbox value="sms" label="短信" />
                </el-checkbox-group>
              </el-form-item>
            </el-form>
          </div>
        </div>

        <!-- ===== 账号管理 ===== -->
        <div v-if="activeMenu === 'account'" class="config-section">
          <div class="card-base mb-12">
            <h5 class="config-title">
              <el-icon><UserFilled /></el-icon> 当前账号信息
            </h5>
            <el-form label-width="80px" label-position="left">
              <el-form-item label="用户名">
                <el-input v-model="accountForm.username" placeholder="输入新用户名" maxlength="20" show-word-limit />
              </el-form-item>
              <el-form-item label="新密码">
                <el-input v-model="accountForm.new_password" type="password" show-password placeholder="留空则不修改密码" />
              </el-form-item>
              <el-form-item label="角色">
                <el-tag :type="userStore.isAdmin ? 'danger' : 'primary'" effect="plain">
                  {{ userStore.isAdmin ? '管理员' : '学生' }}
                </el-tag>
              </el-form-item>
              <el-form-item label="邮箱">
                <el-input v-model="accountForm.email" placeholder="your@email.com" />
              </el-form-item>
              <el-form-item label="手机号">
                <el-input v-model="accountForm.phone" placeholder="13800000000" />
              </el-form-item>
            </el-form>
          </div>

          <div class="card-base">
            <h5 class="config-title">
              <el-icon><Lock /></el-icon> 修改密码
            </h5>
            <el-form label-width="100px" label-position="left">
              <el-form-item label="当前密码">
                <el-input v-model="pwdForm.old_password" type="password" show-password />
              </el-form-item>
              <el-form-item label="新密码">
                <el-input v-model="pwdForm.new_password" type="password" show-password />
              </el-form-item>
              <el-form-item label="确认密码">
                <el-input v-model="pwdForm.confirm_password" type="password" show-password />
              </el-form-item>
            </el-form>
          </div>

          <!-- 管理员：批量用户管理 -->
          <div v-if="userStore.isAdmin" class="card-base mt-12">
            <h5 class="config-title">
              <el-icon><List /></el-icon> 用户列表（管理员）
            </h5>
            <el-table :data="userList" stripe size="small" style="width:100%">
              <el-table-column prop="username" label="用户名" width="120" />
              <el-table-column prop="email" label="邮箱" min-width="180" />
              <el-table-column prop="role" label="角色" width="80">
                <template #default="{ row }">
                  <el-tag :type="row.role === 'admin' ? 'danger' : 'primary'" size="small" effect="plain">
                    {{ row.role === 'admin' ? '管理员' : '学生' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="is_active" label="状态" width="80">
                <template #default="{ row }">
                  <el-switch v-model="row.is_active" size="small" @change="toggleUserActive(row)" />
                </template>
              </el-table-column>
              <el-table-column prop="date_joined" label="注册时间" width="160" />
            </el-table>
          </div>
        </div>

        <!-- 保存按钮 -->
        <div class="save-bar mt-20" v-if="activeMenu !== 'account'">
          <BlueButton @click="handleSaveConfig" :loading="savingConfig" :icon="Select">
            保存配置
          </BlueButton>
          <el-button @click="resetCurrentForm">重置</el-button>
        </div>
        <div class="save-bar mt-20" v-else>
          <BlueButton @click="handleSaveAccount" :loading="savingAccount" :icon="Select">
            保存账号信息
          </BlueButton>
        </div>
      </div>
    </template>
  </Layout>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Cpu, DataBoard, Download, Bell, UserFilled, Lock, List, Select,
} from '@element-plus/icons-vue'
import Layout from '@/layouts/Layout.vue'
import BlueButton from '@/components/BlueButton.vue'
import { useUserStore } from '@/stores/user'
import { useAppStore } from '@/stores/app'
import request from '@/utils/request'

interface MenuItem { key: string; label: string; icon: any }

const userStore = useUserStore()
const appStore = useAppStore()

const menuItems: MenuItem[] = [
  { key: 'deepseek', label: 'DeepSeek 模型配置', icon: Cpu },
  { key: 'vector', label: '向量库配置', icon: DataBoard },
  { key: 'export', label: '课表导出设置', icon: Download },
  { key: 'notification', label: '消息提醒', icon: Bell },
  { key: 'account', label: '账号管理', icon: UserFilled },
]

const activeMenu = ref('deepseek')
const savingConfig = ref(false)
const savingAccount = ref(false)

const currentMenu = computed(() => menuItems.find(m => m.key === activeMenu.value))

// DeepSeek 表单
const deepseekForm = reactive({
  api_key: '', api_base: 'https://api.deepseek.com/v1',
  model: 'deepseek-chat', temperature: 0.7, max_tokens: 4096, top_p: 0.9,
})

// 向量库表单
const vectorForm = reactive({
  persist_dir: './chroma_db', collection_name: 'course_documents',
  chunk_size: 500, chunk_overlap: 50, embedding_model: 'text-embedding-3-small',
})

// 导出表单
const exportForm = reactive({
  default_format: 'csv', default_semester: '2025-2026-2',
  include_cancelled: false, time_format: '24h',
})

// 通知表单
const notifyForm = reactive({
  enabled: true, class_reminder: true, task_reminder: true,
  remind_methods: ['web'] as string[],
})

// 账号表单
const accountForm = reactive({ username: '', new_password: '', email: '', phone: '' })
const pwdForm = reactive({ old_password: '', new_password: '', confirm_password: '' })
const userList = ref<any[]>([])

async function handleSaveConfig() {
  savingConfig.value = true
  try {
    const configs: any[] = []
    if (activeMenu.value === 'deepseek') {
      Object.entries(deepseekForm).forEach(([k, v]) => {
        configs.push({ config_key: `deepseek_${k}`, config_value: String(v), config_type: k === 'api_key' ? 'secret' : 'string', category: 'llm' })
      })
    } else if (activeMenu.value === 'vector') {
      Object.entries(vectorForm).forEach(([k, v]) => {
        configs.push({ config_key: `chroma_${k}`, config_value: String(v), config_type: 'string', category: 'vector' })
      })
    } else if (activeMenu.value === 'export') {
      Object.entries(exportForm).forEach(([k, v]) => {
        configs.push({ config_key: `export_${k}`, config_value: String(v), config_type: 'string', category: 'general' })
      })
    } else if (activeMenu.value === 'notification') {
      Object.entries(notifyForm).forEach(([k, v]) => {
        configs.push({ config_key: `notify_${k}`, config_value: Array.isArray(v) ? JSON.stringify(v) : String(v), config_type: 'string', category: 'notification' })
      })
    }
    for (const cfg of configs) {
      try { await request.post('/config/system/', cfg) } catch { /* */ }
    }
    ElMessage.success('配置已保存')
    // 同步到 appStore
    appStore.updateLLMParam('model', deepseekForm.model as any)
    appStore.updateLLMParam('temperature', deepseekForm.temperature as any)
    appStore.updateLLMParam('max_tokens', deepseekForm.max_tokens as any)
    appStore.updateLLMParam('top_p', deepseekForm.top_p as any)
  } catch { /* */ }
  finally { savingConfig.value = false }
}

async function handleSaveAccount() {
  savingAccount.value = true
  try {
    const payload: any = {
      username: accountForm.username,
      email: accountForm.email,
      phone: accountForm.phone,
    }
    if (accountForm.new_password) {
      payload.password = accountForm.new_password
    }
    await request.patch('/config/user/me/', payload)
    if (accountForm.username && accountForm.username !== userStore.username) {
      userStore.username = accountForm.username
    }
    ElMessage.success('账号信息已更新')
  } catch { /* */ }
  finally { savingAccount.value = false }
}

function resetCurrentForm() {
  if (activeMenu.value === 'deepseek') {
    Object.assign(deepseekForm, {
      api_base: 'https://api.deepseek.com/v1', model: 'deepseek-chat',
      temperature: 0.7, max_tokens: 4096, top_p: 0.9,
    })
  } else if (activeMenu.value === 'vector') {
    Object.assign(vectorForm, {
      persist_dir: './chroma_db', collection_name: 'course_documents',
      chunk_size: 500, chunk_overlap: 50, embedding_model: 'text-embedding-3-small',
    })
  } else if (activeMenu.value === 'export') {
    Object.assign(exportForm, {
      default_format: 'csv', default_semester: '2025-2026-2',
      include_cancelled: false, time_format: '24h',
    })
  } else if (activeMenu.value === 'notification') {
    Object.assign(notifyForm, {
      enabled: true, class_reminder: true, task_reminder: true,
      remind_methods: ['web'],
    })
  }
}

async function toggleUserActive(row: any) {
  try {
    await request.patch(`/config/user/${row.id}/`, { is_active: row.is_active })
  } catch { /* */ }
}

async function fetchUsers() {
  if (!userStore.isAdmin) return
  try {
    const res: any = await request.get('/config/user/')
    userList.value = res.data?.results || res.data || []
  } catch { /* */ }
}

async function fetchConfigs() {
  try {
    const res: any = await request.get('/config/system/public/')
    const data = res.data || {}
    if (data.deepseek_api_base) deepseekForm.api_base = data.deepseek_api_base
    if (data.deepseek_model) deepseekForm.model = data.deepseek_model
    if (data.deepseek_temperature) deepseekForm.temperature = parseFloat(data.deepseek_temperature)
    if (data.deepseek_max_tokens) deepseekForm.max_tokens = parseInt(data.deepseek_max_tokens)
    if (data.chroma_persist_dir) vectorForm.persist_dir = data.chroma_persist_dir
    if (data.chroma_chunk_size) vectorForm.chunk_size = parseInt(data.chroma_chunk_size)
    if (data.chroma_chunk_overlap) vectorForm.chunk_overlap = parseInt(data.chroma_chunk_overlap)
  } catch { /* */ }
}

onMounted(() => {
  accountForm.username = userStore.username
  accountForm.email = userStore.email
  accountForm.phone = userStore.phone
  deepseekForm.model = appStore.llmParams.model
  deepseekForm.temperature = appStore.llmParams.temperature
  deepseekForm.max_tokens = appStore.llmParams.max_tokens
  deepseekForm.top_p = appStore.llmParams.top_p
  fetchUsers()
  fetchConfigs()
})
</script>

<style scoped>
.sidebar-section { padding: 4px 0; }
.sidebar-title {
  font-size: 13px; font-weight: 600; color: var(--color-text-secondary);
  text-transform: uppercase; letter-spacing: 1px; margin-bottom: 16px;
}
.menu-list { display: flex; flex-direction: column; gap: 2px; }
.menu-item {
  display: flex; align-items: center; gap: 10px;
  padding: 10px 12px; border-radius: var(--radius-base);
  cursor: pointer; transition: all var(--transition-fast);
  color: var(--color-text-regular); font-size: 13px;
}
.menu-item:hover { background: var(--color-bg-card-hover); color: var(--color-primary); }
.menu-item.active { background: var(--color-bg-selected); color: var(--color-primary); font-weight: 600; }
.menu-text { white-space: nowrap; }

.settings-page { max-width: 720px; }
.mb-16 { margin-bottom: 16px; }
.mb-12 { margin-bottom: 12px; }
.mt-12 { margin-top: 12px; }
.mt-20 { margin-top: 20px; }
.ml-8 { margin-left: 8px; }

.config-section { margin-top: 16px; }
.config-title {
  display: flex; align-items: center; gap: 8px;
  font-size: 15px; font-weight: 600; color: var(--color-text-primary);
  margin-bottom: 20px; padding-bottom: 12px;
  border-bottom: 1px solid var(--color-border-light);
}

.form-hint { display: block; color: var(--color-text-secondary); margin-top: 2px; }

.save-bar { display: flex; gap: 12px; align-items: center; }
</style>
