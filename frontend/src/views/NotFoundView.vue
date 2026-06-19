<template>
  <div class="-page">
    <h2 class="text-title"></h2>
    <p class="text-caption" style="margin-top:8px"></p>
    <div class="divider" />
    <div class="placeholder-content">
      <el-icon :size="48" color="#c0c4cc"><HomeFilled /></el-icon>
      <p style="margin-top:16px;color:var(--color-text-placeholder)">此页面待开发</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { HomeFilled } from '@element-plus/icons-vue'
</script>

<style scoped>
.placeholder-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 0;
}
</style>
