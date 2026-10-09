<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import AppIcon from '@/components/AppIcon.vue'
import AppModal from '@/components/AppModal.vue'
import EmptyState from '@/components/EmptyState.vue'
import LoadingBlock from '@/components/LoadingBlock.vue'
import PaginationBar from '@/components/PaginationBar.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import { rewardApi, operationsApi } from '@/api'
import { useToastStore } from '@/stores/toast'
import { ADMIN_PAGE_SIZE, REWARD_STATUS, REWARD_TRANSITIONS } from '@/utils/constants'
import { formatDateTime, maskPhone } from '@/utils/format'

const toast = useToastStore()

const items = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(ADMIN_PAGE_SIZE)
const loading = ref(true)
const advanced = ref(false)

const filters = reactive({
  operator: '',
  activity_id: '',
  user_id: '',
  username: '',
  phone_number: '',
  prize_id: '',
  keywords: '',
  status: '',
  start_time: '',
  end_time: '',
})

/* ---------------- 补发创建 ---------------- */
const createOpen = ref(false)
const creating = ref(false)
const createForm = reactive({ reason: '', remark: '', draw_record_id: '' })
const createErrors = reactive({})

const userQuery = ref('')
const userOptions = ref([])
const userSearching = ref(false)
const pickedUser = ref(null)

const prizeQuery = ref('')
const prizeOptions = ref([])
const prizeSearching = ref(false)
const pickedPrize = ref(null)

/* ---------------- 状态流转 ---------------- */
const statusOpen = ref(false)
const current = ref(null)
const nextStatus = ref('')
const statusRemark = ref('')
const statusSaving = ref(false)
const statusOptions = computed(() =>
  current.value ? REWARD_TRANSITIONS[current.value.status] || [] : [],
)

async function load() {
  loading.value = true
  try {
    const data = await rewardApi.list({
      page: page.value,
      page_size: pageSize.value,
      operator: filters.operator || undefined,
      activity_id: filters.activity_id || undefined,
      user_id: filters.user_id || undefined,
      username: filters.username || undefined,
      phone_number: filters.phone_number || undefined,
      prize_id: filters.prize_id || undefined,
      keywords: filters.keywords || undefined,
      status: filters.status || undefined,
      start_time: filters.start_time || undefined,
      end_time: filters.end_time || undefined,
    })
    items.value = data?.items || []
    total.value = data?.total || 0
  } catch (err) {
    toast.fromError(err, '补发记录加载失败')
  } finally {
    loading.value = false
  }
}

function changePage(next) {
  page.value = next
  load()
}

function resetFilters() {
  Object.assign(filters, {
    operator: '', activity_id: '', user_id: '', username: '', phone_number: '',
    prize_id: '', keywords: '', status: '', start_time: '', end_time: '',
  })
  page.value = 1
  load()
}

/* ---------------- 搜索选择器 ---------------- */
let userTimer = null
function searchUsers() {
  clearTimeout(userTimer)
  userTimer = setTimeout(async () => {
    userSearching.value = true
    try {
      const data = await operationsApi.users({
        page: 1,
        page_size: 8,
        keyword: userQuery.value || undefined,
      })
      userOptions.value = data?.items || []
    } catch {
      userOptions.value = []
    } finally {
      userSearching.value = false
    }
  }, 280)
}

let prizeTimer = null
function searchPrizes() {
  clearTimeout(prizeTimer)
  prizeTimer = setTimeout(async () => {
    prizeSearching.value = true
    try {
      const data = await operationsApi.prizes({
        page: 1,
        page_size: 8,
        keyword: prizeQuery.value || undefined,
      })
      prizeOptions.value = data?.items || []
    } catch {
      prizeOptions.value = []
    } finally {
      prizeSearching.value = false
    }
  }, 280)
}

function pickUser(user) {
  pickedUser.value = user
  userOptions.value = []
  userQuery.value = ''
}

function pickPrize(prize) {
  pickedPrize.value = prize
  prizeOptions.value = []
  prizeQuery.value = ''
}

function openCreate() {
  createForm.reason = ''
  createForm.remark = ''
  createForm.draw_record_id = ''
  pickedUser.value = null
  pickedPrize.value = null
  userQuery.value = ''
  prizeQuery.value = ''
  Object.keys(createErrors).forEach((key) => delete createErrors[key])
  createOpen.value = true
  searchUsers()
  searchPrizes()
}

async function submitCreate() {
  Object.keys(createErrors).forEach((key) => delete createErrors[key])
  if (!pickedUser.value) createErrors.user = '请选择补发用户'
  if (!pickedPrize.value) createErrors.prize = '请选择补发奖品'
  if (!createForm.reason.trim()) createErrors.reason = '请填写补发原因'
  if (Object.keys(createErrors).length) return

  creating.value = true
  try {
    await rewardApi.create({
      user_id: pickedUser.value.id,
      prize_id: pickedPrize.value.id,
      draw_record_id: createForm.draw_record_id ? Number(createForm.draw_record_id) : null,
      reason: createForm.reason.trim(),
      remark: createForm.remark.trim() || null,
    })
    toast.success('补发记录已创建（待发放）')
    createOpen.value = false
    page.value = 1
    load()
  } catch (err) {
    toast.fromError(err, '创建失败')
  } finally {
    creating.value = false
  }
}

/* ---------------- 状态流转 ---------------- */
function openStatus(row) {
  current.value = row
  const allowed = REWARD_TRANSITIONS[row.status] || []
  nextStatus.value = allowed[0] || ''
  statusRemark.value = row.remark || ''
  statusOpen.value = true
}

async function submitStatus() {
  if (!current.value || !nextStatus.value) return
  statusSaving.value = true
  try {
    await rewardApi.updateStatus(current.value.id, {
      status: nextStatus.value,
      remark: statusRemark.value.trim() || null,
    })
    toast.success(
      nextStatus.value === 'issued'
        ? '已确认发放：库存已扣减，并生成中奖记录进入领奖流程'
        : '状态已更新',
    )
    statusOpen.value = false
    load()
  } catch (err) {
    toast.fromError(err, '状态更新失败')
  } finally {
    statusSaving.value = false
  }
}

onMounted(load)
</script>

<template>
  <div>
    <div class="toolbar mb-4">
      <input
        v-model="filters.keywords"
        class="input"
        type="search"
        placeholder="关键字（用户名 / 手机号 / 奖品 / 原因）"
        @keyup.enter="page = 1; load()"
      />
      <select v-model="filters.status" class="select" @change="page = 1; load()">
        <option value="">全部状态</option>
        <option v-for="(meta, key) in REWARD_STATUS" :key="key" :value="key">{{ meta.label }}</option>
      </select>
      <button class="btn" type="button" @click="page = 1; load()">
        <AppIcon name="search" :size="15" /> 查询
      </button>
      <button class="btn btn-ghost" type="button" @click="advanced = !advanced">
        <AppIcon name="filter" :size="15" />
        {{ advanced ? '收起筛选' : '更多筛选' }}
      </button>
      <button class="btn btn-primary" type="button" style="margin-left: auto" @click="openCreate">
        <AppIcon name="send" :size="15" /> 人工补发
      </button>
    </div>

    <div v-if="advanced" class="card card-pad mb-5">
      <div class="adv-grid">
        <div class="field">
          <label class="field-label">操作人</label>
          <input v-model="filters.operator" class="input" placeholder="操作人用户名" />
        </div>
        <div class="field">
          <label class="field-label">用户名</label>
          <input v-model="filters.username" class="input" placeholder="补发对象用户名" />
        </div>
        <div class="field">
          <label class="field-label">手机号</label>
          <input v-model="filters.phone_number" class="input" placeholder="补发对象手机号" />
        </div>
        <div class="field">
          <label class="field-label">用户 ID</label>
          <input v-model="filters.user_id" class="input" type="number" placeholder="用户 ID" />
        </div>
        <div class="field">
          <label class="field-label">活动 ID</label>
          <input v-model="filters.activity_id" class="input" type="number" placeholder="活动 ID" />
        </div>
        <div class="field">
          <label class="field-label">奖品 ID</label>
          <input v-model="filters.prize_id" class="input" type="number" placeholder="奖品 ID" />
        </div>
        <div class="field">
          <label class="field-label">开始时间</label>
          <input v-model="filters.start_time" class="input" type="datetime-local" />
        </div>
        <div class="field">
          <label class="field-label">结束时间</label>
          <input v-model="filters.end_time" class="input" type="datetime-local" />
        </div>
      </div>
      <div class="row mt-4" style="justify-content: flex-end">
        <button class="btn btn-ghost" type="button" @click="resetFilters">清空全部条件</button>
        <button class="btn btn-primary" type="button" @click="page = 1; load()">应用筛选</button>
      </div>
    </div>

    <LoadingBlock v-if="loading" />

    <div v-else-if="!items.length" class="card">
      <EmptyState icon="send" title="暂无补发记录" desc="补发用于处理漏发、异常中奖等情况，不改动原中奖记录">
        <button class="btn btn-primary" type="button" @click="openCreate">创建补发</button>
      </EmptyState>
    </div>

    <template v-else>
      <div class="card table-wrap">
        <table class="table">
          <thead>
            <tr>
              <th>补发对象</th>
              <th>奖品 / 活动</th>
              <th>原因</th>
              <th>状态</th>
              <th>操作人</th>
              <th>创建时间</th>
              <th class="right">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in items" :key="row.id">
              <td>
                <p class="strong">{{ row.user_name || `#${row.user_id}` }}</p>
                <p class="text-xs text-soft">{{ row.phone_number ? maskPhone(row.phone_number) : '—' }}</p>
              </td>
              <td class="text-sm">
                <p class="strong truncate">{{ row.prize_name || `#${row.prize_id}` }}</p>
                <p class="text-muted truncate">{{ row.activity_name || `活动 #${row.activity_id}` }}</p>
              </td>
              <td class="text-sm" style="max-width: 240px">
                <p class="clamp-2">{{ row.reason }}</p>
                <p v-if="row.remark" class="text-xs text-soft clamp-2">{{ row.remark }}</p>
              </td>
              <td><StatusBadge :map="REWARD_STATUS" :value="row.status" /></td>
              <td class="text-sm">
                <p>{{ row.operator_name || '—' }}</p>
                <p class="text-xs text-soft">{{ row.operated_at ? formatDateTime(row.operated_at) : '' }}</p>
              </td>
              <td class="text-sm nowrap">{{ formatDateTime(row.created_at) }}</td>
              <td>
                <div class="cell-actions">
                  <button
                    class="btn btn-sm btn-soft"
                    type="button"
                    :disabled="!(REWARD_TRANSITIONS[row.status] || []).length"
                    @click="openStatus(row)"
                  >
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

    <!-- 创建补发 -->
    <AppModal
      v-model="createOpen"
      title="人工补发"
      desc="补发不会改动原中奖记录；确认发放时会扣减库存并生成中奖记录"
      size="lg"
    >
      <div class="stack">
        <div class="field">
          <label class="field-label">补发用户<span class="req">*</span></label>
          <div v-if="pickedUser" class="picked">
            <span class="avatar avatar-sm">{{ (pickedUser.username || '?').slice(0, 1) }}</span>
            <div class="grow">
              <p class="strong">{{ pickedUser.username }}</p>
              <p class="text-xs text-muted">
                #{{ pickedUser.id }} · {{ pickedUser.phone_number || '未绑定手机号' }}
              </p>
            </div>
            <button class="btn btn-sm btn-ghost" type="button" @click="pickedUser = null">更换</button>
          </div>
          <template v-else>
            <input
              v-model="userQuery"
              class="input"
              :class="{ 'is-invalid': createErrors.user }"
              placeholder="输入用户名或手机号搜索"
              @input="searchUsers"
              @focus="searchUsers"
            />
            <p v-if="createErrors.user" class="field-error">{{ createErrors.user }}</p>
            <div v-if="userOptions.length" class="options">
              <button
                v-for="user in userOptions"
                :key="user.id"
                class="option"
                type="button"
                @click="pickUser(user)"
              >
                <span class="avatar avatar-sm">{{ (user.username || '?').slice(0, 1) }}</span>
                <span class="grow">
                  <span class="strong">{{ user.username }}</span>
                  <span class="text-xs text-muted"> #{{ user.id }} · {{ user.phone_number || '—' }}</span>
                </span>
              </button>
            </div>
            <p v-else-if="userSearching" class="field-hint">搜索中…</p>
          </template>
        </div>

        <div class="field">
          <label class="field-label">补发奖品<span class="req">*</span></label>
          <div v-if="pickedPrize" class="picked">
            <img v-if="pickedPrize.img_url" class="picked-thumb" :src="pickedPrize.img_url" alt="" />
            <span v-else class="picked-thumb placeholder"><AppIcon name="gift" :size="15" /></span>
            <div class="grow">
              <p class="strong">{{ pickedPrize.name }}</p>
              <p class="text-xs text-muted">
                #{{ pickedPrize.id }} · 剩余 {{ pickedPrize.remain_stock }} · 活动 #{{ pickedPrize.activity_id }}
              </p>
            </div>
            <button class="btn btn-sm btn-ghost" type="button" @click="pickedPrize = null">更换</button>
          </div>
          <template v-else>
            <input
              v-model="prizeQuery"
              class="input"
              :class="{ 'is-invalid': createErrors.prize }"
              placeholder="输入奖品名称搜索"
              @input="searchPrizes"
              @focus="searchPrizes"
            />
            <p v-if="createErrors.prize" class="field-error">{{ createErrors.prize }}</p>
            <div v-if="prizeOptions.length" class="options">
              <button
                v-for="prize in prizeOptions"
                :key="prize.id"
                class="option"
                type="button"
                @click="pickPrize(prize)"
              >
                <img v-if="prize.img_url" class="picked-thumb" :src="prize.img_url" alt="" />
                <span v-else class="picked-thumb placeholder"><AppIcon name="gift" :size="14" /></span>
                <span class="grow">
                  <span class="strong">{{ prize.name }}</span>
                  <span class="text-xs text-muted"> #{{ prize.id }} · 剩余 {{ prize.remain_stock }}</span>
                </span>
              </button>
            </div>
            <p v-else-if="prizeSearching" class="field-hint">搜索中…</p>
          </template>
        </div>

        <div class="form-row">
          <div class="field">
            <label class="field-label" for="r-draw">关联抽奖记录 ID</label>
            <input
              id="r-draw"
              v-model="createForm.draw_record_id"
              class="input"
              type="number"
              placeholder="选填"
            />
            <p class="field-hint">填写后活动将取自该抽奖记录</p>
          </div>
        </div>

        <div class="field">
          <label class="field-label" for="r-reason">补发原因<span class="req">*</span></label>
          <input
            id="r-reason"
            v-model="createForm.reason"
            class="input"
            :class="{ 'is-invalid': createErrors.reason }"
            maxlength="255"
            placeholder="例如：抽奖成功但未生成中奖记录"
          />
          <p v-if="createErrors.reason" class="field-error">{{ createErrors.reason }}</p>
        </div>

        <div class="field">
          <label class="field-label" for="r-remark">备注</label>
          <input id="r-remark" v-model="createForm.remark" class="input" maxlength="255" placeholder="选填，例如工单号" />
        </div>
      </div>

      <template #footer>
        <button class="btn" type="button" @click="createOpen = false">取消</button>
        <button class="btn btn-primary" type="button" :disabled="creating" @click="submitCreate">
          <span v-if="creating" class="spinner spinner-light" />
          {{ creating ? '提交中…' : '创建补发' }}
        </button>
      </template>
    </AppModal>

    <!-- 状态流转 -->
    <AppModal
      v-model="statusOpen"
      title="补发状态变更"
      :desc="current ? `${current.prize_name || ''} · ${current.user_name || ''}` : ''"
      size="sm"
    >
      <div v-if="current" class="stack-sm">
        <div class="kv">
          <span class="kv-key">当前状态</span>
          <StatusBadge :map="REWARD_STATUS" :value="current.status" />
        </div>
        <div class="field">
          <label class="field-label" for="rs-status">变更为</label>
          <select id="rs-status" v-model="nextStatus" class="select">
            <option v-for="item in statusOptions" :key="item" :value="item">
              {{ REWARD_STATUS[item]?.label || item }}
            </option>
          </select>
        </div>
        <div class="field">
          <label class="field-label" for="rs-remark">备注</label>
          <input id="rs-remark" v-model="statusRemark" class="input" maxlength="255" />
        </div>
        <div v-if="nextStatus === 'issued'" class="alert alert-warning">
          <AppIcon class="alert-icon" name="alert" :size="16" />
          <span>确认发放会扣减奖品库存（数据库与缓存同步），并生成一条中奖记录进入领奖流程。</span>
        </div>
      </div>

      <template #footer>
        <button class="btn" type="button" @click="statusOpen = false">取消</button>
        <button class="btn btn-primary" type="button" :disabled="statusSaving || !nextStatus" @click="submitStatus">
          <span v-if="statusSaving" class="spinner spinner-light" />
          {{ statusSaving ? '提交中…' : '确认' }}
        </button>
      </template>
    </AppModal>
  </div>
</template>

<style scoped>
.adv-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
  gap: var(--sp-4);
}
.form-row { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: var(--sp-4); }
.picked {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 9px 12px;
  border: 1px solid var(--brand-200);
  background: var(--brand-50);
  border-radius: var(--radius-sm);
}
.picked-thumb {
  width: 32px;
  height: 32px;
  border-radius: var(--radius-xs);
  object-fit: cover;
  flex-shrink: 0;
  background: var(--surface-3);
}
.picked-thumb.placeholder { display: grid; place-items: center; color: var(--ink-400); }
.options {
  margin-top: 6px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  overflow: hidden;
  background: var(--surface);
  box-shadow: var(--shadow-sm);
  max-height: 232px;
  overflow-y: auto;
}
.option {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 8px 12px;
  border: 0;
  background: transparent;
  text-align: left;
  cursor: pointer;
  font-size: 13.5px;
  color: var(--ink-700);
}
.option:hover { background: var(--surface-3); }
.option + .option { border-top: 1px solid var(--border); }
</style>
