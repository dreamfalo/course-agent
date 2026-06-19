<template>
  <div class="course-card card-base" :class="{ 'card-selected': selected }" @click="$emit('click')">
    <div class="course-header">
      <h4 class="course-name">{{ course.course_name }}</h4>
      <el-tag :type="statusType" size="small" effect="plain">{{ statusText }}</el-tag>
    </div>
    <div class="course-info">
      <div class="info-item">
        <el-icon :size="14"><User /></el-icon>
        <span>{{ course.teacher }}</span>
      </div>
      <div class="info-item">
        <el-icon :size="14"><Clock /></el-icon>
        <span>{{ course.start_time }} - {{ course.end_time }}</span>
      </div>
      <div class="info-item">
        <el-icon :size="14"><LocationFilled /></el-icon>
        <span>{{ course.location }}</span>
      </div>
    </div>
    <div class="course-footer">
      <span class="course-weekday">{{ weekdayText }}</span>
      <span class="course-weeks">第{{ course.week_range }}周</span>
    </div>
    <div class="course-actions" v-if="$slots.actions">
      <slot name="actions" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { User, Clock, LocationFilled } from '@element-plus/icons-vue'

interface Course {
  id?: number
  course_id?: string
  course_name: string
  teacher: string
  weekday: number
  start_time: string
  end_time: string
  location: string
  week_range?: string
  status?: string
}

const props = defineProps<{
  course: Course
  selected?: boolean
}>()

defineEmits(['click'])

const weekdayMap = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']

const weekdayText = computed(() => weekdayMap[props.course.weekday] || '')

const statusText = computed(() => {
  const map: Record<string, string> = { active: '进行中', cancelled: '已取消', finished: '已结课' }
  return map[props.course.status || 'active'] || '进行中'
})

const statusType = computed(() => {
  const map: Record<string, string> = { active: 'primary', cancelled: 'info', finished: 'success' }
  return map[props.course.status || 'active'] || 'primary'
})
</script>

<style scoped>
.course-card {
  cursor: pointer;
  padding: 16px;
  position: relative;
}

.course-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.course-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.course-info {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 12px;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--color-text-regular);
}

.info-item .el-icon {
  color: var(--color-primary);
}

.course-footer {
  display: flex;
  align-items: center;
  gap: 8px;
}

.course-weekday {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 4px;
  background: var(--color-bg-selected);
  color: var(--color-primary);
  font-weight: 500;
}

.course-weeks {
  font-size: 12px;
  color: var(--color-text-secondary);
}

.course-actions {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--color-border-light);
}
</style>
