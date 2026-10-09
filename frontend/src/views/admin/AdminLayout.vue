<script setup>
import { computed, ref } from 'vue'
import AppIcon from '@/components/AppIcon.vue'
import { useRoute, useRouter } from '@/router'
import { useAuthStore } from '@/stores/auth'
import { initial } from '@/utils/format'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const collapsed = ref(false)

const NAV_GROUPS = [
  {
    title: '运营',
    items: [
      { path: '/admin', label: '运营概览', icon: 'chart', exact: true },
      { path: '/admin/activities', label: '活动管理', icon: 'sparkles' },
      { path: '/admin/prizes', label: '奖品管理', icon: 'gift' },
    ],
  },
  {
    title: '发放',
    items: [
      { path: '/admin/winnings', label: '中奖与发放', icon: 'trophy' },
      { path: '/admin/rewards', label: '人工补发', icon: 'send' },
    ],
  },
  {
    title: '系统',
    items: [
      { path: '/admin/users', label: '用户管理', icon: 'users', roles: ['admin'] },
      { path: '/admin/roles', label: '角色管理', icon: 'shield', roles: ['admin'] },
    ],
  },
]

const groups = computed(() =>
  NAV_GROUPS.map((group) => ({
    ...group,
    items: group.items.filter((item) => !item.roles || auth.hasAnyRole(item.roles)),
  })).filter((group) => group.items.length),
)

function isActive(item) {
  if (item.exact) return route.path === item.path
  return route.path.startsWith(item.path)
}

const pageTitle = computed(() => route.meta?.title || '运营后台')
</script>

<template>
  <div class="admin" :class="{ 'is-collapsed': collapsed }">
    <aside class="sidebar">
      <div class="sidebar-head">
        <a class="sidebar-brand" href="#/admin" @click.prevent="router.push('/admin')">
          <span class="brand-mark"><AppIcon name="sparkles" :size="18" /></span>
          <span v-if="!collapsed" class="brand-text">
            <strong>幸运抽奖</strong>
            <small>运营后台</small>
          </span>
        </a>
        <button
          class="btn btn-icon collapse-btn"
          type="button"
          :aria-label="collapsed ? '展开侧栏' : '收起侧栏'"
          @click="collapsed = !collapsed"
        >
          <AppIcon :name="collapsed ? 'chevronRight' : 'chevronLeft'" :size="16" />
        </button>
      </div>

      <nav class="sidebar-nav">
        <div v-for="group in groups" :key="group.title" class="nav-group">
          <p v-if="!collapsed" class="nav-group-title">{{ group.title }}</p>
          <a
            v-for="item in group.items"
            :key="item.path"
            class="nav-item"
            :class="{ 'is-active': isActive(item) }"
            :href="`#${item.path}`"
            :title="collapsed ? item.label : ''"
            @click.prevent="router.push(item.path)"
          >
            <AppIcon :name="item.icon" :size="17" />
            <span v-if="!collapsed">{{ item.label }}</span>
          </a>
        </div>
      </nav>

      <div class="sidebar-foot">
        <a class="nav-item" href="#/" @click.prevent="router.push('/')">
          <AppIcon name="home" :size="17" />
          <span v-if="!collapsed">返回前台</span>
        </a>
        <div v-if="!collapsed" class="sidebar-user">
          <img v-if="auth.avatarUrl" class="avatar avatar-sm" :src="auth.avatarUrl" alt="" />
          <span v-else class="avatar avatar-sm">{{ initial(auth.displayName) }}</span>
          <div class="grow" style="min-width: 0">
            <p class="text-sm strong truncate">{{ auth.displayName }}</p>
            <p class="text-xs text-muted truncate">{{ auth.roles.join(' · ') || '—' }}</p>
          </div>
        </div>
      </div>
    </aside>

    <div class="admin-main">
      <header class="admin-topbar">
        <div>
          <h1 class="admin-title">{{ pageTitle }}</h1>
          <p class="text-xs text-muted">幸运抽奖系统 · 运营管理</p>
        </div>
      </header>
      <div class="admin-content">
        <slot />
      </div>
    </div>
  </div>
</template>

<style scoped>
.admin {
  display: grid;
  grid-template-columns: 232px minmax(0, 1fr);
  min-height: calc(100vh - var(--header-h));
  background: var(--bg);
}
.admin.is-collapsed { grid-template-columns: 68px minmax(0, 1fr); }

.sidebar {
  display: flex;
  flex-direction: column;
  background: var(--surface);
  border-right: 1px solid var(--border);
  position: sticky;
  top: var(--header-h);
  height: calc(100vh - var(--header-h));
  overflow-y: auto;
}
.sidebar-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: var(--sp-4);
  border-bottom: 1px solid var(--border);
}
.sidebar-brand { display: flex; align-items: center; gap: 10px; color: var(--ink-900); }
.sidebar-brand:hover { color: var(--ink-900); }
.brand-mark {
  display: grid;
  place-items: center;
  width: 34px;
  height: 34px;
  border-radius: 10px;
  background: linear-gradient(135deg, var(--brand-500), var(--brand-800));
  color: #fff;
  flex-shrink: 0;
}
.brand-text { display: flex; flex-direction: column; line-height: 1.15; }
.brand-text strong { font-size: 14.5px; font-weight: 700; }
.brand-text small { font-size: 10px; color: var(--ink-400); letter-spacing: 0.1em; }
.collapse-btn { flex-shrink: 0; }

.sidebar-nav { flex: 1; padding: var(--sp-3) 10px; }
.nav-group + .nav-group { margin-top: var(--sp-4); }
.nav-group-title {
  padding: 0 10px 6px;
  font-size: 10.5px;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--ink-400);
}
.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  height: 38px;
  padding: 0 10px;
  border-radius: var(--radius-sm);
  color: var(--ink-600);
  font-size: 13.6px;
  font-weight: 550;
  transition: background var(--dur-fast) var(--ease), color var(--dur-fast) var(--ease);
}
.nav-item:hover { background: var(--ink-100); color: var(--ink-900); }
.nav-item.is-active {
  background: linear-gradient(135deg, var(--brand-600), var(--brand-800));
  color: #fff;
  box-shadow: var(--shadow-brand);
}
.sidebar-foot { padding: var(--sp-3) 10px var(--sp-4); border-top: 1px solid var(--border); }
.sidebar-user {
  display: flex;
  align-items: center;
  gap: 9px;
  margin-top: var(--sp-3);
  padding: 8px 10px;
  background: var(--surface-2);
  border-radius: var(--radius-sm);
}

.admin-main { min-width: 0; display: flex; flex-direction: column; }
.admin-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--sp-4);
  padding: var(--sp-5) var(--sp-6) var(--sp-4);
  background: var(--surface);
  border-bottom: 1px solid var(--border);
}
.admin-title { font-size: 19px; font-weight: 700; letter-spacing: -0.02em; }
.admin-content { padding: var(--sp-6); flex: 1; min-width: 0; }

@media (max-width: 900px) {
  .admin,
  .admin.is-collapsed { grid-template-columns: 68px minmax(0, 1fr); }
  .brand-text,
  .nav-group-title,
  .nav-item span,
  .sidebar-user { display: none; }
  .admin-content { padding: var(--sp-4); }
  .admin-topbar { padding: var(--sp-4); }
}
</style>
