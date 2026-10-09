<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import AppIcon from '@/components/AppIcon.vue'
import AppModal from '@/components/AppModal.vue'
import EmptyState from '@/components/EmptyState.vue'
import LoadingBlock from '@/components/LoadingBlock.vue'
import PaginationBar from '@/components/PaginationBar.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import { activityApi, winningApi } from '@/api'
import { useToastStore } from '@/stores/toast'
import { ADMIN_PAGE_SIZE, REDEMPTION_STATUS, REDEMPTION_TRANSITIONS } from '@/utils/constants'
import { formatDateTime, maskPhone } from '@/utils/format'

const toast = useToastStore()

const items = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(ADMIN_PAGE_SIZE)
const filters = reactive({ activity_id: '', status: '', keyword: '' })
const loading = ref(true)
const activities = ref([])

const detailOpen = ref(false)
const current = ref(null)
const nextStatus = ref('')
const remark = ref('')
const saving = ref(false)

const isReadonly = computed(
  () => !current.value || (REDEMPTION_TRANSITIONS[current.value.redemption_status] || []).length === 0,
)

const options = computed(() =>
  current.value ? REDEMPTION_TRANSITIONS[current.value.redemption_status] || [] : [],
)

async function loadActivities() {
  try {
    const data = await activityApi.list({ page: 1, page_size: 100 })
    activities.value = data?.items || []
  } catch {
    activities.value = []
  }
}

async function load() {
  loading.value = true
  try {
    const data = await winningApi.list({
      page: page.value,
      page_size: pageSize.value,
      activity_id: filters.activity_id || undefined,
      status: filters.status || undefined,
      keyword: filters.keyword || undefined,
    })
    items.value = data?.items || []
    total.value = data?.total || 0
  } catch (err) {
    toast.fromError(err, '中奖记录加载失败')
  } finally {
    loading.value = false
  }
}

function changePage(next) {
  page.value = next
  load()
}

function resetFilters() {
  Object.assign(filters, { activity_id: '', status: '', keyword: '' })
  page.value = 1
  load()
}

const activityName = (id) => activities.value.find((a) => a.id === id)?.name || `#${id}`

function open(row) {
  current.value = row
  const allowed = REDEMPTION_TRANSITIONS[row.redemption_status] || []
  nextStatus.value = allowed[0] || ''
  remark.value = row.process_remark || ''
  detailOpen.value = true
}

async function submit() {
  if (!current.value || !nextStatus.value) return
  saving.value = true
  try {
    await winningApi.updateStatus(current.value.id, {
      status: nextStatus.value,
      remark: remark.value.trim() || null,
    })
    toast.success('状态已更新')
    detailOpen.value = false
    load()
  } catch (err) {
    toast.fromError(err, '状态更新失败')
  } finally {
    saving.value = false
  }
}

function exportRow(row) {
  const text = [
    `奖品：${row.prize_name}`,
    `收件人：${row.recipient_name || '—'}`,
    `手机号：${row.recipient_phone || '—'}`,
    `地址：${row.recipient_address || '—'}`,
    `兑换码：${row.redemption_code || '—'}`,
  ].join('\n')
  navigator.clipboard?.writeText(text).then(
    () => toast.success('发货信息已复制'),
    () => toast.warning('当前环境不支持自动复制'),
  )
}

onMounted(async () => {
  await loadActivities()
  await load()
})
</script>

<template>
  <div>
    <div class="toolbar mb-5">
      <select v-model="filters.activity_id" class="select" @change="page = 1; load()">
        <option value="">全部活动</option>
        <option v-for="a in activities" :key="a.id" :value="a.id">{{ a.name }}</option>
      </select>
      <select v-model="filters.status" class="select" @change="page = 1; load()">
        <option value="">全部状态</option>
        <option v-for="(meta, key) in REDEMPTION_STATUS" :key="key" :value="key">
          {{ meta.label }}
        </option>
      </select>
      <input
        v-model="filters.keyword"
        class="input"
        type="search"
        placeholder="搜索用户名或手机号"
        @keyup.enter="page = 1; load()"
      />
      <button class="btn" type="button" @click="page = 1; load()">
        <AppIcon name="search" :size="15" /> 查询
      </button>
      <button class="btn btn-ghost" type="button" @click="resetFilters">重置</button>
      <button class="btn" type="button" style="margin-left: auto" @click="load">
        <AppIcon name="refresh" :size="15" /> 刷新
      </button>
    </div>

    <LoadingBlock v-if="loading" />

    <div v-else-if="!items.length" class="card">
      <EmptyState icon="trophy" title="暂无中奖记录" desc="调整筛选条件后再试" />
    </div>

    <template v-else>
      <div class="card table-wrap">
        <table class="table">
          <thead>
            <tr>
              <th>中奖人</th>
              <th>奖品</th>
              <th>活动</th>
              <th>领奖状态</th>
              <th>收货信息</th>
              <th>中奖时间</th>
              <th class="right">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in items" :key="row.id">
              <td>
                <p class="strong">{{ row.username || '—' }}</p>
                <p class="text-xs text-soft">{{ row.recipient_phone ? maskPhone(row.recipient_phone) : '未填写手机号' }}</p>
              </td>
              <td>
                <div class="prize-cell">
                  <img v-if="row.prize_image" class="prize-thumb" :src="row.prize_image" alt="" />
                  <div v-else class="prize-thumb placeholder"><AppIcon name="gift" :size="15" /></div>
                  <div style="min-width: 0">
                    <p class="strong truncate">{{ row.prize_name }}</p>
                    <p class="text-xs text-soft">{{ row.prize_type === 'physical' ? '实物' : '虚拟' }}</p>
                  </div>
                </div>
              </td>
              <td class="text-sm truncate">{{ row.activity_name || activityName(row.activity_id) }}</td>
              <td><StatusBadge :map="REDEMPTION_STATUS" :value="row.redemption_status" /></td>
              <td class="text-xs">
                <template v-if="row.recipient_name || row.recipient_address">
                  <p>{{ row.recipient_name || '—' }}</p>
                  <p class="text-muted clamp-2" style="max-width: 220px">
                    {{ row.recipient_address || '—' }}
                  </p>
                </template>
                <span v-else class="text-soft">未提交</span>
              </td>
              <td class="text-sm nowrap">{{ formatDateTime(row.created_at) }}</td>
              <td>
                <div class="cell-actions">
                  <button class="btn btn-sm btn-soft" type="button" @click="open(row)">
                    处理
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <PaginationBar :page="page" :page-size="pageSize" :total="total" @update:page="changePage" />
    </template>

    <!-- 处理弹窗 -->
    <AppModal
      v-model="detailOpen"
      title="领奖处理"
      :desc="current ? `${current.prize_name} · 中奖人 ${current.username || '—'}` : ''"
    >
      <div v-if="current" class="stack">
        <div class="detail-block">
          <div class="kv">
            <span class="kv-key">当前状态</span>
            <StatusBadge :map="REDEMPTION_STATUS" :value="current.redemption_status" />
          </div>
          <div class="kv">
            <span class="kv-key">流水号</span>
            <span class="kv-val mono">{{ current.order_no }}</span>
          </div>
          <div class="kv">
            <span class="kv-key">兑换码</span>
            <span class="kv-val mono">{{ current.redemption_code || '—' }}</span>
          </div>
          <div class="kv">
            <span class="kv-key">领取有效期</span>
            <span class="kv-val">{{ current.expire_at ? formatDateTime(current.expire_at) : '长期有效' }}</span>
          </div>
        </div>

        <div class="detail-block">
          <div class="kv">
            <span class="kv-key">收件人</span>
            <span class="kv-val">{{ current.recipient_name || '—' }}</span>
          </div>
          <div class="kv">
            <span class="kv-key">手机号</span>
            <span class="kv-val">{{ current.recipient_phone || '—' }}</span>
          </div>
          <div class="kv">
            <span class="kv-key">收货地址</span>
            <span class="kv-val">{{ current.recipient_address || '—' }}</span>
          </div>
          <button class="btn btn-sm mt-2" type="button" @click="exportRow(current)">
            <AppIcon name="clipboard" :size="14" /> 复制发货信息
          </button>
        </div>

        <div v-if="!isReadonly" class="stack-sm">
          <div class="field">
            <label class="field-label" for="w-status">变更状态</label>
            <select id="w-status" v-model="nextStatus" class="select">
              <option v-for="item in options" :key="item" :value="item">
                {{ REDEMPTION_STATUS[item]?.label || item }}
              </option>
            </select>
          </div>
          <div class="field">
            <label class="field-label" for="w-remark">处理备注</label>
            <input
              id="w-remark"
              v-model="remark"
              class="input"
              maxlength="255"
              placeholder="例如：已顺丰发出，单号 SF123456"
            />
          </div>
        </div>
        <div v-else class="alert alert-info">
          <AppIcon class="alert-icon" name="info" :size="16" />
          <span>该记录已处于终态（已发放 / 已取消），无法继续流转。</span>
        </div>
      </div>

      <template #footer>
        <button class="btn" type="button" @click="detailOpen = false">关闭</button>
        <button
          v-if="!isReadonly"
          class="btn btn-primary"
          type="button"
          :disabled="saving || !nextStatus"
          @click="submit"
        >
          <span v-if="saving" class="spinner spinner-light" />
          {{ saving ? '提交中…' : '确认变更' }}
        </button>
      </template>
    </AppModal>
  </div>
</template>

<style scoped>
.prize-cell { display: flex; align-items: center; gap: 9px; min-width: 0; }
.prize-thumb {
  width: 34px;
  height: 34px;
  border-radius: var(--radius-xs);
  object-fit: cover;
  flex-shrink: 0;
  background: var(--surface-3);
}
.prize-thumb.placeholder { display: grid; place-items: center; color: var(--ink-400); }
.detail-block {
  padding: var(--sp-3) var(--sp-4);
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: var(--radius);
}
</style>
