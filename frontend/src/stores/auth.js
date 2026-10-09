/** 认证状态：令牌、当前用户、角色权限 */

import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import { authApi, userApi } from '@/api'
import { clearTokens, getTokens, setTokens, setUnauthorizedHandler } from '@/api/client'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const tokens = ref(getTokens())
  const loading = ref(false)
  const loaded = ref(false)

  const isLoggedIn = computed(() => Boolean(tokens.value?.access))
  const roles = computed(() =>
    (user.value?.roles || [])
      .filter((role) => role.status === 'enabled')
      .map((role) => role.code),
  )
  const isAdmin = computed(() => roles.value.includes('admin'))
  const isOperator = computed(() => roles.value.includes('admin') || roles.value.includes('operator'))
  const displayName = computed(() => user.value?.username || '未登录')
  const avatarUrl = computed(() => user.value?.avatar_url || '')

  function hasAnyRole(list) {
    if (!list?.length) return true
    return list.some((code) => roles.value.includes(code))
  }

  function applySession(pair) {
    const next = { access: pair.access_token, refresh: pair.refresh_token }
    setTokens(next)
    tokens.value = next
  }

  function clearSession() {
    clearTokens()
    tokens.value = null
    user.value = null
    loaded.value = false
  }

  async function login(payload) {
    loading.value = true
    try {
      const pair = await authApi.login(payload)
      applySession(pair)
      await fetchMe()
      return pair
    } finally {
      loading.value = false
    }
  }

  async function register(payload) {
    loading.value = true
    try {
      const pair = await authApi.register(payload)
      applySession(pair)
      await fetchMe()
      return pair
    } finally {
      loading.value = false
    }
  }

  async function fetchMe() {
    if (!tokens.value?.access) return null
    const me = await userApi.me()
    user.value = me
    loaded.value = true
    return me
  }

  /** 首次进入应用时恢复用户信息 */
  async function ensureLoaded() {
    if (!isLoggedIn.value) return null
    if (loaded.value && user.value) return user.value
    try {
      return await fetchMe()
    } catch {
      clearSession()
      return null
    }
  }

  async function logout() {
    const token = tokens.value?.access
    clearSession()
    if (!token) return
    try {
      await authApi.logout(token)
    } catch {
      /* 本地会话已清理，服务端注销失败不阻塞用户 */
    }
  }

  async function updateProfile(payload) {
    const me = await userApi.updateMe(payload)
    user.value = me
    return me
  }

  async function changePassword(payload) {
    return userApi.changePassword(payload)
  }

  // 令牌彻底失效时（刷新也失败）清理并交由 App 层跳转登录
  setUnauthorizedHandler(() => {
    clearSession()
  })

  return {
    user,
    tokens,
    loading,
    loaded,
    isLoggedIn,
    roles,
    isAdmin,
    isOperator,
    displayName,
    avatarUrl,
    hasAnyRole,
    login,
    register,
    fetchMe,
    ensureLoaded,
    logout,
    updateProfile,
    changePassword,
    clearSession,
  }
})
