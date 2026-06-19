import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

/** 课程绑定信息 */
export interface BoundCourse {
  course_id: string
  course_name: string
}

/** DeepSeek 模型参数 */
export interface LLMParams {
  model: string
  temperature: number
  max_tokens: number
  top_p: number
}

export const useAppStore = defineStore('app', () => {
  // ── 当前学期 ──
  const semester = ref<string>('2025-2026-2')
  const semesterOptions = ref([
    { label: '2025-2026-2', value: '2025-2026-2' },
    { label: '2025-2026-1', value: '2025-2026-1' },
    { label: '2024-2025-2', value: '2024-2025-2' },
  ])

  // ── 绑定课程 ──
  const boundCourse = ref<BoundCourse | null>(null)

  // ── DeepSeek 模型参数 ──
  const llmParams = ref<LLMParams>({
    model: 'deepseek-chat',
    temperature: 0.7,
    max_tokens: 4096,
    top_p: 0.9,
  })

  const modelOptions = ref([
    { label: 'DeepSeek Chat', value: 'deepseek-chat' },
    { label: 'DeepSeek Coder', value: 'deepseek-coder' },
  ])

  // ── 侧边栏 ──
  const sidebarCollapsed = ref(false)

  // ── 通知 ──
  const unreadCount = ref(0)

  function setSemester(s: string) {
    semester.value = s
  }

  function bindCourse(course: BoundCourse | null) {
    boundCourse.value = course
  }

  function updateLLMParam(key: keyof LLMParams, value: any) {
    (llmParams.value as any)[key] = value
  }

  function toggleSidebar() {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }

  function setUnreadCount(n: number) {
    unreadCount.value = n
  }

  return {
    semester, semesterOptions,
    boundCourse,
    llmParams, modelOptions,
    sidebarCollapsed,
    unreadCount,
    setSemester, bindCourse, updateLLMParam, toggleSidebar, setUnreadCount,
  }
}, {
  persist: {
    key: 'app-store',
    storage: localStorage,
    paths: ['semester', 'boundCourse', 'llmParams'],
  },
})
