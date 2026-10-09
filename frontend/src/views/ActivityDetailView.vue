<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import AppIcon from '@/components/AppIcon.vue'
import AppModal from '@/components/AppModal.vue'
import EmptyState from '@/components/EmptyState.vue'
import LoadingBlock from '@/components/LoadingBlock.vue'
import PrizeCard from '@/components/PrizeCard.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import { activityApi, lotteryApi, prizeApi } from '@/api'
import { useRoute, useRouter } from '@/router'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'
import { ACTIVITY_STATUS, DRAW_STATUS } from '@/utils/constants'
import { countdownParts, formatDateTime } from '@/utils/format'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const toast = useToastStore()

const activityId = computed(() => Number(route.params.id))

const activity = ref(null)
const prizes = ref([])
const loading = ref(true)
const error = ref('')

const drawing = ref(false)
const resultOpen = ref(false)
const phase = ref('idle') // idle | processing | won | no_prize | failed | refunded | error
const result = ref(null)
const resultMessage = ref('')

const now = ref(Date.now())
let clock = null
let pollTimer = null
let pollCount = 0

const status = computed(() => activity.value?.status)
const canDraw = computed(() => status.value === 'ongoing')

const countdown = computed(() => {
  if (!activity.value) return ''
  if (status.value === 'pending') return text(countdownParts(activity.value.start_time, now.value))
  if (status.value === 'ongoing') return text(countdownParts(activity.value.end_time, now.value))
  return ''
})

function text(parts) {
  if (!parts || parts.past) return ''
  if (parts.day > 0) return `${parts.day} 天 ${parts.hour} 小时 ${parts.min} 分`
  if (parts.hour > 0) return `${parts.hour} 时 ${parts.min} 分 ${parts.sec} 秒`
  return `${parts.min} 分 ${parts.sec} 秒`
}

const limits = computed(() => {
  const a = activity.value
  if (!a) return []
  const list = []
  if (a.total_draw_limit > 0) list.push({ label: '活动总次数', value: `${a.total_draw_limit} 次` })
  else list.push({ label: '活动总次数', value: '不限' })
  if (a.daily_draw_limit > 0) list.push({ label: '每人每日', value: `${a.daily_draw_limit} 次` })
  else list.push({ label: '每人每日', value: '不限' })
  return list
})

const ruleConfig = computed(() => activity.value?.rule_config || {})

const wonPrizeName = computed(
  () => result.value?.result_json?.prize_name || result.value?.prize_name || '',
)

async function load() {
  loading.value = true
  error.value = ''
  try {
    const [detail, prizeList] = await Promise.all([
      activityApi.getPublic(activityId.value),
      prizeApi.listByActivity(activityId.value).catch(() => []),
    ])
    activity.value = detail
    prizes.value = Array.isArray(prizeList) ? prizeList : []
  } catch (err) {
    error.value = err?.message || '活动加载失败'
  } finally {
    loading.value = false
  }
}

async function draw() {
  if (!auth.isLoggedIn) {
    toast.info('请先登录后再抽奖')
    router.push(`/login?redirect=${encodeURIComponent(`/activity/${activityId.value}`)}`)
    return
  }
  if (!canDraw.value) {
    toast.warning(`活动当前不可抽奖（${ACTIVITY_STATUS[status.value]?.label || status.value}）`)
    return
  }

  drawing.value = true
  phase.value = 'processing'
  resultOpen.value = true
  result.value = null
  resultMessage.value = ''
  try {
    const res = await lotteryApi.draw(activityId.value)
    result.value = { order_no: res?.order_no, activity_id: activityId.value }
    pollCount = 0
    poll(res?.order_no)
  } catch (err) {
    phase.value = 'error'
    resultMessage.value = err?.message || '抽奖失败，请稍后重试'
  } finally {
    drawing.value = false
  }
}

/** 轮询异步开奖结果：消费者落库前记录可能还未创建，404 视为仍在处理中 */
function poll(orderNo) {
  if (!orderNo) return
  clearTimeout(pollTimer)
  pollTimer = setTimeout(async () => {
    pollCount += 1
    let settled = false
    try {
      const record = await lotteryApi.recordByOrderNo(orderNo)
      applyResult(record)
      settled = Boolean(record) && record.status !== 'pending'
    } catch (err) {
      if (err?.status !== 404) {
        phase.value = 'error'
        resultMessage.value = err?.message || '结果查询失败'
        return
      }
    }
    if (!resultOpen.value) return
    if (!settled) {
      if (pollCount >= 20) {
        resultMessage.value = '结果仍在处理中，系统会继续查询；也可以关闭后到「我的记录」查看。'
      }
      poll(orderNo)
    }
  }, pollCount === 0 ? 700 : pollCount < 20 ? 1300 : 10000)
}

function applyResult(record) {
  if (!record) return
  result.value = record
  const st = record.status
  if (st === 'pending') return
  phase.value = st === 'won' ? 'won' : st === 'no_prize' ? 'no_prize' : st
  if (st === 'won') {
    toast.success('恭喜中奖！')
    load()
  }
}

function closeResult() {
  resultOpen.value = false
  clearTimeout(pollTimer)
}

function goWinnings() {
  resultOpen.value = false
  router.push('/winnings')
}

onMounted(() => {
  load()
  clock = setInterval(() => {
    now.value = Date.now()
  }, 1000)
})

onBeforeUnmount(() => {
  clearInterval(clock)
  clearTimeout(pollTimer)
})
</script>

<template>
  <div class="page">
    <div class="container">
      <button class="back" type="button" @click="router.push('/')">
        <AppIcon name="chevronLeft" :size="15" />
        返回活动列表
      </button>

      <LoadingBlock v-if="loading" text="正在加载活动…" min-height="380px" />

      <div v-else-if="error" class="alert alert-danger mt-4">
        <AppIcon class="alert-icon" name="alert" :size="16" />
        <div class="grow">
          <p class="strong">加载失败</p>
          <p>{{ error }}</p>
        </div>
        <button class="btn btn-sm" type="button" @click="load">重试</button>
      </div>

      <template v-else-if="activity">
        <!-- 活动头部 -->
        <header class="detail-head card">
          <div class="cover" :style="activity.cover_url ? {} : {}">
            <img v-if="activity.cover_url" :src="activity.cover_url" :alt="activity.name" />
            <div v-else class="cover-fallback"><AppIcon name="gift" :size="46" /></div>
          </div>

          <div class="head-body">
            <div class="row wrap gap-2">
              <StatusBadge :map="ACTIVITY_STATUS" :value="status" size="lg" />
              <span v-if="countdown" class="badge badge-plain st-brand">
                <AppIcon name="clock" :size="12" />
                {{ status === 'pending' ? '距开始' : '距结束' }} {{ countdown }}
              </span>
            </div>

            <h1 class="detail-title">{{ activity.name }}</h1>
            <p class="detail-desc">{{ activity.description || '暂无活动描述' }}</p>

            <div class="info-grid">
              <div class="info-item">
                <span class="info-label">活动时间</span>
                <span class="info-value">
                  {{ formatDateTime(activity.start_time) }} ~ {{ formatDateTime(activity.end_time) }}
                </span>
              </div>
              <div v-for="item in limits" :key="item.label" class="info-item">
                <span class="info-label">{{ item.label }}</span>
                <span class="info-value">{{ item.value }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">奖品数量</span>
                <span class="info-value">{{ prizes.length }} 件</span>
              </div>
            </div>

            <div class="head-actions">
              <button
                class="btn btn-lg btn-gold draw-btn"
                type="button"
                :disabled="!canDraw || drawing"
                @click="draw"
              >
                <AppIcon :name="drawing ? 'refresh' : 'sparkles'" :size="18" />
                {{ drawing ? '抽奖中…' : canDraw ? '立即抽奖' : ACTIVITY_STATUS[status]?.label }}
              </button>
              <button
                v-if="auth.isLoggedIn"
                class="btn btn-lg"
                type="button"
                @click="router.push('/records')"
              >
                <AppIcon name="ticket" :size="16" />
                我的记录
              </button>
            </div>

            <p v-if="!canDraw && ACTIVITY_STATUS[status]?.desc" class="text-xs text-soft mt-3">
              {{ ACTIVITY_STATUS[status].desc }}
            </p>
            <p v-else-if="canDraw" class="text-xs text-soft mt-3">
              点击抽奖后系统会先预扣库存，开奖结果通常 1–3 秒内返回。
            </p>
          </div>
        </header>

        <!-- 活动规则 -->
        <section v-if="ruleConfig && Object.keys(ruleConfig).length" class="card card-pad mt-5">
          <h2 class="section-title">活动说明</h2>
          <ul class="rules">
            <li v-if="ruleConfig.need_phone">
              <AppIcon name="phone" :size="15" /> 参与需绑定手机号
            </li>
            <li v-if="ruleConfig.need_name">
              <AppIcon name="user" :size="15" /> 领奖需填写真实姓名
            </li>
            <li v-if="ruleConfig.announcement">
              <AppIcon name="info" :size="15" /> {{ ruleConfig.announcement }}
            </li>
          </ul>
        </section>

        <!-- 奖品 -->
        <section class="mt-6">
          <div class="row-between mb-4">
            <h2 class="section-title">奖品池</h2>
            <span class="text-sm text-muted">共 {{ prizes.length }} 件</span>
          </div>

          <div v-if="!prizes.length" class="card">
            <EmptyState icon="gift" title="暂无奖品" desc="活动还没有配置奖品，请稍后再来" />
          </div>

          <div v-else class="grid grid-prizes">
            <PrizeCard v-for="prize in prizes" :key="prize.id" :prize="prize" />
          </div>
        </section>
      </template>
    </div>

    <!-- 抽奖结果 -->
    <AppModal
      v-model="resultOpen"
      :title="phase === 'processing' ? '开奖中' : phase === 'won' ? '恭喜中奖' : '抽奖结果'"
      :desc="phase === 'processing' ? '正在为你揭晓结果，请稍候…' : ''"
      size="sm"
      :close-on-mask="phase !== 'processing'"
      @update:model-value="(v) => !v && closeResult()"
    >
      <div class="result">
        <!-- 处理中 -->
        <template v-if="phase === 'processing'">
          <div class="result-visual is-loading">
            <span class="spinner" style="width: 34px; height: 34px; border-width: 3px" />
          </div>
          <p class="result-text">正在开奖…</p>
          <p class="text-xs text-muted">订单号 {{ result?.order_no || '-' }}</p>
          <p v-if="resultMessage" class="text-xs text-muted mt-2">{{ resultMessage }}</p>
        </template>

        <!-- 中奖 -->
        <template v-else-if="phase === 'won'">
          <div class="result-visual is-won">
            <AppIcon name="trophy" :size="42" />
            <span class="burst" aria-hidden="true" />
          </div>
          <p class="result-text strong">恭喜你抽中</p>
          <p class="prize-name">{{ wonPrizeName || '奖品' }}</p>
          <p class="text-xs text-muted">订单号 {{ result?.order_no || '-' }}</p>
          <p class="text-xs text-muted mt-2">
            实物奖品请前往「我的奖品」提交收货信息，运营将尽快安排发放。
          </p>
        </template>

        <!-- 未中奖 -->
        <template v-else-if="phase === 'no_prize'">
          <div class="result-visual is-miss">
            <AppIcon name="inbox" :size="38" />
          </div>
          <p class="result-text strong">这次没有中奖</p>
          <p class="text-xs text-muted">不要气馁，再试一次说不定就是你了</p>
        </template>

        <!-- 其他异常态 -->
        <template v-else>
          <div class="result-visual is-miss">
            <AppIcon name="alert" :size="36" />
          </div>
          <p class="result-text strong">
            {{
              phase === 'refunded'
                ? '本次抽奖已作废'
                : phase === 'failed'
                  ? '开奖处理失败'
                  : '抽奖未成功'
            }}
          </p>
          <p class="text-xs text-muted">
            {{
              resultMessage ||
              result?.error_message ||
              '库存已被回补，你可以重新发起抽奖'
            }}
          </p>
        </template>

        <div v-if="result" class="result-status mt-4">
          <span class="kv-key">当前状态</span>
          <StatusBadge :map="DRAW_STATUS" :value="result.status" />
        </div>
      </div>

      <template #footer>
        <button class="btn" type="button" @click="closeResult">
          {{ phase === 'processing' ? '后台查看' : '关闭' }}
        </button>
        <button v-if="phase === 'won'" class="btn btn-primary" type="button" @click="goWinnings">
          <AppIcon name="trophy" :size="15" />
          去领奖
        </button>
        <button
          v-else-if="phase !== 'processing'"
          class="btn btn-primary"
          type="button"
          :disabled="!canDraw"
          @click="closeResult(); draw()"
        >
          再抽一次
        </button>
      </template>
    </AppModal>
  </div>
</template>

<style scoped>
.back {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  border: 0;
  background: transparent;
  color: var(--text-muted);
  font-size: 13.5px;
  cursor: pointer;
  padding: 0;
  margin-bottom: var(--sp-4);
}
.back:hover { color: var(--brand-700); }

.detail-head {
  display: grid;
  grid-template-columns: minmax(0, 320px) minmax(0, 1fr);
  gap: var(--sp-6);
  padding: var(--sp-5);
}
.cover {
  border-radius: var(--radius-lg);
  overflow: hidden;
  background: linear-gradient(150deg, var(--brand-500), var(--brand-900));
  aspect-ratio: 4 / 3;
}
.cover img { width: 100%; height: 100%; object-fit: cover; }
.cover-fallback {
  width: 100%;
  height: 100%;
  display: grid;
  place-items: center;
  color: rgba(255, 255, 255, 0.72);
}
.head-body { display: flex; flex-direction: column; gap: var(--sp-3); min-width: 0; }
.detail-title {
  font-size: clamp(21px, 2.4vw, 27px);
  font-weight: 740;
  letter-spacing: -0.025em;
}
.detail-desc { color: var(--text-muted); font-size: 14px; }

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: var(--sp-3);
  padding: var(--sp-4);
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: var(--radius);
}
.info-item { display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.info-label { font-size: 12px; color: var(--text-soft); }
.info-value { font-size: 13.5px; font-weight: 600; color: var(--ink-800); }

.head-actions { display: flex; gap: var(--sp-3); flex-wrap: wrap; margin-top: auto; }
.draw-btn { min-width: 168px; }

.rules { display: flex; flex-direction: column; gap: 8px; margin-top: var(--sp-3); }
.rules li {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13.5px;
  color: var(--ink-600);
}

/* ---------- 结果弹窗 ---------- */
.result {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: var(--sp-3) 0 var(--sp-2);
}
.result-visual {
  position: relative;
  display: grid;
  place-items: center;
  width: 88px;
  height: 88px;
  border-radius: 50%;
  margin-bottom: var(--sp-4);
}
.result-visual.is-loading { background: var(--brand-50); }
.result-visual.is-won {
  background: linear-gradient(135deg, var(--gold-300), var(--gold-500));
  color: #4a2c00;
  box-shadow: 0 12px 34px rgba(245, 158, 11, 0.4);
  animation: pop-in 0.5s var(--ease-out);
}
.result-visual.is-miss { background: var(--surface-3); color: var(--ink-400); }
.burst {
  position: absolute;
  inset: -12px;
  border-radius: 50%;
  border: 2px solid var(--gold-300);
  animation: burst 1.6s var(--ease-out) infinite;
}
@keyframes burst {
  0% { transform: scale(0.86); opacity: 0.9; }
  100% { transform: scale(1.28); opacity: 0; }
}
@keyframes pop-in {
  0% { transform: scale(0.6); opacity: 0; }
  60% { transform: scale(1.08); }
  100% { transform: scale(1); opacity: 1; }
}
.result-text { font-size: 15px; color: var(--ink-700); }
.prize-name {
  font-size: 20px;
  font-weight: 750;
  color: var(--gold-600);
  margin: 4px 0 8px;
  letter-spacing: -0.02em;
}
.result-status {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--sp-4);
  width: 100%;
  padding-top: var(--sp-4);
  border-top: 1px dashed var(--border);
  font-size: 13px;
}

@media (max-width: 860px) {
  .detail-head { grid-template-columns: minmax(0, 1fr); }
  .cover { aspect-ratio: 16 / 9; }
}
</style>
