<template>
  <button class="blue-btn" :class="[sizeClass, { block, loading }]" :disabled="disabled || loading" v-bind="$attrs">
    <el-icon v-if="loading" class="is-loading"><Loading /></el-icon>
    <el-icon v-if="icon && !loading"><component :is="icon" /></el-icon>
    <span v-if="$slots.default"><slot /></span>
  </button>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Loading } from '@element-plus/icons-vue'

const props = withDefaults(defineProps<{
  size?: 'small' | 'default' | 'large'
  block?: boolean
  loading?: boolean
  disabled?: boolean
  icon?: any
}>(), {
  size: 'default',
  block: false,
  loading: false,
  disabled: false,
})

const sizeClass = computed(() => `btn-${props.size}`)
</script>

<style scoped>
.blue-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  font-weight: 500;
  color: var(--color-text-inverse);
  background: var(--color-primary);
  border: none;
  border-radius: var(--radius-base);
  cursor: pointer;
  transition: all var(--transition-fast);
  user-select: none;
  white-space: nowrap;
  line-height: 1.5;
}

.blue-btn:hover:not(:disabled) {
  background: var(--color-primary-hover);
  box-shadow: 0 2px 8px rgba(41, 129, 253, 0.35);
}
.blue-btn:active:not(:disabled) {
  background: var(--color-primary-active);
}
.blue-btn:disabled {
  background: var(--color-bg-disabled);
  color: var(--color-text-placeholder);
  cursor: not-allowed;
  box-shadow: none;
}

.btn-small { padding: 4px 12px; font-size: 12px; border-radius: 4px; }
.btn-default { padding: 8px 20px; font-size: 14px; }
.btn-large { padding: 10px 24px; font-size: 15px; border-radius: var(--radius-lg); }

.block { width: 100%; }
.loading { opacity: 0.75; }
</style>
