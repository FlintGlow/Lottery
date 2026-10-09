/** 确认对话框：以 Promise 方式调用，便于在业务代码中 await */

import { reactive } from 'vue'
import { defineStore } from 'pinia'

export const useConfirmStore = defineStore('confirm', () => {
  const state = reactive({
    open: false,
    title: '',
    message: '',
    detail: '',
    confirmText: '确定',
    cancelText: '取消',
    tone: 'primary',
    loading: false,
  })

  let resolver = null

  function ask(options = {}) {
    Object.assign(state, {
      open: true,
      title: options.title || '请确认',
      message: options.message || '',
      detail: options.detail || '',
      confirmText: options.confirmText || '确定',
      cancelText: options.cancelText || '取消',
      tone: options.tone || 'primary',
      loading: false,
    })
    return new Promise((resolve) => {
      resolver = resolve
    })
  }

  function settle(value) {
    state.open = false
    state.loading = false
    if (resolver) {
      resolver(value)
      resolver = null
    }
  }

  const confirm = () => settle(true)
  const cancel = () => settle(false)

  return { state, ask, confirm, cancel, settle }
})
