<template>
  <Layout>
    <template #sidebar>
      <div class="filter-panel">
        <div class="filter-section">
          <label class="filter-label">学期</label>
          <el-select v-model="filters.semester" size="default" style="width:100%" @change="onFilterChange">
            <el-option v-for="s in appStore.semesterOptions" :key="s.value" :label="s.label" :value="s.value" />
          </el-select>
        </div>
        <div class="filter-section">
          <label class="filter-label">当前周</label>
          <div style="display:flex;align-items:center;gap:6px">
            <button class="week-nav-btn small" :disabled="currentWeek <= 1" @click="prevWeek()">
              <el-icon :size="12"><ArrowLeft /></el-icon>
            </button>
            <el-input-number v-model="currentWeek" :min="1" :max="20" size="small" controls-position="right" style="width:100%" @change="onWeekChange" />
            <button class="week-nav-btn small" :disabled="currentWeek >= totalWeeks" @click="nextWeek()">
              <el-icon :size="12"><ArrowRight /></el-icon>
            </button>
          </div>
        </div>
        <div class="filter-section">
          <label class="filter-label">周次筛选</label>
          <div class="week-btns">
            <button v-for="w in weekOptions" :key="w.value" class="week-btn" :class="{ active: filters.weekRange === w.value }" @click="filters.weekRange = w.value; onWeekFilterChange(w.value)">{{ w.label }}</button>
          </div>
        </div>
        <el-collapse v-model="activeCollapse" class="more-filters">
          <el-collapse-item title="更多筛选" name="more">
            <div class="filter-group">
              <label class="filter-label">授课教师</label>
              <el-input v-model="filters.teacher" placeholder="输入教师姓名" size="default" clearable @change="onFilterChange" />
            </div>
            <div class="filter-group">
              <label class="filter-label">课程类型</label>
              <el-select v-model="filters.courseType" placeholder="全部类型" size="default" style="width:100%" clearable @change="onFilterChange">
                <el-option label="全部类型" value="" />
                <el-option label="必修课" value="required" />
                <el-option label="选修课" value="elective" />
              </el-select>
            </div>
            <div class="filter-group">
              <label class="filter-label">上课地点</label>
              <el-input v-model="filters.location" placeholder="输入地点关键词" size="default" clearable @change="onFilterChange" />
            </div>
            <el-button text size="small" style="color:#9ca3af;padding:0" @click="resetMoreFilters"><el-icon><Refresh /></el-icon> 重置筛选</el-button>
          </el-collapse-item>
        </el-collapse>
      </div>
    </template>

    <template #default>
      <div class="schedule-page">
        <!-- 顶部 -->
        <div class="page-header">
          <h1 class="page-title">智能课程助手课表管理</h1>
          <div class="header-actions">
            <el-dropdown trigger="click" @command="handleImportCmd">
            <button class="btn-import">
              <el-icon :size="15"><Upload /></el-icon> 导入课表
              <el-icon :size="12" style="margin-left:2px"><ArrowDown /></el-icon>
            </button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="file"><el-icon><Document /></el-icon> 上传文件</el-dropdown-item>
                <el-dropdown-item command="manual"><el-icon><EditPen /></el-icon> 手动添加</el-dropdown-item>
                <el-dropdown-item command="auto" divided><el-icon><Monitor /></el-icon> 自动导入</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
            <div class="view-tabs">
              <button class="tab-btn" :class="{ active: activeTab === 'week' }" @click="activeTab = 'week'">周视图</button>
              <button class="tab-btn" :class="{ active: activeTab === 'month' }" @click="activeTab = 'month'">月视图</button>
            </div>
          </div>
        </div>
        <input ref="fileInput" id="schedule-file-input" type="file" accept=".csv,.txt,.pdf,.docx,.doc" style="display:none" @change="handleUpload" />
        <div v-if="uploading" class="upload-bar">
          <el-progress :percentage="uploadProgress" />
          <span class="upload-text">{{ uploadMsg }}</span>
        </div>

        <!-- 空状态 -->
        <div v-if="courses.length === 0 && !loading" class="empty-state">
          <el-icon :size="56" color="#d3e4fe"><Calendar /></el-icon>
          <h3>还没有导入课表</h3>
          <p>上传 CSV / TXT 课表文件开始使用</p>
          <label class="btn-upload-empty" for="schedule-file-input">
            <el-icon :size="16"><Upload /></el-icon> 上传课表文件
          </label>
          <p class="empty-hint">支持 CSV / TXT / PDF / Word，格式：课程名称,教师,星期,开始时间,结束时间,地点,周次</p>
        </div>

        <!-- 周视图 -->
        <div v-if="activeTab === 'week' && courses.length > 0" class="week-view">
          <div class="week-nav">
            <button class="week-nav-btn" :disabled="currentWeek <= 1" @click="prevWeek()">
              <el-icon><ArrowLeft /></el-icon>
            </button>
            <span class="week-nav-label">{{ weekLabel }}</span>
            <button class="week-nav-btn" :disabled="currentWeek >= totalWeeks" @click="nextWeek()">
              <el-icon><ArrowRight /></el-icon>
            </button>
          </div>
          <div class="week-calendar">
            <div class="week-header">
              <div class="time-gutter"></div>
              <div v-for="(d, i) in weekDays" :key="i" class="day-header" :class="{ today: d.isToday }">
                <span class="day-name">{{ d.name }}</span>
                <span class="day-date" :class="{ 'today-badge': d.isToday }">{{ d.month }}/{{ d.date }}</span>
              </div>
            </div>
            <div class="week-body">
              <div class="time-axis">
                <div v-for="h in timeSlots" :key="h" class="time-slot">{{ h }}</div>
              </div>
              <div class="day-columns">
                <div v-for="(d, di) in weekDays" :key="di" class="day-col" :class="{ today: d.isToday }">
                  <div v-for="course in getDayCourses(di)" :key="course.id" class="week-course-card" :style="getCourseStyle(course)" @click="selectCourse(course)">
                    <div class="course-bar" :style="{ background: courseColor(course) }"></div>
                    <div class="course-content">
                      <span class="course-title">{{ course.course_name }}</span>
                      <span class="course-meta">{{ course.start_time }} - {{ course.end_time }}</span>
                      <span class="course-meta">{{ course.location }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 月视图 -->
        <div v-if="activeTab === 'month' && courses.length > 0" class="month-view">
          <div class="month-header">
            <button class="month-nav" @click="prevMonth"><el-icon><ArrowLeft /></el-icon></button>
            <span class="month-title">{{ currentYear }}年 {{ currentMonth + 1 }}月</span>
            <button class="month-nav" @click="nextMonth"><el-icon><ArrowRight /></el-icon></button>
          </div>
          <div class="month-grid">
            <div class="month-weekdays"><span v-for="d in monthWeekdays" :key="d">{{ d }}</span></div>
            <div class="month-days">
              <div v-for="(day, idx) in monthDays" :key="idx" class="month-day" :class="{ 'other-month': !day.isCurrentMonth, today: day.isToday }" @click="selectMonthDay(day)">
                <span class="day-num">{{ day.dayOfMonth }}</span>
                <div class="day-dots">
                  <span v-for="(ev, ei) in day.events.slice(0,3)" :key="ei" class="day-dot" :style="{ background: ev.color }"></span>
                  <span v-if="day.events.length > 3" class="day-more">+{{ day.events.length - 3 }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 课程详情卡 -->
        <div class="course-side-panel" v-if="selectedCourse">
          <div class="course-detail-card">
            <div class="card-bar" :style="{ background: courseColor(selectedCourse) }"></div>
            <div class="card-body">
              <div class="card-head">
                <h3 class="card-title">{{ selectedCourse.course_name }}</h3>
                <el-tag :type="selectedCourse.status === 'active' ? 'primary' : 'info'" size="small" effect="plain">{{ statusText(selectedCourse.status) }}</el-tag>
              </div>
              <div class="card-info">
                <div class="info-row"><el-icon :size="15" color="#2981fd"><User /></el-icon><span class="info-label">授课教师</span><span class="info-value">{{ selectedCourse.teacher }}</span></div>
                <div class="info-row"><el-icon :size="15" color="#2981fd"><Clock /></el-icon><span class="info-label">上课时间</span><span class="info-value">{{ weekDayName(selectedCourse.weekday) }} {{ selectedCourse.start_time }}-{{ selectedCourse.end_time }}</span></div>
                <div class="info-row"><el-icon :size="15" color="#2981fd"><LocationFilled /></el-icon><span class="info-label">上课地点</span><span class="info-value">{{ selectedCourse.location }}</span></div>
                <div class="info-row"><el-icon :size="15" color="#2981fd"><Collection /></el-icon><span class="info-label">教学周次</span><span class="info-value">第{{ selectedCourse.week_range }}周</span></div>
              </div>
              <div class="card-actions">
                <button class="btn-primary-fill" @click="handleExport"><el-icon :size="15"><Download /></el-icon> 导出课表</button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 月视图日期弹窗 -->
      <el-dialog v-model="dayDialogVisible" :title="dayDialogTitle" width="420px" destroy-on-close>
        <div v-if="dayDialogCourses.length === 0" class="day-empty">
          <el-icon :size="32" color="#d3e4fe"><Calendar /></el-icon>
          <p>当天无课</p>
        </div>
        <div v-for="c in dayDialogCourses" :key="c.id" class="day-course-item" @click="selectCourse(c); dayDialogVisible = false">
          <div class="day-course-bar" :style="{ background: courseColor(c) }"></div>
          <div class="day-course-body">
            <strong>{{ c.course_name }}</strong>
            <span>{{ c.start_time }} - {{ c.end_time }} | {{ c.location }}</span>
            <span class="text-caption">{{ c.teacher }}</span>
          </div>
        </div>
      </el-dialog>
    
      
      <!-- 自动导入设置弹窗 -->
      <el-dialog v-model="autoDialogVisible" title="自动导入课表" width="440px" destroy-on-close>
        <el-form :model="autoForm" label-width="100px">
          <el-form-item label="教务系统网址" required><el-input v-model="autoForm.url" placeholder="https://jwxt.example.edu.cn" /></el-form-item>
          <el-form-item label="账号" required><el-input v-model="autoForm.username" placeholder="学号" /></el-form-item>
          <el-form-item label="密码" required><el-input v-model="autoForm.password" type="password" placeholder="教务系统密码" show-password /></el-form-item>
          <el-alert type="info" :closable="false" show-icon style="margin-top:8px">
            <template #title>使用说明</template>
            输入教务系统登录信息后，系统将自动抓取课表数据并导入。密码仅用于本次抓取，不会存储。
          </el-alert>
        </el-form>
        <template #footer>
          <el-button @click="autoDialogVisible = false">取消</el-button>
          <el-button type="primary" :loading="autoLoading" @click="doAutoImport">开始导入</el-button>
        </template>
      </el-dialog>
      <!-- 手动添加课程弹窗 -->
      <el-dialog v-model="addDialogVisible" title="添加课程" width="480px" destroy-on-close>
        <el-form :model="addForm" label-width="80px" @keyup.enter="saveCourse">
          <el-form-item label="课程名称" required><el-input v-model="addForm.course_name" placeholder="如：高等数学" /></el-form-item>
          <el-form-item label="授课教师"><el-input v-model="addForm.teacher" placeholder="如：王教授" /></el-form-item>
          <el-row :gutter="12">
            <el-col :span="12">
              <el-form-item label="星期" required>
                <el-select v-model="addForm.weekday" style="width:100%">
                  <el-option v-for="(n,i) in ['周一','周二','周三','周四','周五','周六','周日']" :key="i" :label="n" :value="i" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="地点"><el-input v-model="addForm.location" placeholder="教学楼A101" /></el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="12">
            <el-col :span="12">
              <el-form-item label="开始时间" required><el-time-picker v-model="addForm.start_time" format="HH:mm" value-format="HH:mm" placeholder="08:00" style="width:100%" /></el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="结束时间" required><el-time-picker v-model="addForm.end_time" format="HH:mm" value-format="HH:mm" placeholder="09:30" style="width:100%" /></el-form-item>
            </el-col>
          </el-row>
          <el-form-item label="教学周次"><el-input v-model="addForm.week_range" placeholder="1-16" /></el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="addDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="saveCourse">添加</el-button>
        </template>
      </el-dialog>
  </template>
  </Layout>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, Refresh, ArrowLeft, ArrowRight, ArrowDown, Document, EditPen, Monitor, View, Download, User, Clock, LocationFilled, Collection, Upload, Calendar } from '@element-plus/icons-vue'
import Layout from '@/layouts/Layout.vue'
import { useAppStore } from '@/stores/app'
import request from '@/utils/request'

interface Course {
  id: number; course_id: string; course_name: string;
  teacher: string; weekday: number; start_time: string; end_time: string;
  location: string; week_range: string; status: string; progress?: number;
}

const appStore = useAppStore()
const activeTab = ref<'week' | 'month'>('week')
const activeCollapse = ref<string[]>([])
const filters = reactive({ semester: appStore.semester, weekRange: '', teacher: '', courseType: '', location: '', status: '' })
const weekOptions = [{ label: '全部', value: '' },{ label: '1-8周', value: '1-8' },{ label: '9-16周', value: '9-16' },{ label: '本周', value: 'this' }]

// Week filter handler: "本周" filters courses for currently displayed week
function onWeekFilterChange(_val: string) {
  onFilterChange()
}

const courses = ref<Course[]>([])
const selectedCourse = ref<Course | null>(null)
const loading = ref(false)

// Upload state
const fileInput = ref<HTMLInputElement>()
const uploading = ref(false)
const uploadProgress = ref(0)
const uploadMsg = ref('')

// Day dialog
const dayDialogVisible = ref(false)
const dayDialogTitle = ref('')
const dayDialogCourses = ref<Course[]>([])
const autoDialogVisible = ref(false)
const autoLoading = ref(false)
const autoForm = reactive({ url: '', username: '', password: '' })
const addDialogVisible = ref(false)
const addForm = reactive({ course_name: '', teacher: '', weekday: 0, start_time: '08:00', end_time: '09:30', location: '', week_range: '1-16' })

const now = new Date()
const semesterStart = new Date(2025, 1, 17)  // 2025-02-17 学期开始
const totalWeeks = 20
const currentWeek = ref(1)  // 默认第1周，用户可切换

const weekLabel = computed(() => {
  const weekStart = new Date(semesterStart)
  weekStart.setDate(weekStart.getDate() + (currentWeek.value - 1) * 7)
  const weekEnd = new Date(weekStart)
  weekEnd.setDate(weekEnd.getDate() + 6)
  const fmt = (d: Date) => `${d.getMonth()+1}月${d.getDate()}日`
  return `第${currentWeek.value}周 (${fmt(weekStart)} - ${fmt(weekEnd)})`
})

function prevWeek() { if (currentWeek.value > 1) currentWeek.value-- }
function nextWeek() { if (currentWeek.value < totalWeeks) currentWeek.value++ }
const weekDays = computed(() => {
  const start = new Date(semesterStart)
  start.setDate(start.getDate() + (currentWeek.value - 1) * 7)
  // Adjust to Monday of that week
  const dayOfWeek = start.getDay()
  start.setDate(start.getDate() - (dayOfWeek === 0 ? 6 : dayOfWeek - 1))
  return Array.from({ length: 7 }, (_, i) => {
    const d = new Date(start); d.setDate(d.getDate() + i)
    return { name: ['周一','周二','周三','周四','周五','周六','周日'][i], date: d.getDate(), month: d.getMonth()+1, isToday: d.toDateString() === now.toDateString() }
  })
})

const timeSlots = ['08:00','09:00','10:00','11:00','12:00','13:00','14:00','15:00','16:00','17:00','18:00','19:00','20:00']

const filteredCourses = computed(() => {
  let list = courses.value
  if (filters.teacher) list = list.filter(c => c.teacher.includes(filters.teacher))
  if (filters.location) list = list.filter(c => c.location.includes(filters.location))
  if (filters.weekRange === 'this') {
    const w = currentWeek.value
    list = list.filter(c => { const [a,b] = (c.week_range||'1-16').split('-').map(Number); return w >= a && w <= (b||a) })
  }
  return list
})

function getDayCourses(dayIndex: number) { return filteredCourses.value.filter(c => c.weekday === dayIndex) }

function getCourseStyle(course: Course) {
  const [sh, sm] = (course.start_time || '08:00').split(':').map(Number)
  const [eh, em] = (course.end_time || '09:00').split(':').map(Number)
  const top = ((sh - 8) * 60 + sm) / 60 * 52 + 4
  const height = Math.max(((eh * 60 + em) - (sh * 60 + sm)) / 60 * 52, 40)
  return { top: `${top}px`, height: `${height}px` }
}

function courseColor(c: Course): string {
  const colors = ['#2981fd','#67c23a','#e6a23c','#7b5ce7','#f56c6c','#409eff']
  return colors[c.id % colors.length]
}

function weekDayName(d: number) { return ['周一','周二','周三','周四','周五','周六','周日'][d] }
const statusText = (s: string) => ({ active:'进行中', cancelled:'已取消', finished:'已结课' }[s] || s)

// Month view
const currentYear = ref(now.getFullYear())
const currentMonth = ref(now.getMonth())
const monthWeekdays = ['日','一','二','三','四','五','六']

const weekStart = computed(() => { const d = new Date(now); d.setDate(d.getDate()-d.getDay()+1); return d })

const monthDays = computed(() => {
  const y = currentYear.value; const m = currentMonth.value
  const firstDay = new Date(y, m, 1); const lastDay = new Date(y, m+1, 0)
  const startDow = firstDay.getDay(); const daysInMonth = lastDay.getDate()
  const days: any[] = []
  for (let i = startDow - 1; i >= 0; i--) days.push({ dayOfMonth: new Date(y,m-1,new Date(y,m,0).getDate()-i).getDate(), isCurrentMonth: false, isToday: false, events: [] })
  for (let i = 1; i <= daysInMonth; i++) {
    const d = new Date(y, m, i); const ds = `${y}-${String(m+1).padStart(2,'0')}-${String(i).padStart(2,'0')}`
    const evs = filteredCourses.value.filter(c => {
      const cd = new Date(weekStart.value); cd.setDate(cd.getDate()+c.weekday)
      return `${cd.getFullYear()}-${String(cd.getMonth()+1).padStart(2,'0')}-${String(cd.getDate()).padStart(2,'0')}` === ds
    }).map(c => ({ color: courseColor(c), title: c.course_name }))
    days.push({ dayOfMonth: i, isCurrentMonth: true, isToday: d.toDateString()===now.toDateString(), events: evs })
  }
  while (days.length < 42) days.push({ dayOfMonth: days.length-daysInMonth-startDow+1, isCurrentMonth: false, isToday: false, events: [] })
  return days
})

function prevMonth() { if (currentMonth.value===0) { currentYear.value--; currentMonth.value=11 } else currentMonth.value-- }
function nextMonth() { if (currentMonth.value===11) { currentYear.value++; currentMonth.value=0 } else currentMonth.value++ }

function selectCourse(c: Course) { selectedCourse.value = c }

function selectMonthDay(day: any) {
  if (!day.isCurrentMonth) return
  const d = new Date(currentYear.value, currentMonth.value, day.dayOfMonth)
  dayDialogTitle.value = `${d.getMonth()+1}月${d.getDate()}日 课程`
  dayDialogCourses.value = filteredCourses.value.filter(c => {
    const cd = new Date(weekStart.value); cd.setDate(cd.getDate()+c.weekday)
    const ds = `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`
    return `${cd.getFullYear()}-${String(cd.getMonth()+1).padStart(2,'0')}-${String(cd.getDate()).padStart(2,'0')}` === ds
  })
  dayDialogVisible.value = true
}

async function onFilterChange() { fetchCourses() }
function onWeekChange() { fetchCourses() }

function resetMoreFilters() { filters.teacher=''; filters.courseType=''; filters.location=''; filters.status=''; onFilterChange() }

// legacy: kept for file input change event
async function handleUpload(e: Event) {
  const input = e.target as HTMLInputElement
  if (!input.files?.length) return
  uploading.value = true; uploadProgress.value = 0; uploadMsg.value = '正在解析课表...'
  const fd = new FormData(); fd.append('file', input.files[0])
  try {
    const res: any = await request.post('/schedule/upload_file/', fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 120000,
    })
    uploadProgress.value = 100
    if (res.code === 0) {
      const created = res.data?.created || 0
      if (created > 0) {
        ElMessage.success(`成功导入 ${created} 条课程`)
        uploadMsg.value = `已导入 ${created} 条课程`
      } else {
        const errs = res.data?.errors || []
        const detail = errs.length > 0 ? errs.map((e: any) => `第${e.line}行: ${e.error}`).join('; ') : ''
        ElMessage.warning(res.msg + (detail ? ' — ' + detail : ''))
        uploadMsg.value = '未能识别课程数据，请检查文件格式'
      }
    } else {
      ElMessage.error(res.msg || '导入失败')
      uploadMsg.value = '导入失败'
    }
  } catch { ElMessage.error('上传失败，请重试') }
  uploading.value = false; input.value = ''; fetchCourses()
}

function handleImportCmd(cmd: string) {
  if (cmd === 'file') {
    fileInput.value?.click()
  } else if (cmd === 'manual') {
    openAddDialog()
  } else if (cmd === 'auto') {
    autoDialogVisible.value = true
  }
}

async function doAutoImport() {
  if (!autoForm.url || !autoForm.username || !autoForm.password) {
    ElMessage.warning('请填写教务系统网址、账号和密码')
    return
  }
  autoLoading.value = true
  try {
    const res: any = await request.post('/schedule/auto_import/', autoForm, { timeout: 60000 })
    if (res.code === 0) {
      ElMessage.success(res.msg || '自动导入成功')
      autoDialogVisible.value = false
      fetchCourses()
    } else {
      ElMessage.error(res.msg || '自动导入失败')
    }
  } catch { ElMessage.error('自动导入失败，请检查网址和账号密码') }
  autoLoading.value = false
}

function openAddDialog() { Object.assign(addForm, { course_name: '', teacher: '', weekday: 0, start_time: '08:00', end_time: '09:30', location: '', week_range: '1-16' }); addDialogVisible.value = true }
async function saveCourse() {
  if (!addForm.course_name) { ElMessage.warning('请输入课程名称'); return }
  try {
    const res: any = await request.post('/schedule/', addForm)
    if (res.code === 0 || res.id) { ElMessage.success('添加成功'); addDialogVisible.value = false; fetchCourses() }
    else { ElMessage.error(res.msg || '添加失败') }
  } catch { ElMessage.error('添加失败') }
}

function handleExport() { ElMessage.success('课表导出功能已触发'); request.get('/schedule/export/',{params:{format:'csv'}}).catch(()=>{}) }

async function fetchCourses() {
  loading.value = true
  try {
    const res: any = await request.get('/schedule/', { params: { semester: filters.semester } })
    const raw = res.data?.results || res.data || []
    courses.value = raw.map((c: any) => ({ ...c, progress: c.progress || Math.floor(Math.random()*80+20) }))
  } catch { /* */ }
  finally { loading.value = false }
}

watch(() => filters.semester, (val) => appStore.setSemester(val))
// When currentWeek changes, re-filter if "本周" is active
watch(currentWeek, () => {
  if (filters.weekRange === 'this') onFilterChange()
  else fetchCourses()
})
onMounted(() => { fetchCourses() })
</script>

<style scoped>
.schedule-page { height: 100%; display: flex; flex-direction: column; }
.page-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.page-title { font-size: 20px; font-weight: 700; color: #1f2937; margin: 0; }
.header-actions { display: flex; align-items: center; gap: 12px; }

.btn-import { display: inline-flex; align-items: center; gap: 4px; padding: 8px 18px; border: none; border-radius: 8px; background: #2981fd; color: #fff; font-size: 13px; font-weight: 500; cursor: pointer; transition: all .15s; }
.btn-import:hover { background: #1a6fd6; }
.btn-add-manual { display: inline-flex; align-items: center; gap: 4px; padding: 7px 14px; border: 1px solid #2981fd; border-radius: 8px; background: #fff; color: #2981fd; font-size: 13px; cursor: pointer; transition: all .15s; }
.btn-add-manual:hover { background: #e8f1fe; }

.btn-upload {
  display: inline-flex; align-items: center; gap: 6px; padding: 7px 16px;
  border: 1px dashed #2981fd; border-radius: 8px; background: #e8f1fe;
  color: #2981fd; font-size: 13px; font-weight: 500; cursor: pointer; transition: all .15s;
}
.btn-add-manual {
  display: inline-flex; align-items: center; gap: 4px; padding: 7px 14px;
  border: 1px solid #2981fd; border-radius: 8px; background: #fff;
  color: #2981fd; font-size: 13px; cursor: pointer; transition: all .15s;
}
.btn-add-manual:hover { background: #e8f1fe; }

.btn-upload:hover { background: #d3e4fe; border-style: solid; }

.upload-bar { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; }
.upload-text { font-size: 12px; color: #9ca3af; }

.empty-state { text-align: center; padding: 80px 0; display: flex; flex-direction: column; align-items: center; gap: 12px; color: #9ca3af; }
.empty-state h3 { font-size: 18px; color: #6b7280; margin: 0; }
.empty-state p { margin: 0; }
.empty-hint { font-size: 12px; margin-top: 8px; }
.btn-upload-empty { display: inline-flex; align-items: center; gap: 6px; padding: 10px 24px; border: none; border-radius: 8px; background: #2981fd; color: #fff; font-size: 14px; font-weight: 500; cursor: pointer; transition: all .15s; margin-top: 8px; }
.btn-upload-empty:hover { background: #1a6fd6; }

.view-tabs { display: flex; border-radius: 8px; overflow: hidden; border: 1px solid #e5e7eb; }
.tab-btn { padding: 7px 18px; border: none; background: #fff; font-size: 13px; color: #4b5563; cursor: pointer; transition: all .15s; }
.tab-btn.active { background: #2981fd; color: #fff; }
.tab-btn:hover:not(.active) { background: #e8f1fe; color: #2981fd; }

/* Filter panel */
.filter-panel { padding: 4px 0; }
.filter-section { margin-bottom: 16px; }
.filter-label { display: block; font-size: 12px; color: #9ca3af; margin-bottom: 6px; }
.filter-group { margin-bottom: 12px; }
.week-btns { display: flex; gap: 4px; flex-wrap: wrap; }
.week-btn { padding: 4px 10px; border: 1px solid #e5e7eb; border-radius: 6px; background: #fff; font-size: 12px; color: #4b5563; cursor: pointer; transition: all .15s; }
.week-btn.active { background: #2981fd; color: #fff; border-color: #2981fd; }
.week-btn:hover:not(.active) { background: #e8f1fe; }
.more-filters { border: none; }

/* Week view */
.week-nav { display: flex; align-items: center; justify-content: center; gap: 16px; margin-bottom: 12px; }
.week-nav-btn {
  width: 32px; height: 32px; border: 1px solid #e5e7eb; border-radius: 6px;
  background: #fff; cursor: pointer; display: flex; align-items: center; justify-content: center;
  color: #4b5563; transition: all .15s;
}
.week-nav-btn:hover:not(:disabled) { border-color: #2981fd; color: #2981fd; background: #e8f1fe; }
.week-nav-btn:disabled { opacity: 0.35; cursor: not-allowed; }
.week-nav-label { font-size: 14px; font-weight: 600; color: #1f2937; min-width: 220px; text-align: center; }

.week-calendar { border: 1px solid #f3f4f6; border-radius: 8px; overflow: hidden; }
.week-header { display: flex; background: #fafbfc; border-bottom: 1px solid #f3f4f6; }
.time-gutter { width: 56px; flex-shrink: 0; }
.day-header { flex: 1; text-align: center; padding: 10px 4px; }
.day-header.today { background: #e8f1fe; }
.day-name { font-size: 12px; color: #9ca3af; }
.day-date { font-size: 14px; color: #1f2937; font-weight: 600; }
.today-badge { background: #2981fd; color: #fff; width: 28px; height: 28px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; margin: 2px auto 0; }
.week-body { display: flex; }
.time-axis { width: 56px; flex-shrink: 0; }
.time-slot { height: 52px; font-size: 11px; color: #9ca3af; text-align: right; padding-right: 8px; border-top: 1px solid #f9fafb; }
.day-columns { flex: 1; display: flex; }
.day-col { flex: 1; position: relative; border-left: 1px solid #f3f4f6; min-height: 700px; padding: 4px 3px; }
.day-col.today { background: #fafcff; }
.week-course-card { position: absolute; left: 3px; right: 3px; border-radius: 6px; background: #fff; border: 1px solid #e5e7eb; overflow: hidden; cursor: pointer; transition: all .15s; display: flex; }
.week-course-card:hover { border-color: #2981fd; }
.course-bar { width: 3px; flex-shrink: 0; }
.course-content { padding: 4px 8px; overflow: hidden; }
.course-title { display: block; font-size: 12px; font-weight: 600; color: #1f2937; }
.course-meta { display: block; font-size: 10px; color: #9ca3af; }

/* Month view */
.month-header { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; }
.month-title { font-size: 15px; font-weight: 600; color: #1f2937; min-width: 120px; text-align: center; }
.month-nav { width: 30px; height: 30px; border: 1px solid #e5e7eb; border-radius: 6px; background: #fff; cursor: pointer; display: flex; align-items: center; justify-content: center; color: #4b5563; transition: all .15s; }
.month-nav:hover { border-color: #2981fd; color: #2981fd; background: #e8f1fe; }
.month-grid { border: 1px solid #f3f4f6; border-radius: 8px; overflow: hidden; }
.month-weekdays { display: grid; grid-template-columns: repeat(7, 1fr); background: #fafbfc; border-bottom: 1px solid #f3f4f6; }
.month-weekdays span { text-align: center; padding: 8px 0; font-size: 12px; color: #9ca3af; }
.month-days { display: grid; grid-template-columns: repeat(7, 1fr); }
.month-day { aspect-ratio: 1; padding: 6px; border-right: 1px solid #f9fafb; border-bottom: 1px solid #f9fafb; cursor: pointer; transition: all .15s; display: flex; flex-direction: column; align-items: center; }
.month-day:hover { background: #f0f7ff; }
.month-day.other-month { opacity: 0.25; }
.month-day.today .day-num { background: #2981fd; color: #fff; }
.day-num { width: 26px; height: 26px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 13px; font-weight: 500; color: #1f2937; }
.day-dots { display: flex; gap: 2px; margin-top: 4px; }
.day-dot { width: 5px; height: 5px; border-radius: 50%; }
.day-more { font-size: 10px; color: #9ca3af; }

/* Course detail */
.course-side-panel { margin-top: 16px; }
.course-detail-card { background: #fff; border: 1px solid #f3f4f6; border-radius: 10px; overflow: hidden; max-width: 520px; }
.card-bar { height: 4px; }
.card-body { padding: 20px; }
.card-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.card-title { font-size: 16px; font-weight: 600; color: #1f2937; margin: 0; }
.card-info { margin-bottom: 16px; }
.info-row { display: flex; align-items: center; gap: 8px; padding: 6px 0; border-bottom: 1px solid #f9fafb; }
.info-label { font-size: 13px; color: #9ca3af; min-width: 64px; }
.info-value { font-size: 13px; color: #4b5563; font-weight: 500; }
.card-actions { display: flex; gap: 10px; }
.btn-primary-fill { flex: 1; display: flex; align-items: center; justify-content: center; gap: 6px; padding: 9px 16px; border: none; border-radius: 8px; background: #2981fd; color: #fff; font-size: 13px; font-weight: 500; cursor: pointer; transition: all .15s; }
.btn-primary-fill:hover { background: #1a6fd6; }

/* Day dialog */
.day-empty { text-align: center; padding: 32px 0; color: #9ca3af; }
.day-course-item { display: flex; gap: 10px; padding: 12px; border-radius: 8px; border: 1px solid #f3f4f6; margin-bottom: 8px; cursor: pointer; transition: all .15s; }
.day-course-item:hover { background: #f0f7ff; border-color: #2981fd; }
.day-course-bar { width: 4px; border-radius: 2px; flex-shrink: 0; }
.day-course-body { display: flex; flex-direction: column; gap: 4px; }
.day-course-body strong { font-size: 14px; color: #1f2937; }
.day-course-body span { font-size: 12px; color: #9ca3af; }
.text-caption { font-size: 11px; color: #9ca3af; }
.week-nav-btn.small { width: 28px; height: 28px; }
</style>