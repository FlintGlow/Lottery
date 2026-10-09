<script setup>
import { onMounted, reactive, ref } from 'vue'
import AppIcon from '@/components/AppIcon.vue'
import AppModal from '@/components/AppModal.vue'
import EmptyState from '@/components/EmptyState.vue'
import LoadingBlock from '@/components/LoadingBlock.vue'
import PaginationBar from '@/components/PaginationBar.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import { roleApi, userApi } from '@/api'
import { useConfirmStore } from '@/stores/confirm'
import { useToastStore } from '@/stores/toast'
import { ADMIN_PAGE_SIZE, ROLE_LABEL, USER_STATUS } from '@/utils/constants'
import { formatDateTime, initial, maskPhone } from '@/utils/format'

const toast = useToastStore()
const confirm = useConfirmStore()

const items = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(ADMIN_PAGE_SIZE)
const filters = reactive({ keyword: '', status: '' })
const loading = ref(true)
const roles = ref([])

const roleModal = ref(false)
const current = ref(null)
const selectedRoles = ref([])
const saving = ref(false)

async function loadRoles() {
  try {
    const list = await roleApi.list()
    roles.value = Array.isArray(list) ? list : []
  } catch {
    roles.value = []
  }
}

async function load() {
  loading.value = true
  try {
    const data = await userApi.list({
      page: page.value,
      page_size: pageSize.value,
      keyword: filters.keyword || undefined,
      status: filters.status || undefined,
    })
    items.value = data?.items || []
    total.value = data?.total || 0
  } catch (err) {
    toast.fromError(err, '用户列表加载失败')
  } finally {
    loading.value = false
  }
}

function changePage(next) {
  page.value = next
  load()
}

function resetFilters() {
  filters.keyword = ''
  filters.status = ''
  page.value = 1
  load()
}

const roleLabel = (code) => ROLE_LABEL[code] || code

async function toggleStatus(row) {
  const next = row.status === 'active' ? 'disabled' : 'active'
  const label = next === 'active' ? '启用' : '禁用'
  const ok = await confirm.ask({
    title: `${label}用户`,
    message: `确认${label}「${row.username}」吗？`,
    detail: next === 'disabled' ? '禁用后该用户将无法登录，已签发的令牌也会失效。' : '',
    confirmText: `确认${label}`,
    tone: next === 'disabled' ? 'danger' : 'primary',
  })
  if (!ok) return
  try {
    await userApi.updateStatus(row.id, next)
    toast.success(`已${label}`)
    load()
  } catch (err) {
    toast.fromError(err, `${label}失败`)
  }
}

function openRoles(row) {
  current.value = row
  selectedRoles.value = (row.roles || []).map((role) => role.code)
  roleModal.value = true
}

function toggleRole(code) {
  const index = selectedRoles.value.indexOf(code)
  if (index >= 0) selectedRoles.value.splice(index, 1)
  else selectedRoles.value.push(code)
}

async function saveRoles() {
  if (!selectedRoles.value.length) {
    toast.warning('请至少选择一个角色')
    return
  }
  saving.value = true
  try {
    await userApi.updateRoles(current.value.id, selectedRoles.value)
    toast.success('角色已更新')
    roleModal.value = false
    load()
  } catch (err) {
    toast.fromError(err, '角色更新失败')
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  await loadRoles()
  await load()
})
</script>

<template>
  <div>
    <div class="toolbar mb-5">
      <input
        v-model="filters.keyword"
        class="input"
        type="search"
        placeholder="搜索用户名或手机号"
        @keyup.enter="page = 1; load()"
      />
      <select v-model="filters.status" class="select" @change="page = 1; load()">
        <option value="">全部状态</option>
        <option v-for="(meta, key) in USER_STATUS" :key="key" :value="key">{{ meta.label }}</option>
      </select>
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
      <EmptyState icon="users" title="没有找到用户" desc="调整筛选条件后再试" />
    </div>

    <template v-else>
      <div class="card table-wrap">
        <table class="table">
          <thead>
            <tr>
              <th>用户</th>
              <th>手机号</th>
              <th>角色</th>
              <th>状态</th>
              <th>注册时间</th>
              <th>最后登录</th>
              <th class="right">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in items" :key="row.id">
              <td>
                <div class="user-cell">
                  <img v-if="row.avatar_url" class="avatar avatar-sm" :src="row.avatar_url" alt="" />
                  <span v-else class="avatar avatar-sm">{{ initial(row.username) }}</span>
                  <div style="min-width: 0">
                    <p class="strong truncate">{{ row.username }}</p>
                    <p class="text-xs text-soft mono">#{{ row.id }}</p>
                  </div>
                </div>
              </td>
              <td class="text-sm">{{ maskPhone(row.phone_number) }}</td>
              <td>
                <div class="row gap-1 wrap">
                  <span v-for="role in row.roles" :key="role.id" class="tag">{{ roleLabel(role.code) }}</span>
                  <span v-if="!row.roles?.length" class="text-xs text-soft">无角色</span>
                </div>
              </td>
              <td><StatusBadge :map="USER_STATUS" :value="row.status" /></td>
              <td class="text-sm nowrap">{{ formatDateTime(row.created_at) }}</td>
              <td class="text-sm nowrap">{{ row.last_login ? formatDateTime(row.last_login) : '从未登录' }}</td>
              <td>
                <div class="cell-actions">
                  <button class="btn btn-sm btn-soft" type="button" @click="openRoles(row)">
                    <AppIcon name="shield" :size="14" /> 角色
                  </button>
                  <button
                    class="btn btn-sm"
                    :class="row.status === 'active' ? 'btn-danger' : 'btn-primary'"
                    type="button"
                    @click="toggleStatus(row)"
                  >
                    {{ row.status === 'active' ? '禁用' : '启用' }}
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <PaginationBar :page="page" :page-size="pageSize" :total="total" @update:page="changePage" />
    </template>

    <!-- 角色分配 -->
    <AppModal
      v-model="roleModal"
      title="分配角色"
      :desc="current ? `用户 ${current.username}（#${current.id}）` : ''"
      size="sm"
    >
      <div class="stack-sm">
        <div class="alert alert-info">
          <AppIcon class="alert-icon" name="info" :size="16" />
          <span>
            角色为整体覆盖：提交后该用户的角色列表即为下方勾选项。运营接口需要
            <strong>operator</strong>，管理接口需要 <strong>admin</strong>。
          </span>
        </div>
        <label v-for="role in roles" :key="role.id" class="role-option">
          <input
            type="checkbox"
            :checked="selectedRoles.includes(role.code)"
            @change="toggleRole(role.code)"
          />
          <span class="grow">
            <span class="strong">{{ role.name }}</span>
            <span class="text-xs text-muted mono"> {{ role.code }}</span>
            <span v-if="role.description" class="text-xs text-soft"> · {{ role.description }}</span>
          </span>
          <StatusBadge :map="{ enabled: { label: '启用', cls: 'st-success' }, disabled: { label: '停用', cls: 'st-neutral' } }" :value="role.status" />
        </label>
        <p v-if="!roles.length" class="text-sm text-muted">
          还没有角色，请先到「角色管理」创建。
        </p>
      </div>

      <template #footer>
        <button class="btn" type="button" @click="roleModal = false">取消</button>
        <button class="btn btn-primary" type="button" :disabled="saving" @click="saveRoles">
          <span v-if="saving" class="spinner spinner-light" />
          {{ saving ? '保存中…' : '保存' }}
        </button>
      </template>
    </AppModal>
  </div>
</template>

<style scoped>
.user-cell { display: flex; align-items: center; gap: 9px; min-width: 0; }
.role-option {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: border-color var(--dur-fast) var(--ease), background var(--dur-fast) var(--ease);
}
.role-option:hover { border-color: var(--brand-300); background: var(--brand-50); }
.role-option input { width: 16px; height: 16px; accent-color: var(--brand-600); flex-shrink: 0; }
</style>
