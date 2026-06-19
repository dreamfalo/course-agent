<template>
  <div class="app-layout">
    <header class="app-header">
      <div class="header-left">
        <div class="logo">
          <el-icon :size="24" color="#fff"><Notebook /></el-icon>
          <span class="logo-text">智能课程助手</span>
        </div>
      </div>
      <div class="header-right">
        <div class="header-actions">
          <!-- 用户下拉 -->
          <el-dropdown v-if="userStore.username" trigger="hover" @command="handleUserCommand">
            <span class="header-user">
              <el-icon><UserFilled /></el-icon>
              {{ userStore.username }}
              <span class="role-tag">{{ userStore.role === 'admin' ? '管理员' : '学生' }}</span>
              <el-icon class="arrow-icon"><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="settings">
                  <el-icon><Setting /></el-icon> 系统设置
                </el-dropdown-item>
                <el-dropdown-item divided command="logout">
                  <el-icon><SwitchButton /></el-icon> 退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>
    </header>

    <div class="app-body">
      <aside class="app-sidebar" :class="{ collapsed: sidebarCollapsed }">
        <nav class="sidebar-nav">
          <router-link v-for="item in navItems" :key="item.path" :to="item.path" class="nav-item" :class="{ active: isActive(item.path) }">
            <el-icon :size="18"><component :is="item.icon" /></el-icon>
            <span class="nav-text">{{ item.label }}</span>
          </router-link>
        </nav>
        <div class="sidebar-divider" />
        <div class="sidebar-custom"><slot name="sidebar" /></div>
        <div class="sidebar-toggle" @click="toggleSidebar" :title="sidebarCollapsed ? '展开侧边栏' : '收起侧边栏'">
          <el-icon :size="16"><DArrowLeft v-if="!sidebarCollapsed" /><DArrowRight v-else /></el-icon>
        </div>
      </aside>
      <main class="app-main">
        <div class="main-content"><slot name="default" /></div>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElMessageBox } from 'element-plus'
import {
  Notebook, UserFilled, SwitchButton, DArrowLeft, DArrowRight, ArrowLeft, ArrowRight, ArrowDown,
  HomeFilled, Calendar, List, ChatDotSquare, Setting,
} from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const sidebarCollapsed = ref(false)

const navItems = [
  { path: '/home', label: '首页', icon: HomeFilled },
  { path: '/schedule', label: '课表管理', icon: Calendar },
  { path: '/tasks', label: '学习任务', icon: List },
  { path: '/chat', label: 'AI 对话', icon: ChatDotSquare },
]

function isActive(path: string): boolean {
  return route.path === path || route.path.startsWith(path + '/')
}

function toggleSidebar() { sidebarCollapsed.value = !sidebarCollapsed.value }

async function handleUserCommand(cmd: string) {
  if (cmd === 'settings') {
    router.push('/settings')
  } else if (cmd === 'logout') {
    try {
      await ElMessageBox.confirm('确定要退出登录吗？', '提示', { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' })
    } catch { return }
    userStore.logout()
    router.push('/login')
  }
}
</script>

<style scoped>
.app-layout { display: flex; flex-direction: column; height: 100vh; overflow: hidden; }

.app-header {
  display: flex; align-items: center; justify-content: space-between;
  height: 56px; padding: 0 24px; flex-shrink: 0;
  background: linear-gradient(135deg, #2b82fe 0%, #2981fd 100%);
  z-index: 100;
}
.header-left { display: flex; align-items: center; }
.logo { display: flex; align-items: center; gap: 10px; }
.logo-text { font-size: 18px; font-weight: 700; color: #fff; letter-spacing: 1px; }
.header-right { display: flex; align-items: center; }
.header-actions { display: flex; align-items: center; gap: 16px; }
.header-user {
  display: flex; align-items: center; gap: 6px;
  color: rgba(255,255,255,0.9); font-size: 14px; cursor: pointer;
  padding: 6px 12px; border-radius: 8px; transition: background .15s;
}
.header-user:hover { background: rgba(255,255,255,0.15); }
.arrow-icon { font-size: 12px; margin-left: 2px; }
.role-tag { font-size: 11px; padding: 2px 8px; border-radius: 10px; background: rgba(255,255,255,0.2); color: #fff; }

.app-body { display: flex; flex: 1; overflow: hidden; }

.app-sidebar {
  position: relative; width: 220px; flex-shrink: 0;
  background: #fff; border-right: 1px solid #f3f4f6;
  overflow-y: auto; display: flex; flex-direction: column;
  transition: width .2s;
}
.app-sidebar.collapsed { width: 60px; }
.app-sidebar.collapsed .nav-text,
.app-sidebar.collapsed .sidebar-custom { display: none; }

.sidebar-nav { padding: 12px 8px; display: flex; flex-direction: column; gap: 2px; }
.nav-item {
  display: flex; align-items: center; gap: 10px;
  padding: 10px 12px; border-radius: 8px;
  color: #4b5563; font-size: 14px;
  text-decoration: none; transition: all .15s; white-space: nowrap;
}
.nav-item:hover { background: #f0f7ff; color: #2981fd; }
.nav-item.active { background: #e8f1fe; color: #2981fd; font-weight: 600; }

.sidebar-divider { height: 1px; background: #f3f4f6; margin: 8px 12px; }
.sidebar-custom { flex: 1; padding: 4px 12px; overflow-y: auto; }
.sidebar-toggle {
  position: absolute; bottom: 12px; left: 50%; transform: translateX(-50%);
  display: flex; align-items: center; justify-content: center;
  width: 32px; height: 32px; border-radius: 50%;
  background: #f0f7ff; border: 1px solid #f3f4f6;
  cursor: pointer; color: #9ca3af; transition: all .15s; z-index: 10;
}
.sidebar-toggle:hover { background: #e8f1fe; color: #2981fd; }

.app-main { flex: 1; overflow-y: auto; background: #f8fafc; }
.main-content { padding: 24px; height: calc(100vh - 64px); overflow: hidden; }
</style>