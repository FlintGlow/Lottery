<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import AppIcon from '@/components/AppIcon.vue'
import EmptyState from '@/components/EmptyState.vue'
import LoadingBlock from '@/components/LoadingBlock.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import { activityApi, statisticsApi } from '@/api'
import { useToastStore } from '@/stores/toast'
import { ACTIVITY_STATUS, REDEMPTION_STATUS } from '@/utils/constants'
import { formatDateTime, formatNumber, formatPercent } from '@/utils/format'

const toast = useToastStore()

const activities = ref([])
const selectedId = ref('')
const stats = ref(null)
const loading = ref(false)
const bootstrapping = ref(true)

const selected = computed(() => activities.value.find((a) => a.id === Number(selectedId.value)))

const cards = computed(() => {
  const s = stats.value
  if (!s) return []
  return [
    { label: '参与人数', value: formatNumber(s.participant_count), icon: 'users', tone: 'brand' },
    { label: '抽奖次数', value: formatNumber(s.draw_count), icon: 'ticket', tone: '' },
    { label: '中奖次数', value: formatNumber(s.win_count), icon: 'trophy', tone: 'gold' },
    { label: '未中奖次数', value: formatNumber(s.no_prize_count), icon: 'inbox', tone: '' },
    { label: '中奖率', value: formatPercent(s.win_rate), icon: 'chart', tone: 'brand' },
  ]
})

const claimRows = computed(() => {
  const map = stats.value?.claim_stats || {}
  const total = Object.values(map).reduce((sum, n) => sum + Number(n || 0), 0)
  return Object.entries(map).map(([key, count]) => ({
    key,
    label: REDEMPTION_STATUS[key]?.label || key,
    cls: REDEMPTION_STATUS[key]?.cls || 'st-neutral',
    count: Number(count || 0),
    percent: total ? Math.round((Number(count || 0) / total) * 100) : 0,
  }))
})

const prizeRows = computed(() => stats.value?.prize_stats || [])

async function loadActivities() {
  bootstrapping.value = true
  try {
    const data = await activityApi.list({ page: 1, page_size: 100 })
    activities.value = data?.items || []
    if (activities.value.length && !selectedId.value) {
      const ongoing = activities.value.find((a) => a.status === 'ongoing')
      selectedId.value = String(ongoing?.id ?? activities.value[0].id)
    }
  } catch (err) {
    toast.fromError(err, '活动列表加载失败')
  } finally {
    bootstrapping.value = false
  }
}

async function loadStats() {
  if (!selectedId.value) {
    stats.value = null
    return
  }
  loading.value = true
  try {
    stats.value = await statisticsApi.activity(Number(selectedId.value))
  } catch (err) {
    stats.value = null
    toast.fromError(err, '统计数据加载失败')
  } finally {
    loading.value = false
  }
}

watch(selectedId, loadStats)

onMounted(async () => {
  await loadActivities()
  await loadStats()
})
</script>

<template>
  <div class="dash">
    <div class="row-between wrap mb-5 gap-4">
      <div class="toolbar">
        <select v-model="selectedId" class="select" style="min-width: 240px" :disabled="bootstrapping">
          <option value="">请选择活动</option>
          <option v-for="item in activities" :key="item.id" :value="item.id">
            {{ item.name }}
          </option>
        </select>
        <button class="btn" type="button" :disabled="!selectedId || loading" @click="loadStats">
          <AppIcon name="refresh" :size="15" />
          刷新
        </button>
      </div>
      <div v-if="selected" class="row gap-2 wrap">
        <StatusBadge :map="ACTIVITY_STATUS" :value="selected.status" size="lg" />
        <span class="text-xs text-muted">
          {{ formatDateTime(selected.start_time) }} ~ {{ formatDateTime(selected.end_time) }}
        </span>
      </div>
    </div>

    <LoadingBlock v-if="bootstrapping" text="正在加载活动…" />

    <div v-else-if="!activities.length" class="card">
      <EmptyState
        icon="sparkles"
        title="还没有活动"
        desc="先到「活动管理」创建一个活动，再回来查看统计数据"
      />
    </div>

    <LoadingBlock v-else-if="loading" text="正在统计…" />

    <template v-else-if="stats">
      <!-- 指标卡 -->
      <div class="grid grid-4">
        <div v-for="card in cards" :key="card.label" class="stat">
          <div class="row-between">
            <span class="stat-label">{{ card.label }}</span>
            <span class="stat-icon" :class="card.tone ? `is-${card.tone}` : ''">
              <AppIcon :name="card.icon" :size="15" />
            </span>
          </div>
          <p
            class="stat-value"
            :class="card.tone === 'gold' ? 'stat-gold' : card.tone === 'brand' ? 'stat-accent' : ''"
          >
            {{ card.value }}
          </p>
        </div>
      </div>

      <div class="grid grid-2 mt-5">
        <!-- 奖品统计 -->
        <section class="card">
          <div class="card-head">
            <h2 class="section-title">奖品中出情况</h2>
            <span class="text-xs text-muted">{{ prizeRows.length }} 个奖品</span>
          </div>
          <div v-if="!prizeRows.length" class="table-empty">该活动还没有配置奖品</div>
          <div v-else class="table-wrap">
            <table class="table">
              <thead>
                <tr>
                  <th>奖品</th>
                  <th>类型</th>
                  <th class="right">库存</th>
                  <th class="right">已中出</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in prizeRows" :key="row.prize_id">
                  <td>
                    <span class="strong">{{ row.prize_name }}</span>
                  </td>
                  <td>
                    <span class="tag">{{ row.prize_type === 'physical' ? '实物' : '虚拟' }}</span>
                  </td>
                  <td class="right nowrap">
                    <span class="strong">{{ row.remain_stock }}</span>
                    <span class="text-soft"> / {{ row.total_stock }}</span>
                  </td>
                  <td class="right strong">{{ row.drawn_count }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

        <!-- 领奖分布 -->
        <section class="card">
          <div class="card-head">
            <h2 class="section-title">领奖状态分布</h2>
          </div>
          <div v-if="!claimRows.length" class="table-empty">暂无中奖记录</div>
          <div v-else class="card-body stack-sm">
            <div v-for="row in claimRows" :key="row.key" class="claim-row">
              <div class="row-between">
                <span class="badge" :class="row.cls">{{ row.label }}</span>
                <span class="text-sm">
                  <strong>{{ row.count }}</strong>
                  <span class="text-soft"> · {{ row.percent }}%</span>
                </span>
              </div>
              <div class="progress mt-2">
                <div class="progress-bar" :style="{ width: `${row.percent}%` }" />
              </div>
            </div>
            <p class="text-xs text-soft mt-2">
              数量为 0 的状态不会出现在统计结果中，属正常现象。
            </p>
          </div>
        </section>
      </div>

      <!-- 活动信息 -->
      <section v-if="selected" class="card card-pad mt-5">
        <h2 class="section-title mb-4">活动配置</h2>
        <div class="config-grid">
          <div class="kv">
            <span class="kv-key">活动 ID</span>
            <span class="kv-val mono">{{ selected.id }}</span>
          </div>
          <div class="kv">
            <span class="kv-key">活动总次数上限</span>
            <span class="kv-val">{{ selected.total_draw_limit || '不限' }}</span>
          </div>
          <div class="kv">
            <span class="kv-key">每人每日次数</span>
            <span class="kv-val">{{ selected.daily_draw_limit || '不限' }}</span>
          </div>
          <div class="kv">
            <span class="kv-key">未中奖权重</span>
            <span class="kv-val">{{ selected.rule_config?.none_weight ?? 1000 }}</span>
          </div>
          <div class="kv">
            <span class="kv-key">创建人</span>
            <span class="kv-val">{{ stats.created_by_name || '—' }}</span>
          </div>
          <div class="kv">
            <span class="kv-key">发布时间</span>
            <span class="kv-val">{{ selected.published_at ? formatDateTime(selected.published_at) : '未发布' }}</span>
          </div>
        </div>
      </section>
    </template>

    <div v-else class="card">
      <EmptyState icon="chart" title="暂无统计数据" desc="请选择一个活动" />
    </div>
  </div>
</template>

<style scoped>
.stat-icon {
  display: grid;
  place-items: center;
  width: 28px;
  height: 28px;
  border-radius: 9px;
  background: var(--ink-100);
  color: var(--ink-500);
}
.stat-icon.is-brand { background: var(--brand-50); color: var(--brand-700); }
.stat-icon.is-gold { background: var(--gold-100); color: var(--gold-700); }
.claim-row + .claim-row { margin-top: var(--sp-2); }
.config-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(230px, 1fr));
  gap: 0 var(--sp-6);
}
</style>
