<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import AppIcon from '@/components/AppIcon.vue'
import AppModal from '@/components/AppModal.vue'
import EmptyState from '@/components/EmptyState.vue'
import LoadingBlock from '@/components/LoadingBlock.vue'
import PaginationBar from '@/components/PaginationBar.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import { winningApi } from '@/api'
import { useRouter } from '@/router'
import { useToastStore } from '@/stores/toast'
import { PRIZE_TYPE, REDEMPTION_STATUS } from '@/utils/constants'
import { formatDateTime, initial } from '@/utils/format'

const router = useRouter()
const toast = useToastStore()

const items = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const loading = ref(true)
const error = ref('')
const filter = ref('all')
const submitting = ref(false)

const claimTarget = ref(null)
const claimOpen = ref(false)
const form = reactive({
  recipient_name: '',
  recipient_phone: '',
  recipient_address: '',
  redemption_code: '',
})
const errors = reactive({})

const FILTERS = [
  { key: 'all', label: '全部' },
  { key: 'pending', label: '待填写' },
  { key: 'submitted', label: '已提交' },
  { key: 'completed', label: '已发放' },
]

const filtered = computed(() =>
  filter.value === 'all' ? items.value : items.value.filter((w) => w.redemption_status === filter.value),
)

const isPhysical = computed(() => claimTarget.value?.prize_type === 'physical')

const expired = (win) => Boolean(win.expire_at) && new Date(win.expire_at) < new Date()

async function load() {
  loading.value = true
  error.value = ''
  try {
    const data = await winningApi.mine({ page: page.value, page_size: pageSize.value })
    items.value = data?.items || []
    total.value = data?.total || 0
  } catch (err) {
    error.value = err?.message || '加载失败'
  } finally {
    loading.value = false
  }
}

function changePage(next) {
  page.value = next
  load()
}

function openClaim(win) {
  claimTarget.value = win
  form.recipient_name = win.recipient_name || ''
  form.recipient_phone = win.recipient_phone || ''
  form.recipient_address = win.recipient_address || ''
  form.redemption_code = win.redemption_code || ''
  Object.keys(errors).forEach((key) => delete errors[key])
  claimOpen.value = true
}

function validate() {
  Object.keys(errors).forEach((key) => delete errors[key])
  if (isPhysical.value && !form.recipient_name.trim()) errors.recipient_name = '请填写收货人姓名'
  if (!form.recipient_phone.trim()) errors.recipient_phone = '请填写领奖手机号'
  else if (!/^1[3-9]\d{9}$/.test(form.recipient_phone.trim())) {
    errors.recipient_phone = '请输入有效的 11 位手机号'
  }
  if (isPhysical.value && !form.recipient_address.trim()) errors.recipient_address = '请填写收货地址'
  return !Object.keys(errors).length
}

async function submitClaim() {
  if (!validate()) return
  submitting.value = true
  try {
    const payload = {
      recipient_phone: form.recipient_phone.trim(),
      redemption_code: form.redemption_code.trim() || null,
    }
    if (isPhysical.value) {
      payload.recipient_name = form.recipient_name.trim()
      payload.recipient_address = form.recipient_address.trim()
    }
    await winningApi.claim(claimTarget.value.id, payload)
    toast.success('领奖信息已提交，请等待运营发放')
    claimOpen.value = false
    load()
  } catch (err) {
    if (err?.message === '兑换码不正确') {
      errors.redemption_code = err.message
    } else {
      toast.fromError(err, '提交失败')
    }
  } finally {
    submitting.value = false
  }
}

async function copy(text, label = '已复制') {
  if (!text) return
  try {
    await navigator.clipboard.writeText(String(text))
    toast.success(label)
  } catch {
    toast.warning('当前环境不支持自动复制，请手动选择复制')
  }
}

onMounted(load)
</script>

<template>
  <div class="page">
    <div class="container">
      <div class="row-between wrap mb-5">
        <div>
          <h1 class="page-title">我的奖品</h1>
          <p class="page-subtitle">中奖后提交收货信息，运营人员会尽快安排发放</p>
        </div>
        <button class="btn" type="button" @click="load">
          <AppIcon name="refresh" :size="15" />
          刷新
        </button>
      </div>

      <div class="chips mb-5">
        <button
          v-for="item in FILTERS"
          :key="item.key"
          class="chip"
          :class="{ 'is-active': filter === item.key }"
          type="button"
          @click="filter = item.key"
        >
          {{ item.label }}
        </button>
      </div>

      <LoadingBlock v-if="loading" />

      <div v-else-if="error" class="alert alert-danger">
        <AppIcon class="alert-icon" name="alert" :size="16" />
        <div class="grow">
          <p class="strong">加载失败</p>
          <p>{{ error }}</p>
        </div>
        <button class="btn btn-sm" type="button" @click="load">重试</button>
      </div>

      <div v-else-if="!filtered.length" class="card">
        <EmptyState icon="trophy" title="还没有中奖记录" desc="好运正在路上，去活动广场试试手气">
          <button class="btn btn-primary" type="button" @click="router.push('/')">去抽奖</button>
        </EmptyState>
      </div>

      <div v-else class="win-list">
        <article v-for="win in filtered" :key="win.id" class="win-card card">
          <div class="thumb">
            <img v-if="win.prize_image" :src="win.prize_image" :alt="win.prize_name" />
            <div v-else class="thumb-fallback">
              <AppIcon name="trophy" :size="26" />
            </div>
          </div>

          <div class="win-body">
            <div class="row wrap gap-2">
              <h3 class="win-name">{{ win.prize_name }}</h3>
              <StatusBadge :map="REDEMPTION_STATUS" :value="win.redemption_status" />
              <StatusBadge :map="PRIZE_TYPE" :value="win.prize_type" />
            </div>

            <div class="win-meta">
              <span class="meta-item">
                <AppIcon name="sparkles" :size="13" />
                {{ win.activity_name || `活动 #${win.activity_id}` }}
              </span>
              <span class="meta-item">
                <AppIcon name="clock" :size="13" />
                中奖于 {{ formatDateTime(win.created_at) }}
              </span>
              <span class="meta-item">
                <AppIcon name="ticket" :size="13" />
                <span class="mono">{{ win.order_no }}</span>
              </span>
            </div>

            <div class="win-info">
              <div class="kv">
                <span class="kv-key">兑换码</span>
                <span class="kv-val">
                  <template v-if="win.redemption_code">
                    <span class="mono">{{ win.redemption_code }}</span>
                    <button class="btn btn-sm btn-ghost" type="button" @click="copy(win.redemption_code, '兑换码已复制')">
                      复制
                    </button>
                  </template>
                  <template v-else>—</template>
                </span>
              </div>
              <div class="kv">
                <span class="kv-key">领取有效期</span>
                <span class="kv-val" :class="{ 'is-expired': expired(win) }">
                  {{ win.expire_at ? formatDateTime(win.expire_at) : '长期有效' }}
                  <template v-if="expired(win)">（已过期）</template>
                </span>
              </div>
              <template v-if="win.recipient_phone">
                <div class="kv">
                  <span class="kv-key">领奖手机号</span>
                  <span class="kv-val">{{ win.recipient_phone }}</span>
                </div>
              </template>
              <template v-if="win.recipient_address">
                <div class="kv kv-address">
                  <span class="kv-key">收货地址</span>
                  <span class="kv-val">{{ win.recipient_address }}</span>
                </div>
              </template>
              <template v-if="win.process_remark">
                <div class="kv">
                  <span class="kv-key">处理备注</span>
                  <span class="kv-val">{{ win.process_remark }}</span>
                </div>
              </template>
            </div>

            <div class="win-actions">
              <button
                v-if="win.redemption_status === 'pending'"
                class="btn btn-primary btn-sm"
                type="button"
                :disabled="expired(win)"
                @click="openClaim(win)"
              >
                <AppIcon name="clipboard" :size="14" />
                {{ expired(win) ? '已过期' : '提交领奖信息' }}
              </button>
              <button
                v-else
                class="btn btn-sm"
                type="button"
                @click="openClaim(win)"
              >
                <AppIcon name="eye" :size="14" />
                查看领奖信息
              </button>
            </div>
          </div>
        </article>
      </div>

      <PaginationBar
        v-if="!loading && total > 0"
        :page="page"
        :page-size="pageSize"
        :total="total"
        @update:page="changePage"
      />
    </div>

    <!-- 领奖信息表单 -->
    <AppModal
      v-model="claimOpen"
      :title="claimTarget?.redemption_status === 'pending' ? '提交领奖信息' : '领奖信息'"
      :desc="
        isPhysical
          ? '实物奖品需要收货人、手机号与详细地址'
          : '虚拟奖品仅需填写领奖手机号'
      "
    >
      <div v-if="claimTarget" class="claim-prize">
        <img v-if="claimTarget.prize_image" class="claim-thumb" :src="claimTarget.prize_image" alt="" />
        <span v-else class="claim-thumb avatar">{{ initial(claimTarget.prize_name) }}</span>
        <div class="grow">
          <p class="strong">{{ claimTarget.prize_name }}</p>
          <p class="text-xs text-muted">
            {{ claimTarget.activity_name || `活动 #${claimTarget.activity_id}` }} ·
            <span class="mono">{{ claimTarget.order_no }}</span>
          </p>
        </div>
      </div>

      <div class="stack-sm mt-4">
        <div v-if="isPhysical" class="field">
          <label class="field-label" for="recipient_name">收货人<span class="req">*</span></label>
          <input
            id="recipient_name"
            v-model="form.recipient_name"
            class="input"
            :class="{ 'is-invalid': errors.recipient_name }"
            :disabled="claimTarget?.redemption_status !== 'pending'"
            placeholder="请输入真实姓名"
          />
          <p v-if="errors.recipient_name" class="field-error">{{ errors.recipient_name }}</p>
        </div>

        <div class="field">
          <label class="field-label" for="recipient_phone">领奖手机号<span class="req">*</span></label>
          <input
            id="recipient_phone"
            v-model="form.recipient_phone"
            class="input"
            :class="{ 'is-invalid': errors.recipient_phone }"
            :disabled="claimTarget?.redemption_status !== 'pending'"
            inputmode="numeric"
            maxlength="11"
            placeholder="11 位手机号"
          />
          <p v-if="errors.recipient_phone" class="field-error">{{ errors.recipient_phone }}</p>
        </div>

        <div v-if="isPhysical" class="field">
          <label class="field-label" for="recipient_address">收货地址<span class="req">*</span></label>
          <textarea
            id="recipient_address"
            v-model="form.recipient_address"
            class="textarea"
            :class="{ 'is-invalid': errors.recipient_address }"
            :disabled="claimTarget?.redemption_status !== 'pending'"
            placeholder="省 / 市 / 区 + 详细地址"
          />
          <p v-if="errors.recipient_address" class="field-error">{{ errors.recipient_address }}</p>
        </div>

        <div class="field">
          <label class="field-label" for="redemption_code">兑换码</label>
          <input
            id="redemption_code"
            v-model="form.redemption_code"
            class="input mono"
            :class="{ 'is-invalid': errors.redemption_code }"
            :disabled="claimTarget?.redemption_status !== 'pending'"
            placeholder="中奖记录上的兑换码"
            @input="errors.redemption_code = ''"
          />
          <p v-if="errors.redemption_code" class="field-error">{{ errors.redemption_code }}</p>
        </div>
      </div>

      <template #footer>
        <button class="btn" type="button" @click="claimOpen = false">
          {{ claimTarget?.redemption_status === 'pending' ? '取消' : '关闭' }}
        </button>
        <button
          v-if="claimTarget?.redemption_status === 'pending'"
          class="btn btn-primary"
          type="button"
          :disabled="submitting"
          @click="submitClaim"
        >
          <span v-if="submitting" class="spinner spinner-light" />
          {{ submitting ? '提交中…' : '确认提交' }}
        </button>
      </template>
    </AppModal>
  </div>
</template>

<style scoped>
.win-list { display: flex; flex-direction: column; gap: var(--sp-4); }
.win-card {
  display: grid;
  grid-template-columns: 116px minmax(0, 1fr);
  gap: var(--sp-5);
  padding: var(--sp-4);
  transition: border-color var(--dur) var(--ease), box-shadow var(--dur) var(--ease);
}
.win-card:hover { border-color: var(--brand-200); box-shadow: var(--shadow-sm); }
.thumb {
  border-radius: var(--radius);
  overflow: hidden;
  background: linear-gradient(160deg, var(--gold-100), var(--surface-3));
  aspect-ratio: 1;
}
.thumb img { width: 100%; height: 100%; object-fit: cover; }
.thumb-fallback { width: 100%; height: 100%; display: grid; place-items: center; color: var(--gold-600); }

.win-body { display: flex; flex-direction: column; gap: 8px; min-width: 0; }
.win-name { font-size: 16px; font-weight: 700; }
.win-meta { display: flex; flex-wrap: wrap; gap: 4px 14px; font-size: 12.5px; color: var(--ink-500); }
.meta-item { display: inline-flex; align-items: center; gap: 5px; }
.win-info {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px 24px;
  padding: 16px 18px;
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: var(--radius);
}
.win-info .kv {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  justify-content: center;
  gap: 5px;
  min-width: 0;
  padding: 0;
}
.win-info .kv-key { font-size: 12px; color: var(--ink-500); }
.win-info .kv-val {
  display: inline-flex;
  align-items: center;
  justify-content: flex-start;
  flex-wrap: wrap;
  gap: 6px;
  min-width: 0;
  max-width: 100%;
  text-align: left;
  overflow-wrap: anywhere;
}
.win-info .kv-address {
  grid-column: 1 / -1;
  display: grid;
  grid-template-columns: 84px minmax(0, 1fr);
  align-items: start;
  gap: 14px;
  padding-top: 12px;
  border-top: 1px solid var(--border);
}
.win-info .kv-address .kv-val {
  display: block;
  line-height: 1.6;
  white-space: normal;
}
.kv-val.is-expired { color: var(--danger-600); }
.win-actions { display: flex; gap: var(--sp-2); margin-top: 2px; }

.claim-prize {
  display: flex;
  align-items: center;
  gap: var(--sp-4);
  padding: var(--sp-3);
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: var(--radius);
}
.claim-thumb { width: 52px; height: 52px; border-radius: var(--radius-sm); object-fit: cover; }

@media (max-width: 640px) {
  .win-card { grid-template-columns: minmax(0, 1fr); }
  .thumb { aspect-ratio: 16 / 9; }
  .win-info { grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px 16px; }
  .win-info .kv-address { grid-template-columns: 1fr; gap: 5px; }
}
</style>
