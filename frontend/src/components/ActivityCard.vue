<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import AppIcon from './AppIcon.vue'
import StatusBadge from './StatusBadge.vue'
import { ACTIVITY_STATUS } from '@/utils/constants'
import { formatDate, countdownParts } from '@/utils/format'

const props = defineProps({
  activity: { type: Object, required: true },
})

const now = ref(Date.now())
let timer = null

onMounted(() => {
  timer = setInterval(() => {
    now.value = Date.now()
  }, 1000)
})
onBeforeUnmount(() => timer && clearInterval(timer))

const status = computed(() => props.activity.status)
const canDraw = computed(() => status.value === 'ongoing')

/** 封面缺省时按 id 生成稳定的渐变，避免所有卡片长得一样 */
const gradients = [
  'linear-gradient(135deg,#7c3aed,#4c1d95)',
  'linear-gradient(135deg,#f59e0b,#b45309)',
  'linear-gradient(135deg,#0ea5e9,#1e3a8a)',
  'linear-gradient(135deg,#ec4899,#831843)',
  'linear-gradient(135deg,#10b981,#065f46)',
  'linear-gradient(135deg,#6366f1,#312e81)',
]
const gradient = computed(() => gradients[Number(props.activity.id || 0) % gradients.length])

const countdown = computed(() => {
  if (status.value === 'pending') {
    const parts = countdownParts(props.activity.start_time, now.value)
    return parts ? `距开始 ${formatParts(parts)}` : ''
  }
  if (status.value === 'ongoing') {
    const parts = countdownParts(props.activity.end_time, now.value)
    return parts ? `距结束 ${formatParts(parts)}` : ''
  }
  return ''
})

function formatParts(p) {
  if (p.past) return '已到期'
  if (p.day > 0) return `${p.day} 天 ${p.hour} 小时`
  if (p.hour > 0) return `${p.hour} 时 ${p.min} 分`
  return `${p.min} 分 ${String(p.sec).padStart(2, '0')} 秒`
}

const limits = computed(() => {
  const a = props.activity
  const list = []
  if (a.total_draw_limit > 0) list.push(`活动限 ${a.total_draw_limit} 次`)
  if (a.daily_draw_limit > 0) list.push(`每日 ${a.daily_draw_limit} 次`)
  return list
})
</script>

<template>
  <a class="activity-card card card-hover" :href="`#/activity/${activity.id}`">
    <div class="cover" :style="activity.cover_url ? {} : { background: gradient }">
      <img v-if="activity.cover_url" :src="activity.cover_url" :alt="activity.name" />
      <div v-else class="cover-fallback">
        <AppIcon name="gift" :size="38" />
      </div>
      <div class="cover-top">
        <StatusBadge :map="ACTIVITY_STATUS" :value="status" size="lg" />
      </div>
    </div>

    <div class="body">
      <h3 class="title truncate">{{ activity.name }}</h3>
      <p class="desc clamp-2">{{ activity.description || '参与活动即有机会赢取丰厚奖品' }}</p>

      <div class="meta">
        <span class="meta-item">
          <AppIcon name="calendar" :size="13" />
          {{ formatDate(activity.start_time) }} – {{ formatDate(activity.end_time) }}
        </span>
        <span class="meta-item">
          <AppIcon name="gift" :size="13" />
          {{ activity.prize_count ?? 0 }} 个奖品
        </span>
      </div>

      <div class="foot">
        <span v-if="countdown" class="countdown" :class="{ 'is-live': canDraw }">
          <AppIcon name="clock" :size="13" />
          {{ countdown }}
        </span>
        <span v-else class="text-xs text-soft">{{ ACTIVITY_STATUS[status]?.desc || '' }}</span>
        <span class="cta" :class="{ 'is-live': canDraw }">
          {{ canDraw ? '立即抽奖' : '查看详情' }}
          <AppIcon name="arrowRight" :size="14" />
        </span>
      </div>

      <p v-if="limits.length" class="limits text-xs text-soft">{{ limits.join(' · ') }}</p>
    </div>
  </a>
</template>

<style scoped>
.activity-card {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  color: inherit;
}
.activity-card:hover { color: inherit; }

.cover {
  position: relative;
  aspect-ratio: 16 / 9;
  background: var(--surface-3);
  overflow: hidden;
}
.cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform var(--dur-slow) var(--ease-out);
}
.activity-card:hover .cover img { transform: scale(1.04); }
.cover-fallback {
  width: 100%;
  height: 100%;
  display: grid;
  place-items: center;
  color: rgba(255, 255, 255, 0.72);
}
.cover-top {
  position: absolute;
  top: 10px;
  left: 10px;
  display: flex;
  gap: 6px;
}
.cover-top :deep(.badge) {
  background: rgba(255, 255, 255, 0.94);
  backdrop-filter: blur(6px);
  box-shadow: var(--shadow-xs);
}

.body {
  display: flex;
  flex-direction: column;
  gap: 7px;
  padding: var(--sp-4) var(--sp-5) var(--sp-5);
  flex: 1;
}
.title { font-size: 16px; font-weight: 680; }
.desc {
  font-size: 13px;
  color: var(--text-muted);
  min-height: 40px;
}
.meta {
  display: flex;
  flex-wrap: wrap;
  gap: 4px 14px;
  font-size: 12.5px;
  color: var(--ink-500);
  margin-top: 2px;
}
.meta-item { display: inline-flex; align-items: center; gap: 5px; }
.foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--sp-3);
  margin-top: auto;
  padding-top: var(--sp-3);
  border-top: 1px dashed var(--border);
}
.countdown {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 12.5px;
  font-weight: 600;
  color: var(--ink-500);
  font-variant-numeric: tabular-nums;
}
.countdown.is-live { color: var(--success-600); }
.cta {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  font-weight: 650;
  color: var(--ink-500);
}
.cta.is-live { color: var(--brand-700); }
.limits { margin-top: 2px; }
</style>
