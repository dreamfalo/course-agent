<template>
  <Layout>
    <template #default>
      <div class="home-page">
        <!-- 欢迎横幅 -->
        <div class="welcome-banner">
          <div class="welcome-text">
            <h2>你好，{{ userStore.username }} 👋</h2>
            <p class="welcome-sub">{{ today }} · {{ weekdayCn }} · 继续你的学习之旅</p>
          </div>
          <el-icon :size="48" color="#d3e4fe"><Notebook /></el-icon>
        </div>

        <!-- 统计卡片 -->
        <div class="stats-row">
          <div class="stat-card" @click="$router.push('/schedule')">
            <div class="stat-icon" style="background:#e8f1fe"><el-icon :size="20" color="#2981fd"><Calendar /></el-icon></div>
            <div class="stat-info"><span class="stat-num">{{ stats.scheduleCount }}</span><span class="stat-label">本周课程</span></div>
          </div>
          <div class="stat-card" @click="$router.push('/tasks')">
            <div class="stat-icon" style="background:#e8f8e8"><el-icon :size="20" color="#67c23a"><List /></el-icon></div>
            <div class="stat-info"><span class="stat-num">{{ stats.taskCount }}</span><span class="stat-label">待完成任务</span></div>
          </div>
        </div>

        <!-- 双栏内容 -->
        <div class="content-row">
          <!-- 左侧：学习动态 + 折线图 -->
          <div class="content-left">
            <div class="section-header">
              <h3 class="section-title"><el-icon><TrendCharts /></el-icon> 一周学习动态</h3>
            </div>
            <div class="chart-wrapper">
              <LineChart :data="chartData" :width="560" :height="180" />
            </div>
            
          </div>

          <!-- 右侧：学习笔记 -->
          <div class="content-right">
            <div class="section-header">
              <h3 class="section-title"><el-icon><EditPen /></el-icon> 学习笔记</h3>
              <button class="add-note-btn" @click="openNoteDialog(null)">
                <el-icon :size="14"><Plus /></el-icon> 添加
              </button>
            </div>
            <div class="notes-list">
              <div v-for="note in notes" :key="note.id" class="note-card">
                <div class="note-bar" :style="{ background: note.color }"></div>
                <div class="note-body">
                  <h4 class="note-title">{{ note.title }}</h4>
                  <p class="note-content">{{ note.content }}</p>
                  <div class="note-footer">
                    <span class="note-time">{{ note.updated_at?.slice(0, 16) || '' }}</span>
                    <div class="note-actions">
                      <el-button link size="small" type="primary" @click="openNoteDialog(note)"><el-icon><Edit /></el-icon></el-button>
                      <el-button link size="small" type="danger" @click="deleteNote(note.id)"><el-icon><Delete /></el-icon></el-button>
                    </div>
                  </div>
                </div>
              </div>
              <div v-if="notes.length === 0" class="notes-empty">
                <el-icon :size="32" color="#d3e4fe"><EditPen /></el-icon>
                <p>暂无笔记，点击上方添加</p>
              </div>
            </div>
          </div>
        </div>

        <!-- 笔记弹窗 -->
        <el-dialog v-model="noteDialogVisible" :title="editingNote ? '编辑笔记' : '添加笔记'" width="440px" destroy-on-close>
          <el-form :model="noteForm" label-width="60px" ref="noteFormRef">
            <el-form-item label="标题" prop="title" :rules="[{ required: true, message: '请输入标题' }]">
              <el-input v-model="noteForm.title" placeholder="笔记标题" />
            </el-form-item>
            <el-form-item label="内容">
              <el-input v-model="noteForm.content" type="textarea" :rows="5" placeholder="笔记内容..." />
            </el-form-item>
            <el-form-item label="颜色">
              <div class="color-picker">
                <span v-for="c in noteColors" :key="c" class="color-dot" :class="{ active: noteForm.color === c }" :style="{ background: c }" @click="noteForm.color = c"></span>
              </div>
            </el-form-item>
          </el-form>
          <template #footer>
            <el-button @click="noteDialogVisible = false">取消</el-button>
            <button class="btn-primary-fill" @click="saveNote" :disabled="noteSaving">
              {{ editingNote ? '保存' : '添加' }}
            </button>
          </template>
        </el-dialog>
      </div>
    </template>
  </Layout>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Notebook, Calendar, List, TrendCharts, EditPen, Plus, Edit, Delete } from '@element-plus/icons-vue'
import Layout from '@/layouts/Layout.vue'
import LineChart from '@/components/LineChart.vue'
import { useUserStore } from '@/stores/user'
import request from '@/utils/request'

interface Note { id: number; title: string; content: string; color: string; updated_at?: string }

const router = useRouter()
const userStore = useUserStore()
const weekdays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
const today = new Date().toLocaleDateString('zh-CN')
const weekdayCn = weekdays[new Date().getDay()]

const stats = reactive({ scheduleCount: 0, taskCount: 0 })
const chartData = ref<{ label: string; value: number }[]>([])
const notes = ref<Note[]>([])

const noteColors = ['#2981fd', '#67c23a', '#e6a23c', '#7b5ce7', '#f56c6c', '#909399']
const noteDialogVisible = ref(false)
const noteSaving = ref(false)
const editingNote = ref<Note | null>(null)
const noteForm = reactive({ title: '', content: '', color: '#2981fd' })
const noteFormRef = ref()

function openNoteDialog(note: Note | null) {
  editingNote.value = note
  if (note) { noteForm.title = note.title; noteForm.content = note.content; noteForm.color = note.color }
  else { noteForm.title = ''; noteForm.content = ''; noteForm.color = '#2981fd' }
  noteDialogVisible.value = true
}

async function saveNote() {
  noteSaving.value = true
  try {
    if (editingNote.value) {
      await request.put(`/config/system/${editingNote.value.id}/`, {
        config_key: `note_${editingNote.value.id}`, config_value: JSON.stringify({ title: noteForm.title, content: noteForm.content, color: noteForm.color }), config_type: 'json', category: 'general',
      })
      ElMessage.success('笔记已更新')
    } else {
      const id = Date.now()
      await request.post('/config/system/', {
        config_key: `note_${id}`, config_value: JSON.stringify({ title: noteForm.title, content: noteForm.content, color: noteForm.color }), config_type: 'json', category: 'general',
      })
      ElMessage.success('笔记已添加')
    }
    noteDialogVisible.value = false; fetchNotes()
  } catch { /* */ }
  finally { noteSaving.value = false }
}

async function deleteNote(id: number) {
  try { await ElMessageBox.confirm('删除这条笔记？', '提示', { type: 'warning' }) } catch { return }
  try { await request.delete(`/config/system/${id}/`); ElMessage.success('已删除'); fetchNotes() } catch { /* */ }
}

async function fetchNotes() {
  try {
    const res: any = await request.get('/config/system/', { params: { category: 'general' } })
    const all = res.data?.results || res.data || []
    notes.value = all.filter((c: any) => c.config_key?.startsWith('note_')).map((c: any) => {
      try { const p = JSON.parse(c.config_value); return { id: c.id, title: p.title || '', content: p.content || '', color: p.color || '#2981fd', updated_at: c.updated_at } }
      catch { return { id: c.id, title: c.config_value || '', content: '', color: '#2981fd', updated_at: c.updated_at } }
    }).sort((a: Note, b: Note) => (b.updated_at || '').localeCompare(a.updated_at || ''))
  } catch { /* */ }
}

onMounted(async () => {
  try {
    const [sch, task] = await Promise.allSettled([request.get('/schedule/'), request.get('/task/')])
    if (sch.status === 'fulfilled') stats.scheduleCount = sch.value?.data?.total || 0
    if (task.status === 'fulfilled') stats.taskCount = task.value?.data?.total || 0
  } catch { /* */ }

  const todayDate = new Date()
  const colors = ['#2981fd', '#67c23a', '#e6a23c', '#7b5ce7', '#f56c6c', '#909399', '#2981fd']
  const studyHours = [2.5, 1.5, 3, 2, 1, 3.5, 2]
  const days = ['一', '二', '三', '四', '五', '六', '日']
  for (let i = 6; i >= 0; i--) {
    const d = new Date(todayDate); d.setDate(d.getDate() - i)
    chartData.value.push({ label: days[(d.getDay() + 6) % 7], value: studyHours[i] })}

  fetchNotes()
})
</script>

<style scoped>
.home-page { max-width: 1100px; margin: 0 auto; }

.welcome-banner {
  display: flex; align-items: center; justify-content: space-between;
  background: linear-gradient(135deg, #e8f1fe, #f0f7ff);
  border-radius: 12px; padding: 24px 28px; margin-bottom: 24px;
}
.welcome-text h2 { font-size: 22px; font-weight: 700; color: #1f2937; margin: 0 0 4px; }
.welcome-sub { font-size: 14px; color: #6b7280; margin: 0; }

.stats-row { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; margin-bottom: 24px; }
.stat-card {
  display: flex; align-items: center; gap: 14px;
  background: #fff; border-radius: 10px; padding: 16px 20px;
  border: 1px solid #f3f4f6; cursor: pointer; transition: all .15s;
}
.stat-card:hover { border-color: #2981fd; background: #f0f7ff; }
.stat-icon { display: flex; align-items: center; justify-content: center; width: 44px; height: 44px; border-radius: 10px; }
.stat-num { display: block; font-size: 22px; font-weight: 700; color: #1f2937; }
.stat-label { font-size: 12px; color: #9ca3af; }

.content-row { display: flex; gap: 20px; }
.content-left { flex: 1; min-width: 0; }
.content-right { width: 380px; flex-shrink: 0; }

.section-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }
.section-title { font-size: 15px; font-weight: 600; color: #1f2937; display: flex; align-items: center; gap: 6px; margin: 0; }

.add-note-btn {
  display: flex; align-items: center; gap: 4px; padding: 5px 12px;
  border: 1px solid #2981fd; border-radius: 6px; background: #fff;
  color: #2981fd; font-size: 12px; cursor: pointer; transition: all .15s;
}
.add-note-btn:hover { background: #e8f1fe; }

.chart-wrapper { margin-bottom: 16px; overflow-x: auto; }


.notes-list { display: flex; flex-direction: column; gap: 8px; max-height: 440px; overflow-y: auto; }
.note-card {
  display: flex; background: #e8f1fe; border: 1px solid #d3e4fe;
  border-radius: 8px; overflow: hidden; transition: all .15s;
}
.note-card:hover { border-color: #2981fd; background: #dbeafe; }
.note-bar { width: 4px; flex-shrink: 0; border-radius: 4px 0 0 4px; }
.note-body { padding: 12px 14px; flex: 1; min-width: 0; }
.note-title { font-size: 14px; font-weight: 600; color: #1f2937; margin: 0 0 4px; }
.note-content {
  font-size: 13px; color: #6b7280; margin: 0 0 8px; line-height: 1.5;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
}
.note-footer { display: flex; align-items: center; justify-content: space-between; }
.note-time { font-size: 11px; color: #9ca3af; }
.note-actions { display: flex; gap: 2px; }
.notes-empty { text-align: center; padding: 32px 0; color: #9ca3af; }
.notes-empty p { font-size: 13px; margin-top: 8px; }

.color-picker { display: flex; gap: 8px; }
.color-dot { width: 24px; height: 24px; border-radius: 50%; cursor: pointer; border: 2px solid transparent; transition: all .15s; }
.color-dot:hover { transform: scale(1.15); }
.color-dot.active { border-color: #1f2937; }

.btn-primary-fill {
  padding: 8px 20px; border: none; border-radius: 8px;
  background: #2981fd; color: #fff; font-size: 13px; font-weight: 500;
  cursor: pointer; transition: all .15s;
}
.btn-primary-fill:hover { background: #1a6fd6; }
.btn-primary-fill:disabled { background: #d1d5db; cursor: not-allowed; }
</style>
