/**
 * 轻量路由：运行环境无法安装 vue-router，这里实现一个满足本项目需要的最小路由。
 *
 * 特性：hash 模式、路径参数、查询参数、路由元信息（标题/布局/权限）、
 * 导航守卫（登录态与角色）、滚动复位、视图过渡所需的响应式当前路由。
 */

import { defineAsyncComponent, reactive, readonly } from 'vue'

import RouteLoading from '@/components/RouteLoading.vue'
import { useAuthStore } from '@/stores/auth'

/**
 * 路由懒加载：必须用 defineAsyncComponent 包装。
 * 直接把 () => import(...) 交给 <component :is> 会被当成函数式组件，渲染出 [object Promise]。
 */
const lazy = (loader) =>
  defineAsyncComponent({
    loader,
    loadingComponent: RouteLoading,
    delay: 120,
    timeout: 20000,
  })

const routes = [
  {
    path: '/',
    name: 'home',
    component: lazy(() => import('@/views/HomeView.vue')),
    meta: { title: '活动广场' },
  },
  {
    path: '/login',
    name: 'login',
    component: lazy(() => import('@/views/LoginView.vue')),
    meta: { title: '登录 / 注册', bare: true },
  },
  {
    path: '/activity/:id',
    name: 'activity',
    component: lazy(() => import('@/views/ActivityDetailView.vue')),
    meta: { title: '活动详情' },
  },
  {
    path: '/records',
    name: 'records',
    component: lazy(() => import('@/views/MyRecordsView.vue')),
    meta: { title: '我的抽奖记录', requiresAuth: true },
  },
  {
    path: '/winnings',
    name: 'winnings',
    component: lazy(() => import('@/views/MyWinningsView.vue')),
    meta: { title: '我的奖品', requiresAuth: true },
  },
  {
    path: '/profile',
    name: 'profile',
    component: lazy(() => import('@/views/ProfileView.vue')),
    meta: { title: '个人中心', requiresAuth: true },
  },
  {
    path: '/admin',
    name: 'admin-dashboard',
    component: lazy(() => import('@/views/admin/AdminDashboardView.vue')),
    meta: { title: '运营概览', requiresAuth: true, roles: ['admin', 'operator'], layout: 'admin' },
  },
  {
    path: '/admin/activities',
    name: 'admin-activities',
    component: lazy(() => import('@/views/admin/AdminActivitiesView.vue')),
    meta: { title: '活动管理', requiresAuth: true, roles: ['admin', 'operator'], layout: 'admin' },
  },
  {
    path: '/admin/prizes',
    name: 'admin-prizes',
    component: lazy(() => import('@/views/admin/AdminPrizesView.vue')),
    meta: { title: '奖品管理', requiresAuth: true, roles: ['admin', 'operator'], layout: 'admin' },
  },
  {
    path: '/admin/winnings',
    name: 'admin-winnings',
    component: lazy(() => import('@/views/admin/AdminWinningsView.vue')),
    meta: { title: '中奖与发放', requiresAuth: true, roles: ['admin', 'operator'], layout: 'admin' },
  },
  {
    path: '/admin/rewards',
    name: 'admin-rewards',
    component: lazy(() => import('@/views/admin/AdminRewardsView.vue')),
    meta: { title: '人工补发', requiresAuth: true, roles: ['admin', 'operator'], layout: 'admin' },
  },
  {
    path: '/admin/users',
    name: 'admin-users',
    component: lazy(() => import('@/views/admin/AdminUsersView.vue')),
    meta: { title: '用户管理', requiresAuth: true, roles: ['admin'], layout: 'admin' },
  },
  {
    path: '/admin/roles',
    name: 'admin-roles',
    component: lazy(() => import('@/views/admin/AdminRolesView.vue')),
    meta: { title: '角色管理', requiresAuth: true, roles: ['admin'], layout: 'admin' },
  },
  {
    path: '*',
    name: 'not-found',
    component: lazy(() => import('@/views/NotFoundView.vue')),
    meta: { title: '页面不存在' },
  },
]

const state = reactive({
  path: '/',
  name: '',
  params: {},
  query: {},
  meta: {},
  fullPath: '/',
  matched: null,
})

function parsePath(pathWithQuery) {
  const [path, search = ''] = String(pathWithQuery || '/').split('?')
  const query = {}
  new URLSearchParams(search).forEach((value, key) => {
    query[key] = value
  })
  return { path: path || '/', query }
}

function matchRoute(path) {
  const segments = path.split('/').filter(Boolean)
  for (const route of routes) {
    if (route.path === '*') continue
    const routeSegments = route.path.split('/').filter(Boolean)
    if (routeSegments.length !== segments.length) continue
    const params = {}
    let matched = true
    for (let i = 0; i < routeSegments.length; i += 1) {
      const rs = routeSegments[i]
      if (rs.startsWith(':')) params[rs.slice(1)] = decodeURIComponent(segments[i])
      else if (rs !== segments[i]) {
        matched = false
        break
      }
    }
    if (matched) return { route, params }
  }
  return { route: routes.find((r) => r.path === '*'), params: {} }
}

function resolve(to) {
  const { path, query } = parsePath(to)
  const { route, params } = matchRoute(path)
  return { path, query, route, params }
}

function toHash(target) {
  const qs = new URLSearchParams(target.query).toString()
  return `#${target.path}${qs ? `?${qs}` : ''}`
}

function apply(target) {
  state.path = target.path
  state.name = target.route.name
  state.params = target.params
  state.query = target.query
  state.meta = target.route.meta || {}
  state.matched = target.route
  state.fullPath = `${target.path}${Object.keys(target.query).length
    ? `?${new URLSearchParams(target.query).toString()}`
    : ''}`
  document.title = state.meta.title
    ? `${state.meta.title} · 幸运抽奖系统`
    : '幸运抽奖系统'
}

/**
 * 导航守卫：登录态与角色校验。
 * 角色来自 /users/me，页面首次加载（或刷新）时必须先取回用户信息再判定，
 * 否则带 roles 的路由会被误判为无权限并跳回首页。
 */
async function guard(target) {
  const meta = target.route.meta || {}
  const auth = useAuthStore()

  if (meta.requiresAuth && !auth.isLoggedIn) {
    return { path: '/login', query: { redirect: target.path } }
  }

  if (meta.roles?.length) {
    await auth.ensureLoaded()
    if (!auth.isLoggedIn) {
      return { path: '/login', query: { redirect: target.path } }
    }
    if (!auth.hasAnyRole(meta.roles)) {
      return { path: '/', query: { denied: '1' } }
    }
  }

  return null
}

async function navigate(to, { replace = false, skipGuard = false } = {}) {
  const target = resolve(to)
  if (!skipGuard) {
    const redirect = await guard(target)
    if (redirect) {
      navigate(redirect, { replace: true, skipGuard: true })
      return
    }
  }
  const hash = toHash(target)
  if (replace) {
    window.history.replaceState(null, '', hash)
    apply(target)
    window.scrollTo({ top: 0 })
  } else if (window.location.hash === hash) {
    apply(target)
  } else {
    window.location.hash = hash
  }
}

async function onHashChange() {
  const target = resolve(window.location.hash.replace(/^#/, '') || '/')
  const redirect = await guard(target)
  if (redirect) {
    navigate(redirect, { replace: true, skipGuard: true })
    return
  }
  apply(target)
  window.scrollTo({ top: 0 })
}

let started = false

export const router = {
  current: readonly(state),
  push: (to) => navigate(to),
  replace: (to) => navigate(to, { replace: true }),
  back: () => window.history.back(),
  resolve,
  routes,
  start() {
    if (!started) {
      window.addEventListener('hashchange', onHashChange)
      started = true
    }
    onHashChange()
  },
}

export function useRoute() {
  return state
}

export function useRouter() {
  return router
}

export default router
