<template>
  <div class="line-chart-container">
    <canvas ref="canvasRef" :width="width" :height="height"></canvas>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'

interface DataPoint { label: string; value: number }

const props = withDefaults(defineProps<{
  data: DataPoint[]
  width?: number
  height?: number
  color?: string
  fillColor?: string
}>(), {
  width: 580,
  height: 180,
  color: '#2981fd',
  fillColor: 'rgba(41,129,253,0.08)',
})

const canvasRef = ref<HTMLCanvasElement>()

function draw() {
  const canvas = canvasRef.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  if (!ctx) return

  const { width, height, data, color, fillColor } = props
  const padding = { top: 20, right: 16, bottom: 28, left: 36 }
  const cw = width; const ch = height
  const pw = cw - padding.left - padding.right
  const ph = ch - padding.top - padding.bottom

  ctx.clearRect(0, 0, cw, ch)

  if (!data.length) return

  const maxVal = Math.max(...data.map(d => d.value), 1)
  const stepY = ph / 5

  // 网格线
  ctx.strokeStyle = '#f3f4f6'; ctx.lineWidth = 1
  for (let i = 0; i <= 5; i++) {
    const y = padding.top + i * stepY
    ctx.beginPath(); ctx.moveTo(padding.left, y); ctx.lineTo(cw - padding.right, y); ctx.stroke()
    ctx.fillStyle = '#9ca3af'; ctx.font = '10px sans-serif'; ctx.textAlign = 'right'
    ctx.fillText((maxVal - (maxVal / 5) * i).toFixed(0) + 'h', padding.left - 6, y + 3)
  }

  // X 轴标签
  const stepX = pw / Math.max(data.length - 1, 1)
  ctx.textAlign = 'center'
  data.forEach((d, i) => {
    const x = padding.left + i * stepX
    ctx.fillStyle = '#9ca3af'; ctx.font = '11px sans-serif'
    ctx.fillText(d.label, x, ch - 8)
  })

  // 填充区域
  ctx.beginPath()
  data.forEach((d, i) => {
    const x = padding.left + i * stepX
    const y = padding.top + ph - (d.value / maxVal) * ph
    i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y)
  })
  const lastX = padding.left + (data.length - 1) * stepX
  ctx.lineTo(lastX, padding.top + ph)
  ctx.lineTo(padding.left, padding.top + ph)
  ctx.closePath()
  ctx.fillStyle = fillColor; ctx.fill()

  // 折线
  ctx.beginPath()
  ctx.strokeStyle = color; ctx.lineWidth = 2.5; ctx.lineJoin = 'round'
  data.forEach((d, i) => {
    const x = padding.left + i * stepX
    const y = padding.top + ph - (d.value / maxVal) * ph
    i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y)
  })
  ctx.stroke()

  // 数据点
  data.forEach((d, i) => {
    const x = padding.left + i * stepX
    const y = padding.top + ph - (d.value / maxVal) * ph
    ctx.beginPath(); ctx.arc(x, y, 4, 0, Math.PI * 2)
    ctx.fillStyle = '#fff'; ctx.fill(); ctx.strokeStyle = color; ctx.lineWidth = 2; ctx.stroke()
  })
}

onMounted(draw)
watch(() => props.data, draw, { deep: true })
watch(() => props.width, draw)
</script>

<style scoped>
.line-chart-container { display: inline-block; }
canvas { display: block; }
</style>
