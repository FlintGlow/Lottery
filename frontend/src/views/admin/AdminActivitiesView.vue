<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import AppIcon from '@/components/AppIcon.vue'
import AppModal from '@/components/AppModal.vue'
import EmptyState from '@/components/EmptyState.vue'
import ImagePicker from '@/components/ImagePicker.vue'
import LoadingBlock from '@/components/LoadingBlock.vue'
import PaginationBar from '@/components/PaginationBar.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import { activityApi } from '@/api'
import { useConfirmStore } from '@/stores/confirm'
import { useToastStore } from '@/stores/toast'
import { ACTIVITY_ACTIONS, ACTIVITY_STATUS, ADMIN_PAGE_SIZE } from '@/utils/constants'
import { formatDateTime, fromLocalInput, toLocalInput } from '@/utils/format'

const toast = useToastStore()
const confirm = useConfirmStore()

const items = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(ADMIN_PAGE_SIZE)
const keyword = ref('')
const status = ref('')
const loading = ref(true)

const modalOpen = ref(false)
const editing = ref(null)
const saving = ref(false)
const acting = ref('')
const errors = reactive({})

const emptyForm = () => ({
  name: '',
  description: '',
  cover_url: '',
  start_time: '',
  end_time: '',
  total_draw_limit: 0,
  daily_draw_limit: 0,
  none_weight: 1000,
  need_phone: false,
  need_name: false,
  announcement: '',
})
const form = reactive(emptyForm())

const isEdit = computed(() => Boolean(editing.value))

async function load() {
  loading.value = true
  try {
    const data = await activityApi.list({
      page: page.value,
      page_size: pageSize.value,
      keyword: keyword.value || undefined,
      status: status.value || undefined,
    })
    items.value = data?.items || []
    total.value = data?.total || 0
  } catch (err) {
    toast.fromError(err, '活动列表加载失败')
  } finally {
    loading.value = false
  }
}

function changePage(next) {
  page.value = next
  load()
}

function resetFilters() {
  keyword.value = ''
  status.value = ''
  page.value = 1
  load()
}

function openCreate() {
  editing.value = null
  Object.assign(form, emptyForm())
  Object.keys(errors).forEach((key) => delete errors[key])
  modalOpen.value = true
}

function openEdit(row) {
  editing.value = row
  Object.assign(form, {
    name: row.name || '',
    description: row.description || '',
    cover_url: row.cover_url || '',
    start_time: toLocalInput(row.start_time),
    end_time: toLocalInput(row.end_time),
    total_draw_limit: row.total_draw_limit ?? 0,
    daily_draw_limit: row.daily_draw_limit ?? 0,
    none_weight: row.rule_config?.none_weight ?? 1000,
    need_phone: Boolean(row.rule_config?.need_phone),
    need_name: Boolean(row.rule_config?.need_name),
    announcement: row.rule_config?.announcement || '',
  })
  Object.keys(errors).forEach((key) => delete errors[key])
  modalOpen.value = true
}

function validate() {
  Object.keys(errors).forEach((key) => delete errors[key])
  if (!form.name.trim()) errors.name = '请输入活动名称'
  if (!form.start_time) errors.start_time = '请选择开始时间'
  if (!form.end_time) errors.end_time = '请选择结束时间'
  if (form.start_time && form.end_time && form.end_time <= form.start_time) {
    errors.end_time = '结束时间必须晚于开始时间'
  }
  return !Object.keys(errors).length
}

async function save() {
  if (!validate()) return
  saving.value = true
  try {
    const payload = {
      name: form.name.trim(),
      description: form.description.trim() || null,
      cover_url: form.cover_url || null,
      start_time: fromLocalInput(form.start_time),
      end_time: fromLocalInput(form.end_time),
      total_draw_limit: Number(form.total_draw_limit) || 0,
      daily_draw_limit: Number(form.daily_draw_limit) || 0,
      rule_config: {
        none_weight: Number(form.none_weight) || 0,
        need_phone: form.need_phone,
        need_name: form.need_name,
        announcement: form.announcement.trim() || null,
      },
    }
    if (isEdit.value) {
      await activityApi.update(editing.value.id, payload)
      toast.success('活动已更新')
    } else {
      await activityApi.create(payload)
      toast.success('活动已创建（初始为草稿状态）')
    }
    modalOpen.value = false
    load()
  } catch (err) {
    toast.fromError(err, '保存失败')
  } finally {
    saving.value = false
  }
}

async function runAction(row, action) {
  const label = ACTIVITY_ACTIONS.find((a) => a.action === action)?.label || action
  const ok = await confirm.ask({
    title: `${label}活动`,
    message: `确认要${label}「${row.name}」吗？`,
    detail:
      action === 'end'
        ? '结束后活动将不可再抽奖。'
        : action === 'pause'
          ? '暂停期间用户无法抽奖，可随时恢复。'
          : '',
    confirmText: `确认${label}`,
    tone: action === 'end' ? 'danger' : 'primary',
  })
  if (!ok) return
  acting.value = `${row.id}-${action}`
  try {
    await activityApi.transition(row.id, action)
    toast.success(`活动已${label}`)
    load()
  } catch (err) {
    toast.fromError(err, `${label}失败`)
  } finally {
    acting.value = ''
  }
}

async function remove(row) {
  const ok = await confirm.ask({
    title: '删除活动',
    message: `确认删除「${row.name}」吗？`,
    detail: '仅草稿或待开始、且没有奖品的活动可以删除，删除后不可恢复。',
    confirmText: '删除',
    tone: 'danger',
  })
  if (!ok) return
  try {
    await activityApi.remove(row.id)
    toast.success('活动已删除')
    load()
  } catch (err) {
    toast.fromError(err, '删除失败')
  }
}

const actionsFor = (row) => ACTIVITY_ACTIONS.filter((a) => a.from.includes(row.status))

onMounted(load)
</script>

<template>
  <div>
    <div class="toolbar mb-5">
      <input
        v-model="keyword"
        class="input"
        type="search"
        placeholder="搜索活动名称"
        @keyup.enter="page = 1; load()"
      />
      <select v-model="status" class="select" @change="page = 1; load()">
        <option value="">全部状态</option>
        <option v-for="(meta, key) in ACTIVITY_STATUS" :key="key" :value="key">
          {{ meta.label }}
        </option>
      </select>
      <button class="btn" type="button" @click="page = 1; load()">
        <AppIcon name="search" :size="15" /> 查询
      </button>
      <button class="btn btn-ghost" type="button" @click="resetFilters">重置</button>
      <button class="btn btn-primary" type="button" style="margin-left: auto" @click="openCreate">
        <AppIcon name="plus" :size="15" /> 新建活动
      </button>
    </div>

    <LoadingBlock v-if="loading" />

    <div v-else-if="!items.length" class="card">
      <EmptyState icon="sparkles" title="还没有活动" desc="点击「新建活动」创建第一个抽奖活动">
        <button class="btn btn-primary" type="button" @click="openCreate">新建活动</button>
      </EmptyState>
    </div>

    <template v-else>
      <div class="card table-wrap">
        <table class="table">
          <thead>
            <tr>
              <th>活动</th>
              <th>状态</th>
              <th>活动时间</th>
              <th class="right">次数限制</th>
              <th class="right">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in items" :key="row.id">
              <td>
                <div class="cell-main">
                  <span class="strong">{{ row.name }}</span>
                  <span class="text-xs text-soft mono">#{{ row.id }}</span>
                </div>
                <p v-if="row.description" class="text-xs text-muted clamp-2 desc">{{ row.description }}</p>
              </td>
              <td><StatusBadge :map="ACTIVITY_STATUS" :value="row.status" /></td>
              <td class="nowrap text-sm">
                {{ formatDateTime(row.start_time) }}<br />
                <span class="text-muted">{{ formatDateTime(row.end_time) }}</span>
              </td>
              <td class="right text-sm">
                <div>总 {{ row.total_draw_limit || '不限' }}</div>
                <div class="text-muted">日 {{ row.daily_draw_limit || '不限' }}</div>
              </td>
              <td>
                <div class="cell-actions">
                  <button
                    v-for="action in actionsFor(row)"
                    :key="action.action"
                    class="btn btn-sm"
                    :class="action.cls"
                    type="button"
                    :disabled="acting === `${row.id}-${action.action}`"
                    @click="runAction(row, action.action)"
                  >
                    <span
                      v-if="acting === `${row.id}-${action.action}`"
                      class="spinner"
                      :class="{ 'spinner-light': action.cls === 'btn-primary' }"
                    />
                    {{ action.label }}
                  </button>
                  <button class="btn btn-sm btn-ghost" type="button" @click="openEdit(row)">
                    <AppIcon name="edit" :size="14" /> 编辑
                  </button>
                  <button class="btn btn-sm btn-danger" type="button" @click="remove(row)">
                    <AppIcon name="trash" :size="14" />
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <PaginationBar :page="page" :page-size="pageSize" :total="total" @update:page="changePage" />
    </template>

    <!-- 新建 / 编辑 -->
    <AppModal
      v-model="modalOpen"
      :title="isEdit ? '编辑活动' : '新建活动'"
      :desc="isEdit ? `活动 #${editing?.id}` : '创建后活动处于草稿状态，需要手动发布'"
      size="lg"
    >
      <div class="form-grid">
        <div class="field span-2">
          <label class="field-label" for="a-name">活动名称<span class="req">*</span></label>
          <input
            id="a-name"
            v-model="form.name"
            class="input"
            :class="{ 'is-invalid': errors.name }"
            maxlength="128"
            placeholder="例如：双十一幸运抽奖"
          />
          <p v-if="errors.name" class="field-error">{{ errors.name }}</p>
        </div>

        <div class="field span-2">
          <label class="field-label" for="a-desc">活动描述</label>
          <textarea
            id="a-desc"
            v-model="form.description"
            class="textarea"
            maxlength="2000"
            placeholder="向用户说明活动玩法与注意事项"
          />
        </div>

        <div class="field span-2">
          <label class="field-label">活动封面</label>
          <ImagePicker v-model="form.cover_url" target="admin" height="140px" />
        </div>

        <div class="field">
          <label class="field-label" for="a-start">开始时间<span class="req">*</span></label>
          <input
            id="a-start"
            v-model="form.start_time"
            class="input"
            :class="{ 'is-invalid': errors.start_time }"
            type="datetime-local"
          />
          <p v-if="errors.start_time" class="field-error">{{ errors.start_time }}</p>
        </div>

        <div class="field">
          <label class="field-label" for="a-end">结束时间<span class="req">*</span></label>
          <input
            id="a-end"
            v-model="form.end_time"
            class="input"
            :class="{ 'is-invalid': errors.end_time }"
            type="datetime-local"
          />
          <p v-if="errors.end_time" class="field-error">{{ errors.end_time }}</p>
          <p v-else class="field-hint">结束时间需晚于当前时间，否则活动无法发布</p>
        </div>

        <div class="field">
          <label class="field-label" for="a-total">活动总次数上限</label>
          <input id="a-total" v-model.number="form.total_draw_limit" class="input" type="number" min="0" />
          <p class="field-hint">0 表示不限</p>
        </div>

        <div class="field">
          <label class="field-label" for="a-daily">每人每日次数</label>
          <input id="a-daily" v-model.number="form.daily_draw_limit" class="input" type="number" min="0" />
          <p class="field-hint">0 表示不限</p>
        </div>

        <div class="field span-2">
          <label class="field-label" for="a-none">未中奖权重</label>
          <input id="a-none" v-model.number="form.none_weight" class="input" type="number" min="0" />
          <p class="field-hint">
            该值会与所有奖品权重之和比较，数值越大越难中奖；默认 1000
          </p>
        </div>

        <div class="field span-2">
          <label class="field-label" for="a-ann">活动公告</label>
          <input
            id="a-ann"
            v-model="form.announcement"
            class="input"
            maxlength="200"
            placeholder="展示在活动详情页的提示文案"
          />
        </div>

        <div class="span-2 row gap-5 wrap">
          <label class="checkbox">
            <input v-model="form.need_phone" type="checkbox" />
            参与需绑定手机号
          </label>
          <label class="checkbox">
            <input v-model="form.need_name" type="checkbox" />
            领奖需填写真实姓名
          </label>
        </div>
      </div>

      <template #footer>
        <button class="btn" type="button" @click="modalOpen = false">取消</button>
        <button class="btn btn-primary" type="button" :disabled="saving" @click="save">
          <span v-if="saving" class="spinner spinner-light" />
          {{ saving ? '保存中…' : isEdit ? '保存修改' : '创建活动' }}
        </button>
      </template>
    </AppModal>
  </div>
</template>

<style scoped>
.cell-main { display: flex; align-items: baseline; gap: 8px; }
.desc { max-width: 320px; margin-top: 2px; }
.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--sp-4);
}
.span-2 { grid-column: span 2; }
@media (max-width: 720px) {
  .form-grid { grid-template-columns: minmax(0, 1fr); }
  .span-2 { grid-column: span 1; }
}
</style>
