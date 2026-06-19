<template>
  <div class="gantt-container">
    <!-- 图例 -->
    <div class="gantt-legend">
      <span
        v-for="s in uniqueSubjects"
        :key="s"
        class="legend-item"
        :style="{ '--dot-color': subjectColor(s) }"
      >{{ s }}</span>
    </div>

    <!-- 时间轴头部 -->
    <div class="gantt-header">
      <div class="gantt-label-col">任务</div>
      <div class="gantt-timeline-col" ref="timelineRef">
        <div
          v-for="d in dateRange"
          :key="d.getTime()"
          class="gantt-time-slot"
          :class="{ 'is-weekend': isWeekend(d) }"
        >
          <span class="gantt-date">{{ formatShortDate(d) }}</span>
        </div>
      </div>
    </div>

    <!-- 任务行 -->
    <div class="gantt-body">
      <div
        v-for="(task, idx) in displayTasks"
        :key="task.id"
        class="gantt-row"
      >
        <div class="gantt-label-col" :title="task.name">
          <span class="gantt-task-name">{{ task.name }}</span>
        </div>
        <div class="gantt-timeline-col gantt-bar-row">
          <div
            class="gantt-bar"
            :style="getBarStyle(task)"
            :title="`${task.name}: ${task.start} ~ ${task.end} (${task.progress || 0}%)`"
          >
            <div
              class="gantt-bar-progress"
              :style="{ width: (task.progress || 0) + '%', background: subjectColor(task.custom_class || 'default') }"
            />
          </div>
        </div>
      </div>

      <div v-if="displayTasks.length === 0" class="gantt-empty">
        暂无任务数据
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

export interface GanttTask {
  id: string
  name: string
  start: string
  end: string
  progress: number
  custom_class?: string
  dependencies?: string[]
}

const props = withDefaults(defineProps<{
  tasks: GanttTask[]
  startDate?: string
  endDate?: string
}>(), {
  tasks: () => [],
})

const subjectColors: Record<string, string> = {
  'subject-数学': '#2981fd',
  'subject-英语': '#67c23a',
  'subject-专业课': '#e6a23c',
  'subject-算法': '#7b5ce7',
  'subject-数据结构': '#f56c6c',
  default: '#909399',
}

function subjectColor(klass: string): string {
  return subjectColors[klass || ''] || subjectColors.default
}

const uniqueSubjects = computed(() => {
  const subs = new Set(props.tasks.map(t => t.custom_class || 'default'))
  return Array.from(subs)
})

const dateRange = computed(() => {
  if (props.tasks.length === 0) return []
  const dates = props.tasks.flatMap(t => [new Date(t.start.split('T')[0]), new Date(t.end.split('T')[0])])
  if (dates.length === 0) return []
  const min = new Date(Math.min(...dates.map(d => d.getTime())))
  const max = new Date(Math.max(...dates.map(d => d.getTime())))
  const range: Date[] = []
  const cur = new Date(min)
  while (cur <= max) {
    range.push(new Date(cur))
    cur.setDate(cur.getDate() + 1)
  }
  return range
})

const totalDays = computed(() => dateRange.value.length || 1)

const displayTasks = computed(() => props.tasks)

function formatShortDate(d: Date): string {
  return `${d.getMonth() + 1}/${d.getDate()}`
}

function isWeekend(d: Date): boolean {
  return d.getDay() === 0 || d.getDay() === 6
}

function getBarStyle(task: GanttTask) {
  const startDate = new Date(task.start.split('T')[0])
  const endDate = new Date(task.end.split('T')[0])
  const firstDate = dateRange.value[0]
  if (!firstDate) return { left: '0%', width: '10%' }

  const dayOffset = Math.floor((startDate.getTime() - firstDate.getTime()) / (1000 * 60 * 60 * 24))
  const durationDays = Math.max(1, Math.ceil((endDate.getTime() - startDate.getTime()) / (1000 * 60 * 60 * 24)))
  const leftPct = (dayOffset / totalDays.value) * 100
  const widthPct = Math.max(4, (durationDays / totalDays.value) * 100)

  return {
    left: leftPct + '%',
    width: widthPct + '%',
    background: subjectColor(task.custom_class || 'default') + '20',
    borderColor: subjectColor(task.custom_class || 'default'),
  }
}
</script>

<style scoped>
.gantt-container {
  background: var(--color-bg-white);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-lg);
  overflow-x: auto;
  overflow-y: hidden;
}

.gantt-legend {
  display: flex;
  gap: 16px;
  padding: 10px 16px;
  border-bottom: 1px solid var(--color-border-light);
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--color-text-secondary);
}

.legend-item::before {
  content: '';
  width: 10px;
  height: 10px;
  border-radius: 2px;
  background: var(--dot-color, #2981fd);
}

.gantt-header, .gantt-row {
  display: flex;
}

.gantt-label-col {
  width: 160px;
  min-width: 160px;
  padding: 8px 12px;
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text-regular);
  border-right: 1px solid var(--color-border-light);
  border-bottom: 1px solid var(--color-border-light);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.gantt-timeline-col {
  flex: 1;
  display: flex;
  min-width: 500px;
  position: relative;
}

.gantt-time-slot {
  flex: 1;
  text-align: center;
  padding: 8px 0;
  font-size: 11px;
  color: var(--color-text-secondary);
  border-right: 1px solid var(--color-border-light);
}

.gantt-time-slot.is-weekend {
  background: #fafafa;
}

.gantt-bar-row {
  height: 36px;
  position: relative;
  align-items: center;
  border-bottom: 1px solid var(--color-border-light);
}

.gantt-bar {
  position: absolute;
  top: 6px;
  height: 24px;
  border-radius: 4px;
  border: 1px solid;
  cursor: pointer;
  transition: opacity var(--transition-fast);
}

.gantt-bar:hover {
  opacity: 0.85;
}

.gantt-bar-progress {
  height: 100%;
  border-radius: 3px;
  transition: width var(--transition-base);
}

.gantt-task-name {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.gantt-empty {
  padding: 40px;
  text-align: center;
  color: var(--color-text-placeholder);
  font-size: 14px;
}
</style>
