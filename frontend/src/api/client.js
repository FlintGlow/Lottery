/**
 * HTTP 客户端：统一响应体解析、令牌注入、401 自动刷新、错误归一化。
 *
 * 后端约定（见接口文档第 3、5 章）：
 *   成功  { code: 0, message, data }
 *   失败  { code: <非0>, message, data }，HTTP 状态码与 code 前三位一致
 *   校验失败 code=42200，data 为逐条错误明细
 */

const BASE = import.meta.env.VITE_API_BASE || '/api/v1'
const TOKEN_KEY = 'lottery.tokens'

export class ApiError extends Error {
  constructor(message, { code = -1, status = 0, data = null } = {}) {
    super(message)
    this.name = 'ApiError'
    this.code = code
    this.status = status
    this.data = data
  }

  get isAuth() {
    return this.status === 401
  }

  get isForbidden() {
    return this.status === 403
  }

  get isNetwork() {
    return this.status === 0
  }
}

/* ---------------------------------------------------------------- 令牌 */

function readTokens() {
  try {
    const raw = localStorage.getItem(TOKEN_KEY)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

let tokens = readTokens()
let unauthorizedHandler = null
let refreshInFlight = null

export function getTokens() {
  return tokens
}

export function setTokens(next) {
  tokens = next || null
  try {
    if (tokens) localStorage.setItem(TOKEN_KEY, JSON.stringify(tokens))
    else localStorage.removeItem(TOKEN_KEY)
  } catch {
    /* 忽略隐私模式下的写入失败 */
  }
}

export function clearTokens() {
  setTokens(null)
}

/** 由 auth store 注入：刷新失败或未登录时清理会话 */
export function setUnauthorizedHandler(handler) {
  unauthorizedHandler = handler
}

/** 令牌彻底失效：清理本地会话并广播事件（由 main.js 负责跳转登录页） */
function notifyUnauthorized() {
  clearTokens()
  if (unauthorizedHandler) unauthorizedHandler()
  window.dispatchEvent(new CustomEvent('lottery:unauthorized'))
}

/* ---------------------------------------------------------------- 工具 */

function buildUrl(path, params) {
  const url = path.startsWith('http') ? path : `${BASE}${path}`
  if (!params) return url
  const search = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => {
    if (value === undefined || value === null || value === '') return
    if (Array.isArray(value)) value.forEach((v) => search.append(key, v))
    else search.append(key, value)
  })
  const qs = search.toString()
  return qs ? `${url}${url.includes('?') ? '&' : '?'}${qs}` : url
}

function validationMessage(detail) {
  if (!Array.isArray(detail) || !detail.length) return '参数校验失败'
  const first = detail[0] || {}
  const loc = Array.isArray(first.loc) ? first.loc.filter((x) => x !== 'body' && x !== 'query').join('.') : ''
  const msg = first.msg || '参数不合法'
  return loc ? `${loc}：${msg}` : msg
}

async function parseBody(response) {
  const text = await response.text()
  if (!text) return null
  try {
    return JSON.parse(text)
  } catch {
    return { __raw: text }
  }
}

/** 刷新访问令牌；并发调用共用同一个 Promise */
function refreshTokens() {
  if (refreshInFlight) return refreshInFlight
  const current = tokens
  if (!current?.refresh) return Promise.resolve(null)

  refreshInFlight = (async () => {
    try {
      const res = await fetch(buildUrl('/auth/refresh'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: current.refresh }),
      })
      const payload = await parseBody(res)
      if (!res.ok || !payload || payload.code !== 0 || !payload.data) {
        return null
      }
      const next = {
        access: payload.data.access_token,
        refresh: payload.data.refresh_token || current.refresh,
      }
      setTokens(next)
      return next
    } catch {
      return null
    } finally {
      refreshInFlight = null
    }
  })()

  return refreshInFlight
}

/* ---------------------------------------------------------------- 主流程 */

async function send(method, path, options = {}) {
  const {
    params,
    body,
    formData,
    auth = true,
    retry = true,
    signal,
    timeout = 20000,
  } = options

  const headers = {}
  if (!formData && body !== undefined) headers['Content-Type'] = 'application/json'
  if (auth && tokens?.access) headers.Authorization = `Bearer ${tokens.access}`

  const controller = new AbortController()
  const timer = timeout ? setTimeout(() => controller.abort(), timeout) : null
  if (signal) signal.addEventListener('abort', () => controller.abort(), { once: true })

  let response
  try {
    response = await fetch(buildUrl(path, params), {
      method,
      headers,
      body: formData || (body !== undefined ? JSON.stringify(body) : undefined),
      signal: controller.signal,
    })
  } catch (error) {
    if (error?.name === 'AbortError') {
      throw new ApiError('请求超时，请稍后重试', { status: 0 })
    }
    throw new ApiError('无法连接后端服务，请确认服务已启动', { status: 0 })
  } finally {
    if (timer) clearTimeout(timer)
  }

  // 访问令牌过期：尝试刷新一次并重放请求
  if (response.status === 401 && auth && retry && tokens?.refresh) {
    const next = await refreshTokens()
    if (next) return send(method, path, { ...options, retry: false })
    const payload = await parseBody(response)
    notifyUnauthorized()
    throw new ApiError(payload?.message || '登录状态已失效，请重新登录', {
      code: payload?.code ?? 40100,
      status: 401,
    })
  }

  const payload = await parseBody(response)

  if (response.ok && payload && payload.code === 0) {
    return payload.data
  }

  if (response.ok && payload && payload.code === undefined) {
    // 非统一响应体（例如 /health）
    return payload
  }

  if (response.status === 401) {
    notifyUnauthorized()
  }

  let message = payload?.message
  if (response.status === 422) message = validationMessage(payload?.data)
  if (!message) {
    message = response.status ? `请求失败（HTTP ${response.status}）` : '请求失败'
  }

  throw new ApiError(message, {
    code: payload?.code ?? response.status * 100,
    status: response.status,
    data: payload?.data ?? null,
  })
}

export const http = {
  get: (path, params, options) => send('GET', path, { params, ...options }),
  post: (path, body, options) => send('POST', path, { body, ...options }),
  put: (path, body, options) => send('PUT', path, { body, ...options }),
  patch: (path, body, options) => send('PATCH', path, { body, ...options }),
  del: (path, options) => send('DELETE', path, options),
  upload: (path, formData, options) =>
    send('POST', path, { formData, timeout: 60000, ...options }),
}

export default http
