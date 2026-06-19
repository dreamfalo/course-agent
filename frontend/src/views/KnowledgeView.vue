<template>
  <Layout>
    <template #sidebar>
      <div class="filter-panel">
        <h4 class="panel-title">文档筛选</h4>

        <div class="filter-group">
          <label class="filter-label">学期</label>
          <el-select v-model="appStore.semester" size="default" style="width:100%" @change="fetchFiles">
            <el-option v-for="s in appStore.semesterOptions" :key="s.value" :label="s.label" :value="s.value" />
          </el-select>
        </div>

        <div class="filter-group">
          <label class="filter-label">课程</label>
          <el-select v-model="filters.courseId" placeholder="全部课程" clearable size="default" style="width:100%" @change="fetchFiles">
            <el-option :value="undefined" label="全部课程" />
            <el-option v-for="c in courseList" :key="c.course_id" :label="c.course_name" :value="c.course_id" />
          </el-select>
        </div>

        <div class="filter-group">
          <label class="filter-label">文件格式</label>
          <div class="checkbox-group">
            <el-checkbox v-for="t in fileTypes" :key="t.value" v-model="t.checked" size="small" @change="applyTypeFilter">{{ t.label }}</el-checkbox>
          </div>
        </div>

        <div class="filter-group">
          <label class="filter-label">状态</label>
          <el-select v-model="filters.status" placeholder="全部" clearable size="default" style="width:100%">
            <el-option :value="undefined" label="全部" />
            <el-option value="uploaded" label="已上传" />
            <el-option value="vectorized" label="已向量化" />
          </el-select>
        </div>

        <el-divider style="margin:12px 0" />

        <button class="reset-btn" @click="resetFilters">
          <el-icon><Refresh /></el-icon> 重置筛选
        </button>

        <div class="stats-row">
          <div class="stat-item"><span class="stat-num">{{ files.length }}</span><span class="stat-label">总文档</span></div>
          <div class="stat-item"><span class="stat-num">{{ vectorizedCount }}</span><span class="stat-label">已向量化</span></div>
        </div>
      </div>
    </template>

    <template #default>
      <div class="knowledge-page">
        <div class="page-header">
          <h1 class="page-title">知识库管理</h1>
          <div class="header-actions">
            <input ref="fileInput" type="file" multiple accept=".pdf,.docx,.doc,.txt,.md" style="display:none" @change="handleFilesSelected" />
            <button class="btn-primary-fill" @click="triggerUpload">
              <el-icon><Upload /></el-icon> 上传课件
            </button>
            <button class="btn-outline" :disabled="selectedIds.length === 0" @click="batchDelete">
              <el-icon><Delete /></el-icon> 批量删除
            </button>
          </div>
        </div>

        <!-- 检索 -->
        <div class="search-bar">
          <el-input v-model="searchQuery" placeholder="搜索知识库内容..." :prefix-icon="Search" clearable @keyup.enter="doSearch" style="max-width:420px">
            <template #append><el-button @click="doSearch" :loading="searching">检索</el-button></template>
          </el-input>
        </div>

        <!-- 检索结果 -->
        <div v-if="searchResults.length > 0" class="search-results">
          <div class="results-header">
            <span class="results-title">检索结果 ({{ searchResults.length }})</span>
            <el-button link size="small" @click="searchResults = []">清除</el-button>
          </div>
          <div v-for="(r, i) in searchResults" :key="i" class="result-item">
            <p class="result-content">{{ r.content }}</p>
            <span class="result-meta">{{ r.metadata?.source }} · 相似度 {{ r.score?.toFixed(3) || 'N/A' }}</span>
          </div>
        </div>

        <!-- 上传进度 -->
        <div v-if="uploading" class="upload-bar">
          <el-progress :percentage="uploadProgress" :status="uploadProgress === 100 ? 'success' : undefined" />
          <span class="upload-text">正在上传并向量化文件...</span>
        </div>

        <!-- 空状态 -->
        <div v-if="filteredFiles.length === 0 && !uploading" class="empty-state">
          <el-icon :size="48" color="#d3e4fe"><FolderOpened /></el-icon>
          <p>暂无文档，上传课件开始使用</p>
          <button class="btn-primary-fill" @click="triggerUpload">
            <el-icon><Upload /></el-icon> 上传课件
          </button>
        </div>

        <!-- 文件网格 -->
        <div v-else class="file-grid">
          <div
            v-for="f in filteredFiles"
            :key="f.id"
            class="file-card"
            :class="{ selected: selectedIds.includes(f.id) }"
            @click="toggleSelect(f.id)"
          >
            <div class="file-icon">
              <el-icon :size="26" :color="iconColor(f.file_type)">
                <Document v-if="f.file_type==='docx'" />
                <Notebook v-else-if="f.file_type==='pdf'" />
                <EditPen v-else />
              </el-icon>
            </div>
            <div class="file-body">
              <span class="file-name">{{ f.file_name }}</span>
              <span class="file-meta">{{ f.file_type?.toUpperCase() }} · {{ formatSize(f.file_size) }} · {{ f.chunks_count }}块</span>
              <span class="file-meta">{{ f.course_name || "未绑定课程" }}</span>
            </div>
            <div class="file-tag">
              <el-tag :type="f.status==='vectorized'?'success':'info'" size="small" effect="plain">{{ f.status==="vectorized"?"已向量化":"已上传" }}</el-tag>
            </div>
            <div class="file-actions">
              <el-button link size="small" type="primary" @click.stop="previewFile(f)">预览</el-button>
              <el-button link size="small" type="danger" @click.stop="deleteSingle(f.id)">删除</el-button>
            </div>
          </div>
        </div>
      </div>
    </template>
  </Layout>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Upload, Delete, Search, FolderOpened, Document, Notebook, EditPen, Refresh } from '@element-plus/icons-vue'
import Layout from '@/layouts/Layout.vue'
import { useAppStore } from '@/stores/app'
import request from '@/utils/request'

interface KnowledgeFile {
  id: number; doc_id: string; file_name: string; file_path: string; file_type: string;
  file_size: number; chunks_count: number; course_name: string; course_id: string; status: string;
}

const appStore = useAppStore()
const files = ref<KnowledgeFile[]>([])
const courseList = ref<{ course_id: string; course_name: string }[]>([])
const selectedIds = ref<number[]>([])
const fileInput = ref<HTMLInputElement>()
const searchQuery = ref('')
const searchResults = ref<any[]>([])
const searching = ref(false)
const uploading = ref(false)
const uploadProgress = ref(0)

const filters = reactive({
  courseId: undefined as string | undefined,
  status: undefined as string | undefined,
  activeTypes: ['pdf', 'docx', 'txt', 'md'] as string[],
})

const fileTypes = reactive([
  { label: 'PDF', value: 'pdf', checked: true },
  { label: 'Word', value: 'docx', checked: true },
  { label: 'TXT', value: 'txt', checked: true },
  { label: 'MD', value: 'md', checked: true },
])

const filteredFiles = computed(() => {
  let list = files.value
  if (filters.courseId) list = list.filter(f => f.course_id === filters.courseId)
  if (filters.status) list = list.filter(f => f.status === filters.status)
  list = list.filter(f => filters.activeTypes.includes(f.file_type))
  return list
})

const vectorizedCount = computed(() => files.value.filter(f => f.status === 'vectorized').length)

function formatSize(b: number): string {
  if (b < 1024) return b + 'B'
  if (b < 1048576) return (b / 1024).toFixed(1) + 'KB'
  return (b / 1048576).toFixed(1) + 'MB'
}

function iconColor(t: string): string {
  return { pdf: '#f56c6c', docx: '#2981fd', txt: '#909399', md: '#67c23a' }[t] || '#909399'
}

function toggleSelect(id: number) {
  const i = selectedIds.value.indexOf(id)
  i >= 0 ? selectedIds.value.splice(i, 1) : selectedIds.value.push(id)
}

function applyTypeFilter() {
  filters.activeTypes = fileTypes.filter(t => t.checked).map(t => t.value)
}

function triggerUpload() { fileInput.value?.click() }

async function handleFilesSelected(e: Event) {
  const input = e.target as HTMLInputElement
  if (!input.files?.length) return
  const courseId = filters.courseId || (courseList.value[0]?.course_id || 'COURSE_0001')
  uploading.value = true; uploadProgress.value = 0
  let ok = 0
  for (let i = 0; i < input.files.length; i++) {
    const fd = new FormData()
    fd.append('file', input.files[i])
    fd.append('course_id', courseId)
    fd.append('course_name', courseList.value.find(c => c.course_id === courseId)?.course_name || '')
    try { await request.post('/knowledge/', fd, {}); ok++ } catch { /* */ }
    uploadProgress.value = Math.round((i + 1) / input.files.length * 100)
  }
  if (ok) ElMessage.success(`成功上传 ${ok} 个文件`)
  uploading.value = false; input.value = ''
  fetchFiles()
}

async function doSearch() {
  if (!searchQuery.value.trim()) return
  searching.value = true
  try {
    const res: any = await request.post('/knowledge/search/', { query: searchQuery.value, top_k: 5 })
    searchResults.value = res.data?.results || []
  } catch { /* */ }
  finally { searching.value = false }
}

async function previewFile(f: KnowledgeFile) {
  try {
    const res: any = await request.get(`/knowledge/${f.id}/preview/`)
    if (res.data?.url) window.open(res.data.url, '_blank')
    else ElMessage.warning('无法获取预览链接')
  } catch { /* */ }
}

async function deleteSingle(id: number) {
  try { await ElMessageBox.confirm('确定删除该文档？', '提示', { type: 'warning' }) } catch { return }
  try { await request.delete(`/knowledge/${id}/`); ElMessage.success('已删除'); fetchFiles() } catch { /* */ }
}

async function batchDelete() {
  try { await ElMessageBox.confirm(`确定删除 ${selectedIds.value.length} 个文档？`, '批量删除', { type: 'warning' }) } catch { return }
  for (const id of selectedIds.value) { try { await request.delete(`/knowledge/${id}/`) } catch { /* */ } }
  ElMessage.success('批量删除完成'); selectedIds.value = []; fetchFiles()
}

function resetFilters() {
  filters.courseId = undefined; filters.status = undefined
  fileTypes.forEach(t => t.checked = true); applyTypeFilter()
  fetchFiles()
}

async function fetchFiles() {
  try {
    const res: any = await request.get('/knowledge/')
    files.value = res.data?.results || res.data || []
  } catch { /* */ }
}

onMounted(async () => {
  fetchFiles()
  try {
    const res: any = await request.get('/schedule/', { params: { semester: appStore.semester } })
    courseList.value = (res.data?.results || res.data || []).map((c: any) => ({
      course_id: c.course_id || String(c.id), course_name: c.course_name,
    }))
  } catch { /* */ }
})
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

.knowledge-page { height: 100%; display: flex; flex-direction: column; }
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
  border: 1px solid #e5e7eb; border-radius: 8px; background: #fff;
  color: #f56c6c; font-size: 13px; font-weight: 500; cursor: pointer; transition: all .15s;
}
.btn-outline:hover { border-color: #f56c6c; background: #fef2f2; }
.btn-outline:disabled { opacity: 0.4; cursor: not-allowed; }

.search-bar { margin-bottom: 12px; }
.search-results { background: #fff; border: 1px solid #f3f4f6; border-radius: 8px; padding: 16px; margin-bottom: 12px; }
.results-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
.results-title { font-size: 13px; font-weight: 600; color: #1f2937; }
.result-item { padding: 8px 0; border-bottom: 1px solid #f9fafb; }
.result-item:last-child { border: none; }
.result-content { font-size: 13px; color: #4b5563; line-height: 1.5; margin: 0 0 4px; }
.result-meta { font-size: 11px; color: #9ca3af; }

.upload-bar { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; }
.upload-text { font-size: 12px; color: #9ca3af; white-space: nowrap; }

.empty-state { text-align: center; padding: 64px 0; display: flex; flex-direction: column; align-items: center; gap: 12px; color: #9ca3af; }

.file-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 12px; }
.file-card {
  display: flex; flex-direction: column; gap: 10px; padding: 16px;
  background: #fff; border: 1px solid #f3f4f6; border-radius: 10px;
  cursor: pointer; transition: all .15s; position: relative;
}
.file-card:hover { border-color: #2981fd; background: #f0f7ff; }
.file-card.selected { border-color: #2981fd; background: #e8f1fe; }
.file-icon { display: flex; justify-content: center; padding: 4px 0; }
.file-body { min-width: 0; }
.file-name { display: block; font-size: 14px; font-weight: 500; color: #1f2937; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.file-meta { display: block; font-size: 11px; color: #9ca3af; margin-top: 2px; }
.file-tag { position: absolute; top: 12px; right: 12px; }
.file-actions { display: flex; gap: 4px; padding-top: 8px; border-top: 1px solid #f3f4f6; }
</style>
