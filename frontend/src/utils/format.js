/** 日期与数字格式化工具 */

function toDate(value) {
  if (!value) return null
  if (value instanceof Date) return value
  // 后端返回 ISO 字符串（部分字段不带时区），统一按本地时间解析
  const normalized = typeof value === 'string' && !/[zZ]|[+-]\d{2}:\d{2}$/.test(value)
    ? value.replace(' ', 'T')
    : value
  const d = new Date(normalized)
  return Number.isNaN(d.getTime()) ? null : d
}

const pad = (n) => String(n).padStart(2, '0')

/** 2025-11-01 10:00 */
export function formatDateTime(value, withSecond = false) {
  const d = toDate(value)
  if (!d) return '-'
  const base = `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
  return withSecond ? `${base}:${pad(d.getSeconds())}` : base
}

/** 2025-11-01 */
export function formatDate(value) {
  const d = toDate(value)
  if (!d) return '-'
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}

/** 转成 <input type="datetime-local"> 需要的格式 */
export function toLocalInput(value) {
  const d = toDate(value)
  if (!d) return ''
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`
}

/** 2025-11-01T10:00 -> ISO 字符串（后端接受 datetime） */
export function fromLocalInput(value) {
  if (!value) return null
  return value.length === 16 ? `${value}:00` : value
}

/** 距离某时间的可读描述 */
export function relativeTo(value, now = Date.now()) {
  const d = toDate(value)
  if (!d) return ''
  const diff = d.getTime() - now
  const abs = Math.abs(diff)
  const min = 60 * 1000
  const hour = 60 * min
  const day = 24 * hour
  const suffix = diff >= 0 ? '后' : '前'
  if (abs < min) return '刚刚'
  if (abs < hour) return `${Math.floor(abs / min)} 分钟${suffix}`
  if (abs < day) return `${Math.floor(abs / hour)} 小时${suffix}`
  if (abs < 30 * day) return `${Math.floor(abs / day)} 天${suffix}`
  return formatDate(d)
}

/** 倒计时片段，用于活动卡片 */
export function countdownParts(target, now = Date.now()) {
  const d = toDate(target)
  if (!d) return null
  let diff = d.getTime() - now
  const past = diff < 0
  diff = Math.abs(diff)
  const day = Math.floor(diff / 86400000)
  const hour = Math.floor((diff % 86400000) / 3600000)
  const min = Math.floor((diff % 3600000) / 60000)
  const sec = Math.floor((diff % 60000) / 1000)
  return { past, day, hour, min, sec }
}

export function formatCountdown(target) {
  const p = countdownParts(target)
  if (!p) return ''
  const parts = []
  if (p.day) parts.push(`${p.day} 天`)
  if (p.hour || p.day) parts.push(`${p.hour} 时`)
  parts.push(`${p.min} 分`)
  if (!p.day) parts.push(`${p.sec} 秒`)
  return parts.join(' ')
}

/** 数字千分位 */
export function formatNumber(value) {
  const n = Number(value)
  if (!Number.isFinite(n)) return '0'
  return n.toLocaleString('zh-CN')
}

/** 百分比：0.1234 -> 12.34% */
export function formatPercent(ratio, digits = 2) {
  const n = Number(ratio)
  if (!Number.isFinite(n)) return '0%'
  return `${(n * 100).toFixed(digits)}%`
}

/** 手机号脱敏 */
export function maskPhone(phone) {
  if (!phone || phone.length < 7) return phone || '-'
  return `${phone.slice(0, 3)}****${phone.slice(-4)}`
}

/** 取用户名首字作为头像占位 */
export function initial(name) {
  if (!name) return '?'
  return String(name).trim().slice(0, 1).toUpperCase()
}
