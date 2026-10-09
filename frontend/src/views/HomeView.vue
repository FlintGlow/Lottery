<script setup>
import { computed, onMounted, ref } from 'vue'
import AppIcon from '@/components/AppIcon.vue'
import ActivityCard from '@/components/ActivityCard.vue'
import EmptyState from '@/components/EmptyState.vue'
import { activityApi } from '@/api'
import { useRouter } from '@/router'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'

const router = useRouter()
const auth = useAuthStore()
const toast = useToastStore()

const activities = ref([])
const loading = ref(true)
const error = ref('')
const keyword = ref('')
const filter = ref('all')

const FILTERS = [
  { key: 'all', label: '全部' },
  { key: 'ongoing', label: '进行中' },
  { key: 'pending', label: '即将开始' },
  { key: 'ended', label: '已结束' },
]

const STATUS_ORDER = { ongoing: 0, pending: 1, paused: 2, ended: 3, draft: 4 }

const filtered = computed(() => {
  const kw = keyword.value.trim().toLowerCase()
  return activities.value
    .filter((item) => (filter.value === 'all' ? true : item.status === filter.value))
    .filter((item) => (kw ? String(item.name || '').toLowerCase().includes(kw) : true))
    .sort((a, b) => {
      const sa = STATUS_ORDER[a.status] ?? 9
      const sb = STATUS_ORDER[b.status] ?? 9
      if (sa !== sb) return sa - sb
      return new Date(b.start_time || 0) - new Date(a.start_time || 0)
    })
})

const stats = computed(() => ({
  total: activities.value.length,
  ongoing: activities.value.filter((a) => a.status === 'ongoing').length,
  prizes: activities.value.reduce((sum, a) => sum + (a.prize_count || 0), 0),
}))

const counts = computed(() => {
  const map = { all: activities.value.length }
  activities.value.forEach((a) => {
    map[a.status] = (map[a.status] || 0) + 1
  })
  return map
})

async function load() {
  loading.value = true
  error.value = ''
  try {
    const list = await activityApi.listPublic()
    activities.value = Array.isArray(list) ? list : []
    enrich()
  } catch (err) {
    error.value = err?.message || '活动列表加载失败'
  } finally {
    loading.value = false
  }
}

/** 列表接口不返回奖品数量，这里为展示中的活动补齐（并发受限） */
async function enrich() {
  const targets = activities.value.slice(0, 12).filter((a) => a.prize_count === undefined)
  if (!targets.length) return
  const results = await Promise.allSettled(targets.map((a) => activityApi.getPublic(a.id)))
  results.forEach((res, index) => {
    if (res.status !== 'fulfilled') return
    const detail = res.value
    const target = activities.value.find((a) => a.id === targets[index].id)
    if (target && detail) target.prize_count = detail.prize_count ?? 0
  })
}

function goLogin() {
  router.push('/login')
}

onMounted(load)
</script>

<template>
  <div class="home">
    <!-- Hero -->
    <section class="hero">
      <div class="hero-bg" aria-hidden="true">
        <span class="orb orb-1" />
        <span class="orb orb-2" />
        <span class="orb orb-3" />
      </div>
      <div class="container hero-inner">
        <div class="hero-copy">
          <span class="hero-tag">
            <AppIcon name="sparkles" :size="14" />
            实时开奖 · 库存透明
          </span>
          <h1 class="hero-title">
            幸运抽奖，
            <span class="grad">好礼即刻揭晓</span>
          </h1>
          <p class="hero-desc">
            参与正在进行的活动即可抽奖，中奖记录实时可查，实物奖品在线提交收货信息即可等待发放。
          </p>
          <div class="hero-actions">
            <button class="btn btn-lg btn-gold" type="button" @click="filter = 'ongoing'">
              <AppIcon name="gift" :size="17" />
              去抽奖
            </button>
            <button
              v-if="!auth.isLoggedIn"
              class="btn btn-lg hero-ghost"
              type="button"
              @click="goLogin"
            >
              登录 / 注册
            </button>
            <button v-else class="btn btn-lg hero-ghost" type="button" @click="router.push('/winnings')">
              <AppIcon name="trophy" :size="16" />
              我的奖品
            </button>
          </div>
          <div class="hero-stats">
            <div class="hero-stat">
              <strong>{{ stats.total }}</strong>
              <span>个活动</span>
            </div>
            <div class="hero-stat">
              <strong>{{ stats.ongoing }}</strong>
              <span>正在进行</span>
            </div>
            <div class="hero-stat">
              <strong>{{ stats.prizes }}</strong>
              <span>件奖品</span>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 列表 -->
    <section class="container section">
      <div class="section-head">
        <div>
          <h2 class="section-title">活动列表</h2>
          <p class="text-sm text-muted mt-0">选择感兴趣的活动，点击卡片进入抽奖</p>
        </div>
        <div class="toolbar">
          <div class="search-box">
            <AppIcon name="search" :size="15" />
            <input v-model="keyword" class="search-input" type="search" placeholder="搜索活动名称" />
          </div>
          <button class="btn btn-icon" type="button" title="刷新" @click="load">
            <AppIcon name="refresh" :size="16" />
          </button>
        </div>
      </div>

      <div class="chips">
        <button
          v-for="item in FILTERS"
          :key="item.key"
          class="chip"
          :class="{ 'is-active': filter === item.key }"
          type="button"
          @click="filter = item.key"
        >
          {{ item.label }}
          <span v-if="counts[item.key]" class="chip-count">{{ counts[item.key] }}</span>
        </button>
      </div>

      <div v-if="loading" class="grid grid-auto mt-5">
        <div v-for="n in 6" :key="n" class="skeleton skeleton-card" />
      </div>

      <div v-else-if="error" class="mt-5">
        <div class="alert alert-danger">
          <AppIcon class="alert-icon" name="alert" :size="16" />
          <div class="grow">
            <p class="strong">加载失败</p>
            <p>{{ error }}</p>
            <p class="text-xs mt-2">
              请确认后端服务已启动，并在 vite.config.js 中配置了 /api 代理。
            </p>
          </div>
          <button class="btn btn-sm" type="button" @click="load">重试</button>
        </div>
      </div>

      <div v-else-if="!filtered.length" class="mt-5 card">
        <EmptyState
          icon="inbox"
          title="没有符合条件的活动"
          desc="换一个筛选条件，或稍后再来看看"
        />
      </div>

      <div v-else class="grid grid-auto mt-5">
        <ActivityCard v-for="item in filtered" :key="item.id" :activity="item" />
      </div>
    </section>
  </div>
</template>

<style scoped>
/* ---------- Hero ---------- */
.hero {
  position: relative;
  overflow: hidden;
  background: linear-gradient(140deg, #2a1a5e 0%, #4c1d95 45%, #6d28d9 100%);
  color: #fff;
  padding-block: var(--sp-9) var(--sp-10);
}
.hero-bg { position: absolute; inset: 0; pointer-events: none; }
.orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(60px);
  opacity: 0.5;
}
.orb-1 {
  width: 420px; height: 420px; top: -140px; right: -80px;
  background: radial-gradient(circle, #fbbf24, transparent 70%);
  opacity: 0.34;
}
.orb-2 {
  width: 360px; height: 360px; bottom: -160px; left: -60px;
  background: radial-gradient(circle, #22d3ee, transparent 70%);
  opacity: 0.24;
}
.orb-3 {
  width: 300px; height: 300px; top: 40%; left: 45%;
  background: radial-gradient(circle, #f472b6, transparent 70%);
  opacity: 0.2;
}
.hero-inner { position: relative; }
.hero-copy { max-width: 640px; }
.hero-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 5px 12px;
  border-radius: var(--radius-pill);
  background: rgba(255, 255, 255, 0.14);
  border: 1px solid rgba(255, 255, 255, 0.2);
  font-size: 12.5px;
  font-weight: 600;
  letter-spacing: 0.02em;
  backdrop-filter: blur(6px);
}
.hero-title {
  margin-top: var(--sp-4);
  font-size: clamp(28px, 4.4vw, 44px);
  font-weight: 760;
  line-height: 1.18;
  letter-spacing: -0.03em;
  color: #fff;
}
.grad {
  background: linear-gradient(100deg, #fde68a, #fbbf24 45%, #f59e0b);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}
.hero-desc {
  margin-top: var(--sp-4);
  font-size: 15px;
  line-height: 1.75;
  color: rgba(255, 255, 255, 0.76);
  max-width: 540px;
}
.hero-actions {
  display: flex;
  gap: var(--sp-3);
  margin-top: var(--sp-6);
  flex-wrap: wrap;
}
.hero-ghost {
  background: rgba(255, 255, 255, 0.12);
  border-color: rgba(255, 255, 255, 0.26);
  color: #fff;
  backdrop-filter: blur(6px);
}
.hero-ghost:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.2);
  border-color: rgba(255, 255, 255, 0.4);
}
.hero-stats {
  display: flex;
  gap: var(--sp-7);
  margin-top: var(--sp-7);
  padding-top: var(--sp-5);
  border-top: 1px solid rgba(255, 255, 255, 0.16);
}
.hero-stat { display: flex; flex-direction: column; }
.hero-stat strong {
  font-size: 26px;
  font-weight: 750;
  font-variant-numeric: tabular-nums;
  letter-spacing: -0.02em;
}
.hero-stat span { font-size: 12.5px; color: rgba(255, 255, 255, 0.66); }

/* ---------- 列表 ---------- */
.section { padding-block: var(--sp-8) var(--sp-9); }
.section-head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: var(--sp-4);
  flex-wrap: wrap;
}
.search-box {
  display: flex;
  align-items: center;
  gap: 7px;
  height: 38px;
  padding: 0 12px;
  border: 1px solid var(--border-strong);
  border-radius: var(--radius-sm);
  background: var(--surface);
  color: var(--ink-400);
  transition: border-color var(--dur-fast) var(--ease), box-shadow var(--dur-fast) var(--ease);
}
.search-box:focus-within {
  border-color: var(--brand-500);
  box-shadow: 0 0 0 3.5px var(--brand-100);
}
.search-input {
  border: 0;
  outline: 0;
  background: transparent;
  width: 170px;
  font-size: 13.5px;
  color: var(--ink-900);
}
.chips {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: var(--sp-5);
}
.chip-count {
  display: inline-grid;
  place-items: center;
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  border-radius: var(--radius-pill);
  background: var(--ink-100);
  color: var(--ink-500);
  font-size: 11px;
  font-weight: 700;
}
.chip.is-active .chip-count { background: rgba(255, 255, 255, 0.25); color: #fff; }

@media (max-width: 640px) {
  .hero { padding-block: var(--sp-7) var(--sp-8); }
  .hero-stats { gap: var(--sp-5); }
  .search-input { width: 120px; }
}
</style>
