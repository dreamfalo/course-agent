import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useUserStore = defineStore('user', () => {
  const token = ref<string>('')
  const refreshToken = ref<string>('')
  const userId = ref<string>('')
  const username = ref<string>('')
  const role = ref<'student' | 'admin'>('student')
  const email = ref<string>('')
  const phone = ref<string>('')

  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => role.value === 'admin')

  function setAuth(access: string, refresh: string) {
    token.value = access
    refreshToken.value = refresh
    localStorage.setItem('access_token', access)
    localStorage.setItem('refresh_token', refresh)
  }

  function setUser(data: {
    username: string
    role?: 'student' | 'admin'
    email?: string
    phone?: string
    id?: number | string
  }) {
    username.value = data.username
    userId.value = String(data.id || '')
    role.value = data.role || 'student'
    email.value = data.email || ''
    phone.value = data.phone || ''
  }

  function logout() {
    token.value = ''
    refreshToken.value = ''
    userId.value = ''
    username.value = ''
    role.value = 'student'
    email.value = ''
    phone.value = ''
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
  }

  // 从 localStorage 恢复
  function restore() {
    const savedToken = localStorage.getItem('access_token')
    const savedRefresh = localStorage.getItem('refresh_token')
    if (savedToken) {
      token.value = savedToken
      refreshToken.value = savedRefresh || ''
    }
  }

  return {
    token, refreshToken, userId, username, role, email, phone,
    isLoggedIn, isAdmin,
    setAuth, setUser, logout, restore,
  }
}, {
  persist: {
    key: 'user-store',
    storage: localStorage,
    paths: ['token', 'refreshToken', 'userId', 'username', 'role'],
  },
})
