/** 全局提示（Toast） */

import { ref } from 'vue'
import { defineStore } from 'pinia'

let seed = 0

export const useToastStore = defineStore('toast', () => {
  const items = ref([])

  function remove(id) {
    items.value = items.value.filter((item) => item.id !== id)
  }

  function push(message, type = 'info', duration = 3600) {
    if (!message) return -1
    const id = (seed += 1)
    items.value = [...items.value, { id, message: String(message), type }]
    if (items.value.length > 4) items.value = items.value.slice(-4)
    if (duration > 0) setTimeout(() => remove(id), duration)
    return id
  }

  const success = (message, duration) => push(message, 'success', duration)
  const error = (message, duration) => push(message, 'error', duration ?? 5000)
  const info = (message, duration) => push(message, 'info', duration)
  const warning = (message, duration) => push(message, 'warning', duration ?? 4400)

  /** 统一处理接口异常 */
  function fromError(err, fallback = '操作失败') {
    return error(err?.message || fallback)
  }

  return { items, push, remove, success, error, info, warning, fromError }
})
