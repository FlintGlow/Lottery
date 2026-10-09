<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import AppIcon from '@/components/AppIcon.vue'
import EmptyState from '@/components/EmptyState.vue'
import LoadingBlock from '@/components/LoadingBlock.vue'
import PaginationBar from '@/components/PaginationBar.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import { activityApi, lotteryApi } from '@/api'
import { useRouter } from '@/router'
import { useToastStore } from '@/stores/toast'
import { ADMIN_PAGE_SIZE, DRAW_STATUS } from '@/utils/constants'
import { formatDateTime } from '@/utils/format'

const router = useRouter()
const toast = useToastStore()

const records = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(ADMIN_PAGE_SIZE)
const activityId = ref('')
const activities = ref([])
const loading = ref(true)
const error = ref('')
const expanded = ref(null)

let autoTimer = null

const hasPending = computed(() => records.value.some((item) => item.status === 'pending'))

const activityName = (id) => activities.value.find((a) => a.id === id)?.name || `活动 #${id}`

async function loadActivities() {
  try {
    const list = await activityApi.listPublic()
    activities.value = Array.isArray(list) ? list : []
  } catch {
    activities.value = []
  }
}

async function load(silent = false) {
  if (!silent) loading.value = true
  error.value = ''
  try {
    const data = await lotteryApi.myRecords({
      page: page.value,
      page_size: pageSize.value,
      activity_id: activityId.value || undefined,
    })
    records.value = data?.items || []
    total.value = data?.total || 0
  } catch (err) {
    error.value = err?.message || '记录加载失败'
  } finally {
    loading.value = false
    scheduleAuto()
  }
}

/** 有未落库的记录时自动轮询刷新 */
function scheduleAuto() {
  clearTimeout(autoTimer)
  if (!hasPending.value) return
  autoTimer = setTimeout(() => load(true), 3000)
}

function changePage(next) {
  page.value = next
  load()
}

function changeActivity() {
  page.value = 1
  load()
}

function toggle(orderNo) {
  expanded.value = expanded.value === orderNo ? null : orderNo
}

function detailOf(record) {
  const json = record?.result_json || {}
  return {
    prize: json.prize_name || '',
    level: json.level || '',
    ip: json.ip || '',
    drawAt: json.draw_at || '',
    prizeId: record?.prize_id,
  }
}

onMounted(async () => {
  await loadActivities()
  await load()
})

onBeforeUnmount(() => clearTimeout(autoTimer))
</script>

<template>
  <div class="page">
    <div class="container">
      <div class="row-between wrap mb-5">
        <div>
          <h1 class="page-title">我的抽奖记录</h1>
          <p class="page-subtitle">每次抽奖的流水号与开奖结果，处理中的记录会自动刷新</p>
        </div>
        <div class="toolbar">
          <select v-model="activityId" class="select" @change="changeActivity">
            <option value="">全部活动</option>
            <option v-for="item in activities" :key="item.id" :value="item.id">
              {{ item.name }}
            </option>
          </select>
          <button class="btn" type="button" @click="load()">
            <AppIcon name="refresh" :size="15" />
            刷新
          </button>
        </div>
      </div>

      <div v-if="hasPending" class="alert alert-info mb-4">
        <AppIcon class="alert-icon" name="clock" :size="16" />
        <span>存在正在处理的抽奖记录，页面每 3 秒自动刷新一次结果。</span>
      </div>

      <LoadingBlock v-if="loading" />

      <div v-else-if="error" class="alert alert-danger">
        <AppIcon class="alert-icon" name="alert" :size="16" />
        <div class="grow">
          <p class="strong">加载失败</p>
          <p>{{ error }}</p>
        </div>
        <button class="btn btn-sm" type="button" @click="load()">重试</button>
      </div>

      <div v-else-if="!records.length" class="card">
        <EmptyState icon="ticket" title="还没有抽奖记录" desc="去活动广场参与一次抽奖吧">
          <button class="btn btn-primary" type="button" @click="router.push('/')">
            去抽奖
          </button>
        </EmptyState>
      </div>

      <template v-else>
        <div class="card table-wrap">
          <table class="table">
            <thead>
              <tr>
                <th>流水号</th>
                <th>活动</th>
                <th>状态</th>
                <th>结果</th>
                <th>抽奖时间</th>
                <th class="right">操作</th>
              </tr>
            </thead>
            <tbody>
              <template v-for="record in records" :key="record.order_no">
                <tr>
                  <td>
                    <span class="mono">{{ record.order_no }}</span>
                  </td>
                  <td>{{ activityName(record.activity_id) }}</td>
                  <td><StatusBadge :map="DRAW_STATUS" :value="record.status" /></td>
                  <td>
                    <span v-if="record.status === 'won'" class="won-text">
                      <AppIcon name="trophy" :size="14" />
                      {{ detailOf(record).prize || '已中奖' }}
                    </span>
                    <span v-else-if="record.error_message" class="text-xs text-muted">
                      {{ record.error_message }}
                    </span>
                    <span v-else class="text-muted">—</span>
                  </td>
                  <td class="nowrap">{{ formatDateTime(record.created_at, true) }}</td>
                  <td>
                    <div class="cell-actions">
                      <button class="btn btn-sm btn-ghost" type="button" @click="toggle(record.order_no)">
                        {{ expanded === record.order_no ? '收起' : '详情' }}
                      </button>
                      <button
                        v-if="record.win_id"
                        class="btn btn-sm btn-soft"
                        type="button"
                        @click="router.push('/winnings')"
                      >
                        去领奖
                      </button>
                    </div>
                  </td>
                </tr>
                <tr v-if="expanded === record.order_no" class="detail-row">
                  <td colspan="6">
                    <div class="detail-grid">
                      <div class="kv">
                        <span class="kv-key">订单号</span>
                        <span class="kv-val mono">{{ record.order_no }}</span>
                      </div>
                      <div class="kv">
                        <span class="kv-key">奖品编号</span>
                        <span class="kv-val">{{ detailOf(record).prizeId ?? '—' }}</span>
                      </div>
                      <div class="kv">
                        <span class="kv-key">奖品等级</span>
                        <span class="kv-val">{{ detailOf(record).level || '—' }}</span>
                      </div>
                      <div class="kv">
                        <span class="kv-key">中奖记录 ID</span>
                        <span class="kv-val">{{ record.win_id ?? '—' }}</span>
                      </div>
                      <div class="kv">
                        <span class="kv-key">抽奖 IP</span>
                        <span class="kv-val">{{ detailOf(record).ip || '—' }}</span>
                      </div>
                      <div class="kv">
                        <span class="kv-key">失败原因</span>
                        <span class="kv-val">{{ record.error_message || '—' }}</span>
                      </div>
                    </div>
                  </td>
                </tr>
              </template>
            </tbody>
          </table>
        </div>

        <PaginationBar
          :page="page"
          :page-size="pageSize"
          :total="total"
          @update:page="changePage"
        />
      </template>
    </div>
  </div>
</template>

<style scoped>
.won-text {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  color: var(--gold-600);
  font-weight: 650;
}
.detail-row td {
  background: var(--surface-2);
  padding: var(--sp-4) var(--sp-5);
}
.detail-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(230px, 1fr));
  gap: 0 var(--sp-6);
}
</style>
