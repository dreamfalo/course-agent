<template>
  <div class="chat-bubble" :class="[role, { 'is-streaming': streaming }]">
    <div class="bubble-avatar">
      <el-icon v-if="role === 'user'" :size="20"><UserFilled /></el-icon>
      <div v-else class="ai-avatar">
        <el-icon :size="20"><Notebook /></el-icon>
      </div>
    </div>
    <div class="bubble-body">
      <div class="bubble-header">
        <span class="bubble-name">{{ role === 'user' ? '我' : '课程小助手' }}</span>
        <span class="bubble-time">{{ formatTime(time) }}</span>
      </div>
      <div class="bubble-content">
        <!-- 文本内容 -->
        <div class="bubble-text" v-if="content" v-html="renderedContent"></div>

        <!-- 工具调用记录 -->
        <div v-if="toolCalls && toolCalls.length > 0" class="bubble-tools">
          <div
            v-for="(tc, idx) in toolCalls"
            :key="idx"
            class="tool-item"
            :class="{ expanded: expandedTools.has(idx) }"
          >
            <div class="tool-header" @click="toggleTool(idx)">
              <el-icon :size="14" :color="'#67c23a'"><Tools /></el-icon>
              <span class="tool-name">{{ tc.tool }}</span>
              <el-icon :size="14" class="tool-arrow">
                <ArrowDown v-if="expandedTools.has(idx)" />
                <ArrowRight v-else />
              </el-icon>
            </div>
            <div class="tool-detail" v-if="expandedTools.has(idx)">
              <div class="tool-section">
                <span class="tool-label">输入</span>
                <pre>{{ JSON.stringify(tc.input, null, 2) }}</pre>
              </div>
              <div class="tool-section">
                <span class="tool-label">输出</span>
                <pre>{{ tc.output }}</pre>
              </div>
            </div>
          </div>
        </div>

        <!-- 流式指示 -->
        <span v-if="streaming" class="streaming-cursor">▊</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, reactive } from 'vue'
import { UserFilled, Notebook, Tools, ArrowDown, ArrowRight } from '@element-plus/icons-vue'

interface ToolCall {
  tool: string
  input: any
  output: string
}

const props = withDefaults(defineProps<{
  role: 'user' | 'assistant'
  content: string
  time?: string | Date
  toolCalls?: ToolCall[]
  streaming?: boolean
}>(), {
  role: 'user',
  content: '',
  toolCalls: () => [],
  streaming: false,
})

const expandedTools = reactive(new Set<number>())

function toggleTool(idx: number) {
  if (expandedTools.has(idx)) {
    expandedTools.delete(idx)
  } else {
    expandedTools.add(idx)
  }
}

const renderedContent = computed(() => {
  return props.content
    .replace(/\n/g, '<br>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
})

function formatTime(t?: string | Date): string {
  if (!t) return ''
  const d = typeof t === 'string' ? new Date(t) : t
  return d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}
</script>

<style scoped>
.chat-bubble {
  display: flex;
  gap: 10px;
  padding: 8px 0;
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(4px); }
  to { opacity: 1; transform: translateY(0); }
}

.chat-bubble.user {
  flex-direction: row-reverse;
}

.bubble-avatar {
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 14px;
}

.user .bubble-avatar {
  background: var(--color-primary);
}

.assistant .bubble-avatar .ai-avatar {
  background: linear-gradient(135deg, #67c23a, #85ce61);
  border-radius: 50%;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}

.bubble-body {
  max-width: 75%;
  min-width: 100px;
}

.bubble-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.user .bubble-header {
  flex-direction: row-reverse;
}

.bubble-name {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text-secondary);
}

.bubble-time {
  font-size: 11px;
  color: var(--color-text-placeholder);
}

.bubble-content {
  position: relative;
}

.bubble-text {
  padding: 10px 14px;
  border-radius: var(--radius-lg);
  font-size: 14px;
  line-height: 1.6;
  color: var(--color-text-primary);
  word-break: break-word;
}

.user .bubble-text {
  background: var(--color-primary);
  color: #fff;
  border-bottom-right-radius: 4px;
}

.assistant .bubble-text {
  background: var(--color-bg-white);
  border: 1px solid var(--color-border-light);
  border-bottom-left-radius: 4px;
}

.bubble-tools {
  margin-top: 6px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.tool-item {
  background: var(--color-bg-card-hover);
  border: 1px solid var(--color-border-light);
  border-radius: 6px;
  overflow: hidden;
  font-size: 12px;
}

.tool-header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  cursor: pointer;
  transition: background var(--transition-fast);
}

.tool-header:hover {
  background: var(--color-bg-selected);
}

.tool-name {
  flex: 1;
  font-weight: 500;
  color: var(--color-text-regular);
}

.tool-arrow {
  color: var(--color-text-placeholder);
}

.tool-detail {
  padding: 8px 10px;
  border-top: 1px solid var(--color-border-light);
  background: var(--color-bg-white);
}

.tool-section {
  margin-bottom: 6px;
}

.tool-label {
  display: inline-block;
  font-size: 11px;
  font-weight: 600;
  color: var(--color-text-secondary);
  margin-bottom: 2px;
}

pre {
  font-size: 11px;
  color: var(--color-text-regular);
  background: #f8f9fc;
  padding: 6px 8px;
  border-radius: 4px;
  overflow-x: auto;
  white-space: pre-wrap;
  word-break: break-all;
  margin: 0;
}

.streaming-cursor {
  color: var(--color-primary);
  animation: blink 0.8s infinite;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}
</style>
