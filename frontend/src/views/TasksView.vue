<template>
  <Layout>
    <template #sidebar>
      <div class="filter-panel">
        <h4 class="panel-title">任务筛选</h4>

        <div class="filter-group">
          <label class="filter-label">计划</label>
          <el-select v-model="filters.planId" placeholder="全部" clearable size="default" style="width:100%" @change="fetchTasks">
            <el-option v-for="p in planList" :key="p.plan_id" :label="p.plan_id" :value="p.plan_id" />
          </el-select>
        </div>

        <div class="filter-group">
          <label class="filter-label">状态</label>
          <div class="checkbox-group">
            <el-checkbox v-for="s in statusOptions" :key="s.value" v-model="s.checked" size="small" @change="onFilterChange">{{ s.label }}</el-checkbox>
          </div>
        </div>

        <div class="filter-group">
          <label class="filter-label">科目</label>
          <div class="checkbox-group">
            <el-checkbox v-for="sub in subjectList" :key="sub" v-model="subjectChecked[sub]" size="small" @change="onFilterChange">{{ sub }}</el-checkbox>
          </div>
        </div>

        <div class="filter-group">
          <label class="filter-label">日期范围</label>
          <el-date-picker v-model="dateRange" type="daterange" range-separator="至" start-placeholder="开始" end-placeholder="结束" size="default" style="width:100%" value-format="YYYY-MM-DD" @change="onDateRangeChange" />
        </div>

        <el-divider style="margin:12px 0" />
        <button class="reset-btn" @click="resetFilters"><el-icon><Refresh /></el-icon> 重置</button>

        <div class="stats-row">
          <div class="stat-item"><span class="stat-num">{{ tasks.length }}</span><span class="stat-label">总任务</span></div>
          <div class="stat-item"><span class="stat-num">{{ completedCount }}</span><span class="stat-label">已完成</span></div>
        </div>
      </div>
    </template>

    <template #default>
      <div class="task-page">
        <div class="page-header">
          <h1 class="page-title">学习任务规划</h1>
          <div class="header-actions">
            <button class="btn-primary-fill" @click="openAddDialog">
              <el-icon><Plus /></el-icon> 添加任务
            </button>
            <button class="btn-outline" @click="openGenerateDialog">
              <el-icon><MagicStick /></el-icon> AI 生成
            </button>
          </div>
        </div>

        <!-- 甘特图 -->
        <div class="gantt-section">
          <GanttChart :tasks="ganttTasks" />
        </div>

        <!-- 任务表格 -->
        <div class="table-section">
          <el-table :data="displayTasks" stripe size="default" style="width:100%" v-loading="loading" empty-text="暂无任务数据">
            <el-table-column prop="task_id" label="任务ID" width="100" />
            <el-table-column prop="task_name" label="任务名称" min-width="150" />
            <el-table-column prop="subject" label="科目" width="80" />
            <el-table-column label="日期" width="110">
              <template #default="{ row }">{{ row.date }}</template>
            </el-table-column>
            <el-table-column label="时间" width="120">
              <template #default="{ row }">{{ row.start_time }} - {{ row.end_time }}</template>
            </el-table-column>
            <el-table-column prop="duration_minutes" label="时长" width="70">
              <template #default="{ row }">{{ row.duration_minutes }}min</template>
            </el-table-column>
            <el-table-column label="进度" width="120">
              <template #default="{ row }">
                <el-progress :percentage="row.progress || 0" :stroke-width="6" :show-text="true" :color="'#2981fd'" />
              </template>
            </el-table-column>
            <el-table-column label="状态" width="90">
              <template #default="{ row }">
                <el-tag :type="statusTag(row.status)" size="small" effect="plain">{{ statusText(row.status) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="180" fixed="right">
              <template #default="{ row }">
                <el-button link size="small" type="primary" @click="openEditDialog(row)">编辑</el-button>
                <el-button v-if="row.status!=='completed'" link size="small" type="success" @click="finishTask(row.id)">完成</el-button>
                <el-button link size="small" type="danger" @click="deleteTask(row.id)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>

        <!-- ===== 添加 / 编辑任务弹窗 ===== -->
        <el-dialog v-model="dialogVisible" :title="editId ? '编辑任务' : '添加任务'" width="480px" destroy-on-close>
          <el-form :model="form" label-width="90px" ref="formRef" :rules="formRules">
            <el-form-item label="任务名称" prop="task_name">
              <el-input v-model="form.task_name" placeholder="如：复习高等数学" />
            </el-form-item>
            <el-form-item label="科目" prop="subject">
              <el-select v-model="form.subject" placeholder="选择科目" allow-create filterable style="width:100%">
                <el-option v-for="s in subjectList" :key="s" :label="s" :value="s" />
              </el-select>
            </el-form-item>
            <el-form-item label="日期" prop="date">
              <el-date-picker v-model="form.date" type="date" value-format="YYYY-MM-DD" style="width:100%" />
            </el-form-item>
            <el-form-item label="时间">
              <div style="display:flex;gap:8px;width:100%">
                <el-time-picker v-model="form.start_time" format="HH:mm" value-format="HH:mm" placeholder="开始" style="flex:1" />
                <span style="line-height:32px">-</span>
                <el-time-picker v-model="form.end_time" format="HH:mm" value-format="HH:mm" placeholder="结束" style="flex:1" />
              </div>
            </el-form-item>
            <el-form-item label="时长(分钟)">
              <el-input-number v-model="form.duration_minutes" :min="15" :max="480" :step="15" />
            </el-form-item>
            <el-form-item v-if="editId" label="进度">
              <el-slider v-model="form.progress" :min="0" :max="100" />
            </el-form-item>
            <el-form-item v-if="editId" label="状态">
              <el-select v-model="form.status" style="width:100%">
                <el-option value="pending" label="待开始" />
                <el-option value="in_progress" label="进行中" />
                <el-option value="completed" label="已完成" />
                <el-option value="cancelled" label="已取消" />
              </el-select>
            </el-form-item>
          </el-form>
          <template #footer>
            <el-button @click="dialogVisible = false">取消</el-button>
            <button class="btn-primary-fill" @click="handleSubmit" :disabled="submitting">
              {{ editId ? '保存修改' : '添加任务' }}
            </button>
          </template>
        </el-dialog>

        <!-- ===== AI 生成弹窗 ===== -->
        <el-dialog v-model="showGenerateDialog" title="AI 生成学习计划" width="480px">
          <el-form :model="genForm" label-width="110px">
            <el-form-item label="每天学习时长(h)">
              <el-input-number v-model="genForm.daily_study_hours" :min="1" :max="12" />
            </el-form-item>
            <el-form-item label="科目列表">
              <el-select v-model="genForm.subjects" multiple allow-create filterable placeholder="输入科目后回车" style="width:100%" />
            </el-form-item>
            <el-form-item label="开始日期">
              <el-date-picker v-model="genForm.start_date" type="date" value-format="YYYY-MM-DD" style="width:100%" />
            </el-form-item>
            <el-form-item label="计划天数">
              <el-input-number v-model="genForm.days" :min="7" :max="90" />
            </el-form-item>
          </el-form>
          <p style="font-size:12px;color:#e6a23c">将根据你的课表自动规避上课时段</p>
          <template #footer>
            <el-button @click="showGenerateDialog = false">取消</el-button>
            <button class="btn-primary-fill" @click="handleGenerate" :disabled="generating">
              <el-icon><MagicStick /></el-icon> 开始生成
            </button>
          </template>
        </el-dialog>
      </div>
    </template>
  </Layout>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus, MagicStick, Refresh } from '@element-plus/icons-vue'
import Layout from '@/layouts/Layout.vue'
import GanttChart from '@/components/GanttChart.vue'
import type { GanttTask } from '@/components/GanttChart.vue'
import { useAppStore } from '@/stores/app'
import request from '@/utils/request'

interface Task {
  id: number; task_id: string; plan_id: string; task_name: string; subject: string;
  date: string; weekday: number; start_time: string; end_time: string;
  duration_minutes: number; progress: number; status: string; dependencies: string[];
}

const appStore = useAppStore()
const tasks = ref<Task[]>([])
const loading = ref(false)
const planList = ref<{ plan_id: string }[]>([])
const subjectList = ref<string[]>([])
const subjectChecked = reactive<Record<string, boolean>>({})
const dateRange = ref<[string, string] | null>(null)

const filters = reactive({
  planId: undefined as string | undefined,
  activeStatuses: ['pending', 'in_progress', 'completed'],
  activeSubjects: [] as string[],
  startDate: undefined as string | undefined,
  endDate: undefined as string | undefined,
})

const statusOptions = reactive([
  { label: '待开始', value: 'pending', checked: true },
  { label: '进行中', value: 'in_progress', checked: true },
  { label: '已完成', value: 'completed', checked: true },
  { label: '已取消', value: 'cancelled', checked: false },
])

const statusText = (s: string) => ({ pending: '待开始', in_progress: '进行中', completed: '已完成', cancelled: '已取消' }[s] || s)
const statusTag = (s: string) => ({ pending: 'info', in_progress: 'primary', completed: 'success', cancelled: 'danger' }[s] || 'info')

const displayTasks = computed(() => {
  let list = tasks.value
  if (filters.planId) list = list.filter(t => t.plan_id === filters.planId)
  if (filters.activeStatuses.length < 4) list = list.filter(t => filters.activeStatuses.includes(t.status))
  if (filters.activeSubjects.length) list = list.filter(t => filters.activeSubjects.includes(t.subject))
  if (filters.startDate) list = list.filter(t => t.date >= filters.startDate!)
  if (filters.endDate) list = list.filter(t => t.date <= filters.endDate!)
  return list
})

const completedCount = computed(() => tasks.value.filter(t => t.status === 'completed').length)

const ganttTasks = computed<GanttTask[]>(() =>
  displayTasks.value.map(t => ({
    id: t.task_id, name: t.task_name, start: `${t.date}T${t.start_time}`,
    end: `${t.date}T${t.end_time}`, progress: t.progress,
    custom_class: `subject-${t.subject}`, dependencies: t.dependencies,
  }))
)

// 弹窗
const dialogVisible = ref(false)
const editId = ref<number | null>(null)
const submitting = ref(false)
const formRef = ref<FormInstance>()
const form = reactive({ task_name: '', subject: '数学', date: '', start_time: '19:00', end_time: '20:30', duration_minutes: 90, progress: 0, status: 'pending' })
const formRules: FormRules = { task_name: [{ required: true, message: '请输入任务名称', trigger: 'blur' }], subject: [{ required: true, message: '请选择科目', trigger: 'blur' }] }

const showGenerateDialog = ref(false)
const generating = ref(false)
const genForm = reactive({ daily_study_hours: 3, subjects: ['数学', '英语', '专业课'], start_date: '', days: 30 })

function onFilterChange() {
  filters.activeStatuses = statusOptions.filter(s => s.checked).map(s => s.value)
  filters.activeSubjects = subjectList.value.filter(s => subjectChecked[s])
}

function onDateRangeChange(val: [string, string] | null) {
  if (val) { filters.startDate = val[0]; filters.endDate = val[1] }
  else { filters.startDate = undefined; filters.endDate = undefined }
  fetchTasks()
}

async function fetchTasks() {
  loading.value = true
  try {
    const params: any = {}
    if (filters.planId) params.plan_id = filters.planId
    if (filters.startDate) params.start_date = filters.startDate
    if (filters.endDate) params.end_date = filters.endDate
    const res: any = await request.get('/task/', { params })
    const raw = res.data?.results || res.data || []
    tasks.value = raw
    subjectList.value = [...new Set(raw.map((t: Task) => t.subject))] as string[]
    subjectList.value.forEach(s => { if (!(s in subjectChecked)) subjectChecked[s] = true })
    planList.value = [...new Map(raw.map((t: Task) => [t.plan_id, { plan_id: t.plan_id }])).values()] as any
    onFilterChange()
  } catch { /* */ }
  finally { loading.value = false }
}

function openAddDialog() {
  editId.value = null
  const d = new Date()
  form.date = `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`
  form.task_name = ''; form.subject = '数学'; form.start_time = '19:00'; form.end_time = '20:30'
  form.duration_minutes = 90; form.progress = 0; form.status = 'pending'
  dialogVisible.value = true
}

function openEditDialog(t: Task) {
  editId.value = t.id
  form.task_name = t.task_name; form.subject = t.subject; form.date = t.date
  form.start_time = t.start_time; form.end_time = t.end_time
  form.duration_minutes = t.duration_minutes; form.progress = t.progress; form.status = t.status
  dialogVisible.value = true
}

async function handleSubmit() {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    submitting.value = true
    try {
      if (editId.value) {
        await request.patch(`/task/${editId.value}/`, { ...form })
        ElMessage.success('任务已更新')
      } else {
        await request.post('/task/', { ...form, weekday: new Date(form.date).getDay() || 0 })
        ElMessage.success('任务已添加')
      }
      dialogVisible.value = false; fetchTasks()
    } catch { /* */ }
    finally { submitting.value = false }
  })
}

async function finishTask(id: number) {
  try { await request.patch(`/task/${id}/`, { status: 'completed', progress: 100 }); ElMessage.success('任务已完成'); fetchTasks() } catch { /* */ }
}

async function deleteTask(id: number) {
  try { await ElMessageBox.confirm('确定删除该任务？', '提示', { type: 'warning' }) } catch { return }
  try { await request.delete(`/task/${id}/`); ElMessage.success('已删除'); fetchTasks() } catch { /* */ }
}

function openGenerateDialog() {
  const d = new Date()
  genForm.start_date = `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`
  showGenerateDialog.value = true
}

async function handleGenerate() {
  generating.value = true
  try {
    const res: any = await request.post('/task/ai_generate/', genForm)
    ElMessage.success(res.msg || `已生成 ${res.data?.total_tasks || 0} 个任务`)
    showGenerateDialog.value = false; fetchTasks()
  } catch { /* */ }
  finally { generating.value = false }
}

function resetFilters() {
  filters.planId = undefined; filters.startDate = undefined; filters.endDate = undefined
  dateRange.value = null
  statusOptions.forEach(s => s.checked = s.value !== 'cancelled')
  subjectList.value.forEach(s => subjectChecked[s] = true)
  onFilterChange(); fetchTasks()
}

onMounted(() => fetchTasks())
</script>

<style scoped>
.filter-panel { padding: 4px 0; }
.panel-title { font-size: 12px; font-weight: 600; color: #9ca3af; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 14px; }
.filter-group { margin-bottom: 14px; }
.filter-label { display: block; font-size: 12px; color: #9ca3af; margin-bottom: 4px; }
.checkbox-group { display: flex; flex-wrap: wrap; gap: 4px; }

.reset-btn {
  width: 100%; display: flex; align-items: center; justify-content: center;
  gap: 4px; padding: 6px 0; border: none; border-radius: 6px;
  background: #f3f4f6; color: #9ca3af; font-size: 12px; cursor: pointer; transition: all .15s;
}
.reset-btn:hover { background: #e8f1fe; color: #2981fd; }
.stats-row { display: flex; gap: 8px; margin-top: 12px; }
.stat-item { flex:1; text-align: center; padding: 10px 6px; border-radius: 8px; background: #f0f7ff; }
.stat-num { display: block; font-size: 18px; font-weight: 700; color: #2981fd; }
.stat-label { font-size: 11px; color: #9ca3af; }

.task-page { height: 100%; display: flex; flex-direction: column; }
.page-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }
.page-title { font-size: 20px; font-weight: 700; color: #1f2937; margin: 0; }
.header-actions { display: flex; gap: 8px; }

.btn-primary-fill {
  display: flex; align-items: center; gap: 6px; padding: 8px 18px;
  border: none; border-radius: 8px; background: #2981fd; color: #fff;
  font-size: 13px; font-weight: 500; cursor: pointer; transition: all .15s;
}
.btn-primary-fill:hover { background: #1a6fd6; }
.btn-primary-fill:disabled { background: #d1d5db; cursor: not-allowed; }

.btn-outline {
  display: flex; align-items: center; gap: 6px; padding: 8px 18px;
  border: 1px solid #2981fd; border-radius: 8px; background: #fff;
  color: #2981fd; font-size: 13px; font-weight: 500; cursor: pointer; transition: all .15s;
}
.btn-outline:hover { background: #e8f1fe; }

.gantt-section { margin-bottom: 20px; }
.table-section { flex: 1; overflow: auto; }
</style>
