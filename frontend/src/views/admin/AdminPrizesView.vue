<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import AppIcon from '@/components/AppIcon.vue'
import AppModal from '@/components/AppModal.vue'
import EmptyState from '@/components/EmptyState.vue'
import ImagePicker from '@/components/ImagePicker.vue'
import LoadingBlock from '@/components/LoadingBlock.vue'
import PaginationBar from '@/components/PaginationBar.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import { activityApi, categoryApi, prizeApi } from '@/api'
import { useConfirmStore } from '@/stores/confirm'
import { useToastStore } from '@/stores/toast'
import { ADMIN_PAGE_SIZE, PRIZE_STATUS, PRIZE_TYPE } from '@/utils/constants'
import { formatDateTime } from '@/utils/format'

const toast = useToastStore()
const confirm = useConfirmStore()

const tab = ref('prizes')

/* ---------------------------------------------------------------- 奖品 */
const items = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(ADMIN_PAGE_SIZE)
const filters = reactive({ activity_id: '', category_id: '', keyword: '', status: '' })
const loading = ref(true)
const activities = ref([])
const categories = ref([])

const modalOpen = ref(false)
const editing = ref(null)
const saving = ref(false)
const errors = reactive({})

const emptyForm = () => ({
  activity_id: '',
  category_id: '',
  name: '',
  prize_type: 'physical',
  prize_level: '',
  description: '',
  total_stock: 0,
  weight: 0,
  daily_limit: 0,
  img_url: '',
  sort_order: 0,
  status: 'enabled',
})
const form = reactive(emptyForm())
const isEdit = computed(() => Boolean(editing.value))

const stockOpen = ref(false)
const stockTarget = ref(null)
const stockDelta = ref(1)
const stockVersion = ref(0)
const stockSaving = ref(false)

/* ---------------------------------------------------------------- 分类 */
const categoryModal = ref(false)
const categoryEditing = ref(null)
const categorySaving = ref(false)
const categoryForm = reactive({ name: '', description: '', sort_order: 0, status: 'enabled' })
const categoryErrors = reactive({})

const activityName = (id) => activities.value.find((a) => a.id === id)?.name || `#${id}`

async function loadRefs() {
  try {
    const [acts, cats] = await Promise.all([
      activityApi.list({ page: 1, page_size: 100 }),
      categoryApi.list(),
    ])
    activities.value = acts?.items || []
    categories.value = Array.isArray(cats) ? cats : []
  } catch (err) {
    toast.fromError(err, '基础数据加载失败')
  }
}

async function load() {
  loading.value = true
  try {
    const data = await prizeApi.list({
      page: page.value,
      page_size: pageSize.value,
      activity_id: filters.activity_id || undefined,
      category_id: filters.category_id || undefined,
      keyword: filters.keyword || undefined,
      status: filters.status || undefined,
    })
    items.value = data?.items || []
    total.value = data?.total || 0
  } catch (err) {
    toast.fromError(err, '奖品列表加载失败')
  } finally {
    loading.value = false
  }
}

function changePage(next) {
  page.value = next
  load()
}

function resetFilters() {
  Object.assign(filters, { activity_id: '', category_id: '', keyword: '', status: '' })
  page.value = 1
  load()
}

function openCreate() {
  editing.value = null
  Object.assign(form, emptyForm())
  form.activity_id = filters.activity_id || activities.value[0]?.id || ''
  Object.keys(errors).forEach((key) => delete errors[key])
  modalOpen.value = true
}

function openEdit(row) {
  editing.value = row
  Object.assign(form, {
    activity_id: row.activity_id,
    category_id: row.category_id ?? '',
    name: row.name || '',
    prize_type: row.prize_type || 'physical',
    prize_level: row.prize_level || '',
    description: row.description || '',
    total_stock: row.total_stock ?? 0,
    weight: row.weight ?? 0,
    daily_limit: row.daily_limit ?? 0,
    img_url: row.img_url || '',
    sort_order: row.sort_order ?? 0,
    status: row.status || 'enabled',
  })
  Object.keys(errors).forEach((key) => delete errors[key])
  modalOpen.value = true
}

function validate() {
  Object.keys(errors).forEach((key) => delete errors[key])
  if (!form.activity_id) errors.activity_id = '请选择所属活动'
  if (!form.name.trim()) errors.name = '请输入奖品名称'
  if (!isEdit.value && Number(form.total_stock) < 0) errors.total_stock = '库存不能为负'
  return !Object.keys(errors).length
}

async function save() {
  if (!validate()) return
  saving.value = true
  try {
    const base = {
      category_id: form.category_id ? Number(form.category_id) : null,
      name: form.name.trim(),
      prize_type: form.prize_type,
      prize_level: form.prize_level.trim() || null,
      description: form.description.trim() || null,
      weight: Number(form.weight) || 0,
      daily_limit: Number(form.daily_limit) || 0,
      img_url: form.img_url || null,
      sort_order: Number(form.sort_order) || 0,
    }
    if (isEdit.value) {
      await prizeApi.update(editing.value.id, { ...base, status: form.status })
      toast.success('奖品已更新')
    } else {
      await prizeApi.create({
        ...base,
        activity_id: Number(form.activity_id),
        total_stock: Number(form.total_stock) || 0,
      })
      toast.success('奖品已创建')
    }
    modalOpen.value = false
    load()
  } catch (err) {
    toast.fromError(err, '保存失败')
  } finally {
    saving.value = false
  }
}

async function remove(row) {
  const ok = await confirm.ask({
    title: '删除奖品',
    message: `确认删除「${row.name}」吗？`,
    detail: '若该奖品已产生抽奖或中奖记录，删除会被拒绝。',
    confirmText: '删除',
    tone: 'danger',
  })
  if (!ok) return
  try {
    await prizeApi.remove(row.id)
    toast.success('奖品已删除')
    load()
  } catch (err) {
    toast.fromError(err, '删除失败')
  }
}

async function openStock(row) {
  stockTarget.value = row
  stockDelta.value = 1
  stockVersion.value = row.version
  stockOpen.value = true
  // 拉取最新版本号，避免乐观锁冲突
  try {
    const fresh = await prizeApi.get(row.id)
    if (fresh) {
      stockTarget.value = fresh
      stockVersion.value = fresh.version
    }
  } catch {
    /* 使用列表中的版本号 */
  }
}

async function submitStock() {
  if (!stockTarget.value) return
  const delta = Number(stockDelta.value)
  if (!Number.isFinite(delta) || delta === 0) {
    toast.warning('请输入非 0 的调整量')
    return
  }
  stockSaving.value = true
  try {
    await prizeApi.adjustStock(stockTarget.value.id, { version: stockVersion.value, delta })
    toast.success('库存已调整')
    stockOpen.value = false
    load()
  } catch (err) {
    if (err?.status === 409) {
      toast.error('版本冲突：奖品已被其他操作修改，请刷新后重试')
      load()
    } else {
      toast.fromError(err, '库存调整失败')
    }
  } finally {
    stockSaving.value = false
  }
}

/* ---------------------------------------------------------------- 分类 CRUD */
function openCategoryCreate() {
  categoryEditing.value = null
  Object.assign(categoryForm, { name: '', description: '', sort_order: 0, status: 'enabled' })
  Object.keys(categoryErrors).forEach((key) => delete categoryErrors[key])
  categoryModal.value = true
}

function openCategoryEdit(row) {
  categoryEditing.value = row
  Object.assign(categoryForm, {
    name: row.name || '',
    description: row.description || '',
    sort_order: row.sort_order ?? 0,
    status: row.status || 'enabled',
  })
  Object.keys(categoryErrors).forEach((key) => delete categoryErrors[key])
  categoryModal.value = true
}

async function saveCategory() {
  Object.keys(categoryErrors).forEach((key) => delete categoryErrors[key])
  if (!categoryForm.name.trim()) categoryErrors.name = '请输入分类名称'
  if (Object.keys(categoryErrors).length) return

  categorySaving.value = true
  try {
    const payload = {
      name: categoryForm.name.trim(),
      description: categoryForm.description.trim() || null,
      sort_order: Number(categoryForm.sort_order) || 0,
      status: categoryForm.status,
    }
    if (categoryEditing.value) {
      await categoryApi.update(categoryEditing.value.id, payload)
      toast.success('分类已更新')
    } else {
      delete payload.status
      await categoryApi.create(payload)
      toast.success('分类已创建')
    }
    categoryModal.value = false
    await loadRefs()
  } catch (err) {
    toast.fromError(err, '保存失败')
  } finally {
    categorySaving.value = false
  }
}

async function removeCategory(row) {
  const ok = await confirm.ask({
    title: '删除分类',
    message: `确认删除分类「${row.name}」吗？`,
    detail: '若分类下仍有奖品，删除会被拒绝。',
    confirmText: '删除',
    tone: 'danger',
  })
  if (!ok) return
  try {
    await categoryApi.remove(row.id)
    toast.success('分类已删除')
    await loadRefs()
  } catch (err) {
    toast.fromError(err, '删除失败')
  }
}

const stockPercent = (row) => {
  const total = Number(row.total_stock || 0)
  if (!total) return 0
  return Math.max(0, Math.min(100, Math.round((Number(row.remain_stock || 0) / total) * 100)))
}

onMounted(async () => {
  await loadRefs()
  await load()
})
</script>

<template>
  <div>
    <div class="tabs mb-5" style="max-width: 260px">
      <button class="tab" :class="{ 'is-active': tab === 'prizes' }" type="button" @click="tab = 'prizes'">
        奖品列表
      </button>
      <button
        class="tab"
        :class="{ 'is-active': tab === 'categories' }"
        type="button"
        @click="tab = 'categories'"
      >
        奖品分类
      </button>
    </div>

    <!-- ============ 奖品 ============ -->
    <template v-if="tab === 'prizes'">
      <div class="toolbar mb-5">
        <select v-model="filters.activity_id" class="select" @change="page = 1; load()">
          <option value="">全部活动</option>
          <option v-for="a in activities" :key="a.id" :value="a.id">{{ a.name }}</option>
        </select>
        <select v-model="filters.category_id" class="select" @change="page = 1; load()">
          <option value="">全部分类</option>
          <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name }}</option>
        </select>
        <select v-model="filters.status" class="select" @change="page = 1; load()">
          <option value="">全部状态</option>
          <option v-for="(meta, key) in PRIZE_STATUS" :key="key" :value="key">{{ meta.label }}</option>
        </select>
        <input
          v-model="filters.keyword"
          class="input"
          type="search"
          placeholder="搜索奖品名称"
          @keyup.enter="page = 1; load()"
        />
        <button class="btn" type="button" @click="page = 1; load()">
          <AppIcon name="search" :size="15" /> 查询
        </button>
        <button class="btn btn-ghost" type="button" @click="resetFilters">重置</button>
        <button class="btn btn-primary" type="button" style="margin-left: auto" @click="openCreate">
          <AppIcon name="plus" :size="15" /> 新建奖品
        </button>
      </div>

      <LoadingBlock v-if="loading" />

      <div v-else-if="!items.length" class="card">
        <EmptyState icon="gift" title="没有找到奖品" desc="调整筛选条件，或创建一个新奖品">
          <button class="btn btn-primary" type="button" @click="openCreate">新建奖品</button>
        </EmptyState>
      </div>

      <template v-else>
        <div class="card table-wrap">
          <table class="table">
            <thead>
              <tr>
                <th>奖品</th>
                <th>活动 / 分类</th>
                <th>类型</th>
                <th style="min-width: 150px">库存</th>
                <th class="right">权重</th>
                <th class="right">每日上限</th>
                <th>状态</th>
                <th class="right">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in items" :key="row.id">
                <td>
                  <div class="prize-cell">
                    <img v-if="row.img_url" class="prize-thumb" :src="row.img_url" alt="" />
                    <div v-else class="prize-thumb placeholder"><AppIcon name="gift" :size="16" /></div>
                    <div style="min-width: 0">
                      <p class="strong truncate">{{ row.name }}</p>
                      <p class="text-xs text-soft">
                        {{ row.prize_level || '未分级' }} · #{{ row.id }}
                      </p>
                    </div>
                  </div>
                </td>
                <td class="text-sm">
                  <div class="truncate">{{ activityName(row.activity_id) }}</div>
                  <div class="text-muted">{{ row.category_name || '未分类' }}</div>
                </td>
                <td><StatusBadge :map="PRIZE_TYPE" :value="row.prize_type" /></td>
                <td>
                  <div class="row-between text-xs mb-1">
                    <strong>{{ row.remain_stock }}</strong>
                    <span class="text-soft">/ {{ row.total_stock }}</span>
                  </div>
                  <div class="progress">
                    <div
                      class="progress-bar"
                      :class="stockPercent(row) <= 20 ? 'is-low' : ''"
                      :style="{ width: `${stockPercent(row)}%` }"
                    />
                  </div>
                </td>
                <td class="right strong">{{ row.weight }}</td>
                <td class="right text-sm">
                  <span v-if="row.daily_limit > 0" class="strong">{{ row.daily_limit }}</span>
                  <span v-else class="text-soft">不限</span>
                </td>
                <td><StatusBadge :map="PRIZE_STATUS" :value="row.status" /></td>
                <td>
                  <div class="cell-actions">
                    <button class="btn btn-sm btn-soft" type="button" @click="openStock(row)">
                      <AppIcon name="box" :size="14" /> 库存
                    </button>
                    <button class="btn btn-sm btn-ghost" type="button" @click="openEdit(row)">
                      <AppIcon name="edit" :size="14" />
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
    </template>

    <!-- ============ 分类 ============ -->
    <template v-else>
      <div class="toolbar mb-5">
        <button class="btn btn-primary" type="button" style="margin-left: auto" @click="openCategoryCreate">
          <AppIcon name="plus" :size="15" /> 新建分类
        </button>
      </div>

      <div v-if="!categories.length" class="card">
        <EmptyState icon="box" title="还没有奖品分类" desc="分类用于在奖品列表与用户端做分组展示" />
      </div>

      <div v-else class="card table-wrap">
        <table class="table">
          <thead>
            <tr>
              <th>分类名称</th>
              <th>描述</th>
              <th class="right">排序</th>
              <th>状态</th>
              <th>创建时间</th>
              <th class="right">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in categories" :key="row.id">
              <td class="strong">{{ row.name }}</td>
              <td class="text-sm text-muted">{{ row.description || '—' }}</td>
              <td class="right">{{ row.sort_order }}</td>
              <td><StatusBadge :map="PRIZE_STATUS" :value="row.status" /></td>
              <td class="text-sm nowrap">{{ formatDateTime(row.created_at) }}</td>
              <td>
                <div class="cell-actions">
                  <button class="btn btn-sm btn-ghost" type="button" @click="openCategoryEdit(row)">
                    <AppIcon name="edit" :size="14" /> 编辑
                  </button>
                  <button class="btn btn-sm btn-danger" type="button" @click="removeCategory(row)">
                    <AppIcon name="trash" :size="14" />
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>

    <!-- 奖品表单 -->
    <AppModal
      v-model="modalOpen"
      :title="isEdit ? '编辑奖品' : '新建奖品'"
      :desc="isEdit ? `奖品 #${editing?.id}` : '库存与权重决定中奖概率与数量上限'"
      size="lg"
    >
      <div class="form-grid">
        <div class="field">
          <label class="field-label" for="pr-activity">所属活动<span class="req">*</span></label>
          <select
            id="pr-activity"
            v-model="form.activity_id"
            class="select"
            :class="{ 'is-invalid': errors.activity_id }"
            :disabled="isEdit"
          >
            <option value="">请选择活动</option>
            <option v-for="a in activities" :key="a.id" :value="a.id">{{ a.name }}</option>
          </select>
          <p v-if="errors.activity_id" class="field-error">{{ errors.activity_id }}</p>
          <p v-else-if="isEdit" class="field-hint">所属活动不可修改</p>
        </div>

        <div class="field">
          <label class="field-label" for="pr-category">奖品分类</label>
          <select id="pr-category" v-model="form.category_id" class="select">
            <option value="">不分类</option>
            <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name }}</option>
          </select>
        </div>

        <div class="field">
          <label class="field-label" for="pr-name">奖品名称<span class="req">*</span></label>
          <input
            id="pr-name"
            v-model="form.name"
            class="input"
            :class="{ 'is-invalid': errors.name }"
            maxlength="128"
            placeholder="例如：一等奖 · 蓝牙耳机"
          />
          <p v-if="errors.name" class="field-error">{{ errors.name }}</p>
        </div>

        <div class="field">
          <label class="field-label" for="pr-level">奖品等级</label>
          <input id="pr-level" v-model="form.prize_level" class="input" maxlength="32" placeholder="一等奖" />
        </div>

        <div class="field">
          <label class="field-label" for="pr-type">奖品类型</label>
          <select id="pr-type" v-model="form.prize_type" class="select">
            <option value="physical">实物（需收货信息）</option>
            <option value="virtual">虚拟（仅需手机号）</option>
          </select>
        </div>

        <div class="field">
          <label class="field-label" for="pr-status">状态</label>
          <select id="pr-status" v-model="form.status" class="select" :disabled="!isEdit">
            <option value="enabled">启用</option>
            <option value="disabled">停用</option>
          </select>
          <p v-if="!isEdit" class="field-hint">创建后默认启用</p>
        </div>

        <div class="field">
          <label class="field-label" for="pr-stock">总库存</label>
          <input
            id="pr-stock"
            v-model.number="form.total_stock"
            class="input"
            type="number"
            min="0"
            :disabled="isEdit"
          />
          <p class="field-hint">{{ isEdit ? '库存请通过「库存」按钮调整（带乐观锁）' : '创建时同步作为剩余库存' }}</p>
        </div>

        <div class="field">
          <label class="field-label" for="pr-weight">中奖权重</label>
          <input id="pr-weight" v-model.number="form.weight" class="input" type="number" min="0" />
          <p class="field-hint">0 表示该奖品不参与抽奖</p>
        </div>

        <div class="field">
          <label class="field-label" for="pr-daily">每日中出上限</label>
          <input id="pr-daily" v-model.number="form.daily_limit" class="input" type="number" min="0" />
          <p class="field-hint">
            0 表示不限。达到上限后当天不再中出该奖品，库存自动回补；<strong>该字段仅管理端与运营可见</strong>，用户端不返回。
          </p>
        </div>

        <div class="field">
          <label class="field-label" for="pr-sort">排序</label>
          <input id="pr-sort" v-model.number="form.sort_order" class="input" type="number" min="0" />
        </div>

        <div class="field span-2">
          <label class="field-label" for="pr-desc">奖品描述</label>
          <textarea id="pr-desc" v-model="form.description" class="textarea" maxlength="2000" />
        </div>

        <div class="field span-2">
          <label class="field-label">奖品图片</label>
          <ImagePicker v-model="form.img_url" target="admin" height="150px" />
        </div>
      </div>

      <template #footer>
        <button class="btn" type="button" @click="modalOpen = false">取消</button>
        <button class="btn btn-primary" type="button" :disabled="saving" @click="save">
          <span v-if="saving" class="spinner spinner-light" />
          {{ saving ? '保存中…' : isEdit ? '保存修改' : '创建奖品' }}
        </button>
      </template>
    </AppModal>

    <!-- 库存调整 -->
    <AppModal
      v-model="stockOpen"
      title="调整库存"
      :desc="stockTarget ? `${stockTarget.name} · 当前剩余 ${stockTarget.remain_stock} / ${stockTarget.total_stock}` : ''"
      size="sm"
    >
      <div v-if="stockTarget" class="stack-sm">
        <div class="alert alert-info">
          <AppIcon class="alert-icon" name="info" :size="16" />
          <span>
            调整会同时作用于总库存与剩余库存，并自增版本号。提交时携带当前版本
            <span class="mono">{{ stockVersion }}</span>，并发冲突会返回 409。
          </span>
        </div>

        <div class="field">
          <label class="field-label" for="st-delta">调整数量</label>
          <div class="input-group">
            <button class="btn" type="button" @click="stockDelta = Number(stockDelta) - 10">-10</button>
            <button class="btn" type="button" @click="stockDelta = Number(stockDelta) - 1">-1</button>
            <input id="st-delta" v-model.number="stockDelta" class="input" type="number" />
            <button class="btn" type="button" @click="stockDelta = Number(stockDelta) + 1">+1</button>
            <button class="btn" type="button" @click="stockDelta = Number(stockDelta) + 10">+10</button>
          </div>
          <p class="field-hint">正数增加库存，负数减少库存</p>
        </div>

        <div class="preview">
          <span>调整后剩余库存</span>
          <strong>
            {{ Math.max(0, Number(stockTarget.remain_stock || 0) + Number(stockDelta || 0)) }}
          </strong>
        </div>
      </div>

      <template #footer>
        <button class="btn" type="button" @click="stockOpen = false">取消</button>
        <button class="btn btn-primary" type="button" :disabled="stockSaving" @click="submitStock">
          <span v-if="stockSaving" class="spinner spinner-light" />
          {{ stockSaving ? '提交中…' : '确认调整' }}
        </button>
      </template>
    </AppModal>

    <!-- 分类表单 -->
    <AppModal
      v-model="categoryModal"
      :title="categoryEditing ? '编辑分类' : '新建分类'"
      size="sm"
    >
      <div class="stack-sm">
        <div class="field">
          <label class="field-label" for="c-name">分类名称<span class="req">*</span></label>
          <input
            id="c-name"
            v-model="categoryForm.name"
            class="input"
            :class="{ 'is-invalid': categoryErrors.name }"
            maxlength="64"
            placeholder="例如：数码产品"
          />
          <p v-if="categoryErrors.name" class="field-error">{{ categoryErrors.name }}</p>
        </div>
        <div class="field">
          <label class="field-label" for="c-desc">描述</label>
          <input id="c-desc" v-model="categoryForm.description" class="input" maxlength="255" />
        </div>
        <div class="field">
          <label class="field-label" for="c-sort">排序</label>
          <input id="c-sort" v-model.number="categoryForm.sort_order" class="input" type="number" min="0" />
        </div>
        <div v-if="categoryEditing" class="field">
          <label class="field-label" for="c-status">状态</label>
          <select id="c-status" v-model="categoryForm.status" class="select">
            <option value="enabled">启用</option>
            <option value="disabled">停用</option>
          </select>
        </div>
      </div>

      <template #footer>
        <button class="btn" type="button" @click="categoryModal = false">取消</button>
        <button class="btn btn-primary" type="button" :disabled="categorySaving" @click="saveCategory">
          <span v-if="categorySaving" class="spinner spinner-light" />
          {{ categorySaving ? '保存中…' : '保存' }}
        </button>
      </template>
    </AppModal>
  </div>
</template>

<style scoped>
.prize-cell { display: flex; align-items: center; gap: 10px; min-width: 0; }
.prize-thumb {
  width: 38px;
  height: 38px;
  border-radius: var(--radius-xs);
  object-fit: cover;
  flex-shrink: 0;
  background: var(--surface-3);
}
.prize-thumb.placeholder { display: grid; place-items: center; color: var(--ink-400); }
.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--sp-4);
}
.span-2 { grid-column: span 2; }
.preview {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--sp-3) var(--sp-4);
  background: var(--brand-50);
  border-radius: var(--radius);
  font-size: 13.5px;
  color: var(--brand-800);
}
.preview strong { font-size: 20px; font-weight: 750; }
@media (max-width: 720px) {
  .form-grid { grid-template-columns: minmax(0, 1fr); }
  .span-2 { grid-column: span 1; }
}
</style>
