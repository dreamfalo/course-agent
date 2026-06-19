<template>
  <div class="calendar-widget">
    <!-- 月份导航 -->
    <div class="cal-header">
      <button class="cal-nav-btn" @click="prevMonth">
        <el-icon><ArrowLeft /></el-icon>
      </button>
      <span class="cal-title">{{ currentYear }}年 {{ currentMonth + 1 }}月</span>
      <button class="cal-nav-btn" @click="nextMonth">
        <el-icon><ArrowRight /></el-icon>
      </button>
    </div>

    <!-- 星期头 -->
    <div class="cal-weekdays">
      <span v-for="d in weekdays" :key="d" class="cal-weekday">{{ d }}</span>
    </div>

    <!-- 日期网格 -->
    <div class="cal-grid">
      <div
        v-for="(day, idx) in calendarDays"
        :key="idx"
        class="cal-day"
        :class="{
          'is-today': day.isToday,
          'is-selected': day.isSelected,
          'is-other-month': !day.isCurrentMonth,
          'has-events': day.events && day.events.length > 0,
        }"
        @click="selectDay(day)"
      >
        <span class="cal-day-num">{{ day.dayOfMonth }}</span>
        <div class="cal-events" v-if="day.events?.length">
          <span
            v-for="(evt, ei) in day.events.slice(0, 2)"
            :key="ei"
            class="cal-event-dot"
            :style="{ background: evt.color || '#2981fd' }"
            :title="evt.title"
          ></span>
          <span v-if="day.events.length > 2" class="cal-event-more">+{{ day.events.length - 2 }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { ArrowLeft, ArrowRight } from '@element-plus/icons-vue'

export interface CalendarEvent {
  date: string
  title: string
  color?: string
}

const props = defineProps<{
  events?: CalendarEvent[]
  modelValue?: Date
}>()

const emit = defineEmits<{
  'update:modelValue': [date: Date]
  select: [date: Date]
}>()

const weekdays = ['日', '一', '二', '三', '四', '五', '六']

const today = new Date()
const currentYear = ref(today.getFullYear())
const currentMonth = ref(today.getMonth())
const selectedDate = ref<Date | null>(props.modelValue || null)

interface DayCell {
  date: Date
  dayOfMonth: number
  isCurrentMonth: boolean
  isToday: boolean
  isSelected: boolean
  events: CalendarEvent[]
}

const calendarDays = computed<DayCell[]>(() => {
  const year = currentYear.value
  const month = currentMonth.value
  const firstDay = new Date(year, month, 1)
  const lastDay = new Date(year, month + 1, 0)
  const startDayOfWeek = firstDay.getDay()
  const daysInMonth = lastDay.getDate()
  const days: DayCell[] = []

  // 上月填充
  const prevLastDay = new Date(year, month, 0).getDate()
  for (let i = startDayOfWeek - 1; i >= 0; i--) {
    const d = new Date(year, month - 1, prevLastDay - i)
    days.push(makeCell(d, false))
  }

  // 本月
  for (let i = 1; i <= daysInMonth; i++) {
    const d = new Date(year, month, i)
    days.push(makeCell(d, true))
  }

  // 下月填充
  const remaining = 42 - days.length
  for (let i = 1; i <= remaining; i++) {
    const d = new Date(year, month + 1, i)
    days.push(makeCell(d, false))
  }

  return days
})

function makeCell(date: Date, isCurrentMonth: boolean): DayCell {
  const dateStr = formatDate(date)
  const dayEvents = (props.events || []).filter(e => e.date === dateStr)
  return {
    date,
    dayOfMonth: date.getDate(),
    isCurrentMonth,
    isToday: date.toDateString() === today.toDateString(),
    isSelected: selectedDate.value?.toDateString() === date.toDateString(),
    events: dayEvents,
  }
}

function formatDate(d: Date): string {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

function selectDay(day: DayCell) {
  if (!day.isCurrentMonth) return
  selectedDate.value = day.date
  emit('update:modelValue', day.date)
  emit('select', day.date)
}

function prevMonth() {
  if (currentMonth.value === 0) {
    currentYear.value--
    currentMonth.value = 11
  } else {
    currentMonth.value--
  }
}

function nextMonth() {
  if (currentMonth.value === 11) {
    currentYear.value++
    currentMonth.value = 0
  } else {
    currentMonth.value++
  }
}
</script>

<style scoped>
.calendar-widget {
  background: var(--color-bg-white);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border-light);
  padding: 16px;
  user-select: none;
}

.cal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.cal-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.cal-nav-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: none;
  border-radius: 50%;
  background: transparent;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.cal-nav-btn:hover {
  background: var(--color-bg-selected);
  color: var(--color-primary);
}

.cal-weekdays {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  text-align: center;
  margin-bottom: 4px;
}

.cal-weekday {
  font-size: 12px;
  color: var(--color-text-secondary);
  padding: 4px 0;
  font-weight: 500;
}

.cal-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 2px;
}

.cal-day {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 4px 2px;
  border-radius: 6px;
  cursor: pointer;
  min-height: 48px;
  transition: background var(--transition-fast);
}

.cal-day:hover {
  background: var(--color-bg-card-hover);
}

.cal-day.is-other-month {
  opacity: 0.3;
  cursor: default;
}

.cal-day.is-today .cal-day-num {
  background: var(--color-primary);
  color: #fff;
}

.cal-day.is-selected {
  background: var(--color-bg-selected);
}

.cal-day-num {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  border-radius: 50%;
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text-primary);
}

.cal-events {
  display: flex;
  gap: 2px;
  margin-top: 2px;
  flex-wrap: wrap;
  justify-content: center;
}

.cal-event-dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
}

.cal-event-more {
  font-size: 10px;
  color: var(--color-text-secondary);
}
</style>
