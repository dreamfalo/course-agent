<template>
  <Layout>
    <template #sidebar>
      <div class="sidebar-section">
        <div class="sidebar-header">
          <h4 class="sidebar-title">对话历史</h4>
          <button class="new-chat-btn" @click="startNewChat">
            <el-icon :size="14"><Plus /></el-icon> 新对话
          </button>
        </div>
        <div class="session-list">
          <div
            v-for="s in sessions"
            :key="s.session_id"
            class="session-item"
            :class="{ active: activeSession === s.session_id }"
            @click="switchSession(s.session_id)"
          >
            <el-icon :size="14"><ChatDotSquare /></el-icon>
            <div class="session-info">
              <span class="session-id">{{ s.session_id.slice(0, 8) }}</span>
              <span class="session-time">{{ formatTime(s.last_active) }}</span>
            </div>
            <span class="session-count">{{ s.msg_count }}</span>
            <button class="session-delete" @click.stop="deleteSession(s.session_id)" title="删除对话">
              <el-icon :size="12"><Close /></el-icon>
            </button>
          </div>
          <div v-if="sessions.length === 0" class="empty-sessions">暂无历史对话</div>
        </div>
      </div>
    </template>

    <template #default>
      <div class="chat-page">
        <div class="chat-main">
          <div class="chat-header">
            <h2 class="chat-title"><el-icon><Notebook /></el-icon> AI 课程助手</h2>
            <span class="chat-session" v-if="activeSession">会话: {{ activeSession?.slice(0, 8) }}</span>
          </div>
          <div class="divider" />

          <div class="chat-messages" ref="msgContainer">
            <div v-if="messages.length === 0" class="chat-welcome">
              <el-icon :size="56" color="#d3e4fe"><Notebook /></el-icon>
              <h3>你好，我是课程小助手</h3>
              <p>可以帮你查课表、搜资料、规划学习任务</p>
              <div class="quick-prompts">
                <span class="prompt-chip" @click="sendQuick('帮我查一下这周的课表')">📮 查课表</span>
                <span class="prompt-chip" @click="sendQuick('帮我搜索微积分相关资料')">🔍 搜资料</span>
                <span class="prompt-chip" @click="sendQuick('帮我生成本周的学习计划')">📑 定计划</span>
              </div>
            </div>
            <ChatBubble
              v-for="(msg, idx) in messages"
              :key="idx"
              :role="msg.role"
              :content="msg.content"
              :time="msg.created_at"
              :toolCalls="msg.tool_calls || []"
              :streaming="idx === messages.length - 1 && sending"
            />
          </div>

          <div class="chat-input-bar">
            <div class="input-row">
              <el-input
                v-model="inputText"
                type="textarea"
                :rows="2"
                placeholder="输入你的问题，如「帮我查周三的课表」..."
                @keydown.enter.exact="handleSend"
                :disabled="sending"
                resize="none"
              />
              <button class="send-btn" @click="handleSend" :disabled="sending || !inputText.trim()">
                <el-icon :size="18"><Promotion /></el-icon>
              </button>
            </div>
            <div class="input-hint">Enter 发送 · 支持课表查询、资料搜索、任务规划</div>
          </div>
        </div>
      </div>
    </template>
  </Layout>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import { Plus, Notebook, ChatDotSquare, Promotion, Close } from '@element-plus/icons-vue'
import Layout from '@/layouts/Layout.vue'
import ChatBubble from '@/components/ChatBubble.vue'
import { useUserStore } from '@/stores/user'
import request from '@/utils/request'

interface Message { role: 'user' | 'assistant'; content: string; created_at?: string; tool_calls?: any[] }
interface Session { session_id: string; last_active: string; msg_count: number }

const userStore = useUserStore()
const messages = ref<Message[]>([])
const inputText = ref('')
const sending = ref(false)
const activeSession = ref('')
const sessions = ref<Session[]>([])
const msgContainer = ref<HTMLElement>()

function formatTime(t?: string): string {
  if (!t) return ''
  const d = new Date(t); const now = new Date(); const diff = now.getTime() - d.getTime()
  if (diff < 60000) return '刚才'
  if (diff < 3600000) return Math.floor(diff / 60000) + '分钟前'
  if (diff < 86400000) return Math.floor(diff / 3600000) + '小时前'
  return d.toLocaleDateString('zh-CN')
}

async function fetchSessions() {
  try { const res: any = await request.get('/agent/sessions/'); sessions.value = res.data || [] } catch { /* */ }
}

async function deleteSession(sid: string) {
  try {
    await request.delete('/agent/sessions/delete/', { data: { session_id: sid } })
    if (activeSession.value === sid) { activeSession.value = ''; messages.value = [] }
    fetchSessions()
  } catch { /* */ }
}

async function switchSession(sid: string) {
  activeSession.value = sid; messages.value = []
  try {
    const res: any = await request.get('/agent/history/', { params: { session_id: sid } })
    messages.value = (res.data || []).map((h: any) => ({ role: h.role, content: h.content, created_at: h.created_at, tool_calls: h.tool_calls || [] }))
  } catch { /* */ }
  scrollToBottom()
}

function startNewChat() { activeSession.value = ''; messages.value = []; inputText.value = '' }

async function handleSend() {
  const text = inputText.value.trim()
  if (!text || sending.value) return
  inputText.value = ''
  messages.value.push({ role: 'user', content: text, created_at: new Date().toISOString() })
  sending.value = true; scrollToBottom()
  try {
    const res: any = await request.post('/agent/chat/', {
      message: text, session_id: activeSession.value || undefined, role: userStore.role,
    })
    const data = res.data
    messages.value.push({ role: 'assistant', content: data.response || '', created_at: new Date().toISOString(), tool_calls: data.tool_calls || [] })
    activeSession.value = data.session_id || activeSession.value
    fetchSessions()
  } catch (e: any) {
    messages.value.push({ role: 'assistant', content: '抱歉，请求失败: ' + (e.message || '未知错误'), created_at: new Date().toISOString() })
  } finally { sending.value = false; scrollToBottom() }
}

function sendQuick(text: string) { inputText.value = text; handleSend() }

function scrollToBottom() { nextTick(() => { if (msgContainer.value) msgContainer.value.scrollTop = msgContainer.value.scrollHeight }) }

onMounted(() => fetchSessions())
</script>

<style scoped>
.sidebar-section { padding: 4px 0; }
.sidebar-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }
.sidebar-title { font-size: 12px; font-weight: 600; color: #9ca3af; text-transform: uppercase; letter-spacing: 1px; }
.new-chat-btn {
  display: flex; align-items: center; gap: 4px; padding: 4px 10px;
  border: 1px solid #e5e7eb; border-radius: 6px; background: #fff;
  color: #2981fd; font-size: 12px; cursor: pointer; transition: all .15s;
}
.new-chat-btn:hover { background: #e8f1fe; border-color: #2981fd; }

.session-list { max-height: calc(100vh - 200px); overflow-y: auto; }
.session-item {
  display: flex; align-items: center; gap: 8px; padding: 10px;
  border-radius: 8px; cursor: pointer; transition: all .15s; margin-bottom: 2px;
}
.session-item:hover { background: #e8f1fe; }
.session-item.active { background: #e8f1fe; color: #2981fd; font-weight: 500; }
.session-info { flex: 1; min-width: 0; }
.session-id { display: block; font-size: 13px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.session-time { font-size: 11px; color: #9ca3af; }
.session-delete {
  opacity: 0; background: none; border: none; color: #f56c6c; cursor: pointer; padding: 2px; transition: all .15s;
}
.session-item:hover .session-delete { opacity: 1; }
.session-delete:hover { background: #fef2f2; border-radius: 4px; }

.session-count {
  font-size: 11px; padding: 1px 6px; border-radius: 10px; background: #f3f4f6; color: #9ca3af;
}
.empty-sessions { text-align: center; padding: 24px 0; font-size: 12px; color: #9ca3af; }

.chat-page { height: 100%; display: flex; flex-direction: column; overflow: hidden; }
.chat-main { flex: 1; display: flex; flex-direction: column; min-width: 0; min-height: 0; }
.chat-header { display: flex; align-items: center; gap: 12px; margin-bottom: 8px; flex-shrink: 0; }
.chat-title { font-size: 18px; font-weight: 700; color: #1f2937; display: flex; align-items: center; gap: 8px; margin: 0; }
.chat-session { font-size: 12px; color: #9ca3af; }
.divider { height: 1px; background: #f3f4f6; margin-bottom: 12px; }

.chat-messages {
  flex: 1; overflow-y: auto; padding: 8px 4px; scroll-behavior: smooth;
  min-height: 0;
}
.chat-welcome {
  text-align: center; padding: 60px 20px; display: flex;
  flex-direction: column; align-items: center; gap: 12px;
}
.chat-welcome h3 { font-size: 18px; color: #1f2937; margin: 0; }
.chat-welcome p { font-size: 14px; color: #9ca3af; }
.quick-prompts { display: flex; gap: 8px; margin-top: 16px; flex-wrap: wrap; justify-content: center; }
.prompt-chip {
  padding: 6px 14px; border-radius: 20px; font-size: 13px;
  background: #e8f1fe; color: #2981fd; cursor: pointer;
  transition: all .15s; border: 1px solid transparent;
}
.prompt-chip:hover { border-color: #2981fd; background: #f0f7ff; }

.chat-input-bar { padding: 12px 0 0; border-top: 1px solid #f3f4f6; flex-shrink: 0; }
.input-row { display: flex; gap: 8px; align-items: flex-end; }
.send-btn {
  display: flex; align-items: center; justify-content: center;
  width: 42px; height: 42px; border: none; border-radius: 8px;
  background: #2981fd; color: #fff; cursor: pointer; transition: all .15s; flex-shrink: 0;
}
.send-btn:hover:not(:disabled) { background: #1a6fd6; }
.send-btn:disabled { background: #d1d5db; cursor: not-allowed; }
.input-hint { font-size: 11px; color: #9ca3af; margin-top: 4px; }
</style>
