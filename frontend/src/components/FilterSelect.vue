<template>
  <div class="filter-select">
    <label v-if="label" class="filter-label">{{ label }}</label>
    <el-select
      v-model="model"
      :placeholder="placeholder"
      :clearable="clearable"
      :multiple="multiple"
      :disabled="disabled"
      popper-class="filter-select-popper"
      @change="$emit('update:modelValue', model)"
      @visible-change="$emit('visible-change', $event)"
    >
      <el-option
        v-for="opt in options"
        :key="opt.value"
        :label="opt.label"
        :value="opt.value"
      />
    </el-select>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Option {
  label: string
  value: string | number
}

const props = defineProps<{
  modelValue?: string | number | (string | number)[]
  options: Option[]
  label?: string
  placeholder?: string
  clearable?: boolean
  multiple?: boolean
  disabled?: boolean
}>()

defineEmits<{
  'update:modelValue': [value: any]
  'visible-change': [visible: boolean]
}>()

const model = computed({
  get: () => props.modelValue,
  set: (val) => { /* 由 el-select v-model 驱动 */ },
})
</script>

<style scoped>
.filter-select {
  display: flex;
  align-items: center;
  gap: 8px;
}

.filter-label {
  font-size: 13px;
  color: var(--color-text-regular);
  white-space: nowrap;
  font-weight: 500;
}

:deep(.el-select) {
  min-width: 140px;
}
</style>
