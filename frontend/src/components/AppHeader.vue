<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import AppIcon from './AppIcon.vue'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'
import { useRouter, useRoute } from '@/router'
import { initial } from '@/utils/format'

const auth = useAuthStore()
const toast = useToastStore()
const router = useRouter()
const route = useRoute()

const menuOpen = ref(false)
const userOpen = ref(false)
const scrolled = ref(false)

const NAV = [
  { path: '/', label: '活动广场', icon: 'sparkles' },
  { path: '/records', label: '抽奖记录', icon: 'ticket', auth: true },
  { path: '/winnings', label: '我的奖品', icon: 'trophy', auth: true },
]

const navItems = computed(() => NAV.filter((item) => !item.auth || auth.isLoggedIn))

function isActive(path) {
  if (path === '/') return route.path === '/' || route.path.startsWith('/activity/')
  return route.path.startsWith(path)
}

function go(path) {
  menuOpen.value = false
  userOpen.value = false
  router.push(path)
}

async function logout() {
  userOpen.value = false
  await auth.logout()
  toast.success('已退出登录')
  router.push('/')
}

function onDocumentClick(event) {
  if (!event.target.closest?.('.user-menu')) userOpen.value = false
  if (!event.target.closest?.('.nav-collapse') && !event.target.closest?.('.nav-toggle')) {
    menuOpen.value = false
  }
}

function onScroll() {
  scrolled.value = window.scrollY > 6
}

onMounted(() => {
  document.addEventListener('click', onDocumentClick)
  window.addEventListener('scroll', onScroll, { passive: true })
  onScroll()
})

onBeforeUnmount(() => {
  document.removeEventListener('click', onDocumentClick)
  window.removeEventListener('scroll', onScroll)
})

watch(() => route.fullPath, () => {
  menuOpen.value = false
  userOpen.value = false
})
</script>

<template>
  <header class="app-header" :class="{ 'is-scrolled': scrolled }">
    <div class="container header-inner">
      <a class="brand" href="#/" @click.prevent="go('/')">
        <span class="brand-mark">
          <AppIcon name="sparkles" :size="19" />
        </span>
        <span class="brand-text">
          <strong>幸运抽奖</strong>
          <small>Lucky Draw</small>
        </span>
      </a>

      <nav class="nav-desktop" aria-label="主导航">
        <a
          v-for="item in navItems"
          :key="item.path"
          class="nav-link"
          :class="{ 'is-active': isActive(item.path) }"
          :href="`#${item.path}`"
          @click.prevent="go(item.path)"
        >
          <AppIcon :name="item.icon" :size="16" />
          <span>{{ item.label }}</span>
        </a>
        <a
          v-if="auth.isOperator"
          class="nav-link"
          :class="{ 'is-active': route.path.startsWith('/admin') }"
          href="#/admin"
          @click.prevent="go('/admin')"
        >
          <AppIcon name="chart" :size="16" />
          <span>运营后台</span>
        </a>
      </nav>

      <div class="header-right">
        <template v-if="auth.isLoggedIn">
          <div class="user-menu">
            <button
              class="user-trigger"
              type="button"
              :aria-expanded="userOpen"
              @click="userOpen = !userOpen"
            >
              <img v-if="auth.avatarUrl" class="avatar avatar-sm" :src="auth.avatarUrl" alt="" />
              <span v-else class="avatar avatar-sm">{{ initial(auth.displayName) }}</span>
              <span class="user-name truncate">{{ auth.displayName }}</span>
              <AppIcon name="chevronDown" :size="14" class="chev" :class="{ 'is-open': userOpen }" />
            </button>
            <Transition name="fade">
              <div v-if="userOpen" class="dropdown">
                <div class="dropdown-head">
                  <img v-if="auth.avatarUrl" class="avatar" :src="auth.avatarUrl" alt="" />
                  <span v-else class="avatar">{{ initial(auth.displayName) }}</span>
                  <div class="grow">
                    <p class="strong truncate">{{ auth.displayName }}</p>
                    <p class="text-xs text-muted">
                      {{ auth.roles.length ? auth.roles.join(' · ') : '普通用户' }}
                    </p>
                  </div>
                </div>
                <hr class="divider" />
                <button class="dropdown-item" type="button" @click="go('/profile')">
                  <AppIcon name="user" :size="16" />
                  个人中心
                </button>
                <button class="dropdown-item" type="button" @click="go('/winnings')">
                  <AppIcon name="trophy" :size="16" />
                  我的奖品
                </button>
                <button
                  v-if="auth.isOperator"
                  class="dropdown-item"
                  type="button"
                  @click="go('/admin')"
                >
                  <AppIcon name="chart" :size="16" />
                  运营后台
                </button>
                <hr class="divider" />
                <button class="dropdown-item is-danger" type="button" @click="logout">
                  <AppIcon name="logout" :size="16" />
                  退出登录
                </button>
              </div>
            </Transition>
          </div>
        </template>
        <template v-else>
          <button class="btn btn-sm btn-ghost" type="button" @click="go('/login')">登录</button>
          <button class="btn btn-sm btn-primary" type="button" @click="go('/login?tab=register')">
            免费注册
          </button>
        </template>

        <button
          class="btn btn-icon nav-toggle"
          type="button"
          aria-label="菜单"
          @click="menuOpen = !menuOpen"
        >
          <AppIcon :name="menuOpen ? 'close' : 'menu'" :size="18" />
        </button>
      </div>
    </div>

    <Transition name="fade">
      <div v-if="menuOpen" class="nav-collapse">
        <div class="container stack-sm">
          <a
            v-for="item in navItems"
            :key="item.path"
            class="nav-link is-block"
            :class="{ 'is-active': isActive(item.path) }"
            :href="`#${item.path}`"
            @click.prevent="go(item.path)"
          >
            <AppIcon :name="item.icon" :size="16" />
            <span>{{ item.label }}</span>
          </a>
          <a
            v-if="auth.isOperator"
            class="nav-link is-block"
            :class="{ 'is-active': route.path.startsWith('/admin') }"
            href="#/admin"
            @click.prevent="go('/admin')"
          >
            <AppIcon name="chart" :size="16" />
            <span>运营后台</span>
          </a>
          <a
            v-if="auth.isLoggedIn"
            class="nav-link is-block"
            href="#/profile"
            @click.prevent="go('/profile')"
          >
            <AppIcon name="user" :size="16" />
            <span>个人中心</span>
          </a>
        </div>
      </div>
    </Transition>
  </header>
</template>

<style scoped>
.app-header {
  position: sticky;
  top: 0;
  z-index: var(--z-header);
  background: rgba(255, 255, 255, 0.82);
  backdrop-filter: saturate(180%) blur(14px);
  border-bottom: 1px solid transparent;
  transition: border-color var(--dur) var(--ease), box-shadow var(--dur) var(--ease);
}
.app-header.is-scrolled {
  border-bottom-color: var(--border);
  box-shadow: 0 2px 16px rgba(26, 23, 48, 0.05);
}
.header-inner {
  height: var(--header-h);
  display: flex;
  align-items: center;
  gap: var(--sp-5);
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  color: var(--ink-900);
  flex-shrink: 0;
}
.brand:hover { color: var(--ink-900); }
.brand-mark {
  display: grid;
  place-items: center;
  width: 36px;
  height: 36px;
  border-radius: 11px;
  background: linear-gradient(135deg, var(--brand-500), var(--brand-800));
  color: #fff;
  box-shadow: var(--shadow-brand);
}
.brand-text { display: flex; flex-direction: column; line-height: 1.1; }
.brand-text strong { font-size: 15.5px; font-weight: 700; letter-spacing: -0.01em; }
.brand-text small {
  font-size: 10px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--ink-400);
  font-weight: 600;
}

.nav-desktop {
  display: flex;
  align-items: center;
  gap: 2px;
  margin-left: var(--sp-4);
  flex: 1;
}
.nav-link {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  height: 36px;
  padding: 0 13px;
  border-radius: var(--radius-sm);
  color: var(--ink-600);
  font-size: 13.8px;
  font-weight: 550;
  transition: background var(--dur-fast) var(--ease), color var(--dur-fast) var(--ease);
}
.nav-link:hover { background: var(--ink-100); color: var(--ink-900); }
.nav-link.is-active { background: var(--brand-50); color: var(--brand-700); }
.nav-link.is-block { height: 42px; width: 100%; }

.header-right {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  margin-left: auto;
  flex-shrink: 0;
}
.nav-toggle { display: none; }

.user-menu { position: relative; }
.user-trigger {
  display: flex;
  align-items: center;
  gap: 8px;
  height: 40px;
  padding: 0 10px 0 5px;
  border: 1px solid var(--border);
  border-radius: var(--radius-pill);
  background: var(--surface);
  cursor: pointer;
  transition: border-color var(--dur-fast) var(--ease), box-shadow var(--dur-fast) var(--ease);
}
.user-trigger:hover { border-color: var(--brand-300); box-shadow: var(--shadow-xs); }
.user-name { max-width: 96px; font-size: 13.5px; font-weight: 600; color: var(--ink-800); }
.chev { color: var(--ink-400); transition: transform var(--dur-fast) var(--ease); }
.chev.is-open { transform: rotate(180deg); }

.dropdown {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  width: 236px;
  padding: 6px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  box-shadow: var(--shadow-lg);
  z-index: var(--z-dropdown);
}
.dropdown-head {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 8px 10px;
}
.dropdown-item {
  display: flex;
  align-items: center;
  gap: 9px;
  width: 100%;
  height: 36px;
  padding: 0 10px;
  border: 0;
  border-radius: var(--radius-xs);
  background: transparent;
  color: var(--ink-700);
  font-size: 13.5px;
  font-weight: 550;
  cursor: pointer;
  text-align: left;
}
.dropdown-item:hover { background: var(--ink-100); color: var(--ink-900); }
.dropdown-item.is-danger { color: var(--danger-600); }
.dropdown-item.is-danger:hover { background: var(--danger-50); }

.nav-collapse {
  display: none;
  padding: var(--sp-3) 0 var(--sp-4);
  border-top: 1px solid var(--border);
  background: var(--surface);
}

@media (max-width: 900px) {
  .nav-desktop { display: none; }
  .nav-toggle { display: inline-flex; }
  .nav-collapse { display: block; }
  .user-name { display: none; }
}
</style>
