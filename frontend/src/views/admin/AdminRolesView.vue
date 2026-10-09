<script setup>
import { onMounted, reactive, ref } from 'vue'
import AppIcon from '@/components/AppIcon.vue'
import AppModal from '@/components/AppModal.vue'
import EmptyState from '@/components/EmptyState.vue'
import LoadingBlock from '@/components/LoadingBlock.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import { roleApi } from '@/api'
import { useConfirmStore } from '@/stores/confirm'
import { useToastStore } from '@/stores/toast'
import { ROLE_STATUS } from '@/utils/constants'

const toast = useToastStore()
const confirm = useConfirmStore()

const items = ref([])
const loading = ref(true)
const modalOpen = ref(false)
const editing = ref(null)
const saving = ref(false)
const errors = reactive({})

const form = reactive({ code: '', name: '', description: '', sort_order: 0, status: 'enabled' })

const PRESETS = [
  { code: 'admin', name: '管理员', description: '拥有全部权限，包括用户与角色管理' },
  { code: 'operator', name: '运营人员', description: '可管理活动、奖品、中奖发放与补发' },
  { code: 'user', name: '普通用户', description: '前台默认角色，可参与抽奖与领奖' },
]

const isEdit = ref(false)

async function load() {
  loading.value = true
  try {
    const list = await roleApi.list()
    items.value = Array.isArray(list) ? list : []
  } catch (err) {
    toast.fromError(err, '角色列表加载失败')
  } finally {
    loading.value = false
  }
}

function openCreate(preset) {
  isEdit.value = false
  editing.value = null
  Object.assign(form, {
    code: preset?.code || '',
    name: preset?.name || '',
    description: preset?.description || '',
    sort_order: 0,
    status: 'enabled',
  })
  Object.keys(errors).forEach((key) => delete errors[key])
  modalOpen.value = true
}

function openEdit(row) {
  isEdit.value = true
  editing.value = row
  Object.assign(form, {
    code: row.code,
    name: row.name || '',
    description: row.description || '',
    sort_order: row.sort_order ?? 0,
    status: row.status || 'enabled',
  })
  Object.keys(errors).forEach((key) => delete errors[key])
  modalOpen.value = true
}

async function save() {
  Object.keys(errors).forEach((key) => delete errors[key])
  if (!isEdit.value) {
    if (!form.code.trim()) errors.code = '请输入角色编码'
    else if (!/^[a-z][a-z0-9_]{1,31}$/.test(form.code.trim())) {
      errors.code = '小写字母开头，仅含小写字母、数字与下划线，2–32 位'
    }
  }
  if (!form.name.trim()) errors.name = '请输入角色名称'
  if (Object.keys(errors).length) return

  saving.value = true
  try {
    if (isEdit.value) {
      await roleApi.update(editing.value.id, {
        name: form.name.trim(),
        description: form.description.trim() || null,
        sort_order: Number(form.sort_order) || 0,
        status: form.status,
      })
      toast.success('角色已更新')
    } else {
      await roleApi.create({
        code: form.code.trim(),
        name: form.name.trim(),
        description: form.description.trim() || null,
        sort_order: Number(form.sort_order) || 0,
      })
      toast.success('角色已创建')
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
    title: '删除角色',
    message: `确认删除角色「${row.name}」吗？`,
    detail: '若该角色仍被用户使用，删除会被拒绝。删除为软删除。',
    confirmText: '删除',
    tone: 'danger',
  })
  if (!ok) return
  try {
    await roleApi.remove(row.id)
    toast.success('角色已删除')
    load()
  } catch (err) {
    toast.fromError(err, '删除失败')
  }
}

onMounted(load)
</script>

<template>
  <div>
    <div class="row-between wrap mb-5 gap-4">
      <div class="alert alert-info grow" style="max-width: 720px">
        <AppIcon class="alert-icon" name="info" :size="16" />
        <span>
          权限判定以角色编码（code）为准，且只统计状态为「启用」的角色。
          运营接口要求 <strong>operator</strong>，管理接口要求 <strong>admin</strong>。
        </span>
      </div>
      <button class="btn btn-primary" type="button" @click="openCreate()">
        <AppIcon name="plus" :size="15" /> 新建角色
      </button>
    </div>

    <div v-if="!items.length && !loading" class="card mb-5">
      <EmptyState icon="shield" title="还没有角色" desc="可以直接套用下面的常用角色模板">
        <div class="row gap-2 wrap" style="justify-content: center">
          <button
            v-for="preset in PRESETS"
            :key="preset.code"
            class="btn btn-sm"
            type="button"
            @click="openCreate(preset)"
          >
            创建 {{ preset.name }}
          </button>
        </div>
      </EmptyState>
    </div>

    <LoadingBlock v-if="loading" />

    <template v-else-if="items.length">
      <div class="card table-wrap">
        <table class="table">
          <thead>
            <tr>
              <th>角色名称</th>
              <th>编码</th>
              <th>描述</th>
              <th class="right">排序</th>
              <th>状态</th>
              <th class="right">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in items" :key="row.id">
              <td class="strong">{{ row.name }}</td>
              <td><span class="tag mono">{{ row.code }}</span></td>
              <td class="text-sm text-muted">{{ row.description || '—' }}</td>
              <td class="right">{{ row.sort_order }}</td>
              <td><StatusBadge :map="ROLE_STATUS" :value="row.status" /></td>
              <td>
                <div class="cell-actions">
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

      <section class="card card-pad mt-5">
        <h2 class="section-title mb-4">常用角色模板</h2>
        <div class="row gap-3 wrap">
          <button
            v-for="preset in PRESETS"
            :key="preset.code"
            class="preset"
            type="button"
            :disabled="items.some((r) => r.code === preset.code)"
            @click="openCreate(preset)"
          >
            <AppIcon name="shield" :size="16" />
            <span class="grow" style="text-align: left">
              <span class="strong">{{ preset.name }}</span>
              <span class="text-xs text-muted mono"> {{ preset.code }}</span>
              <span class="text-xs text-soft preset-desc">{{ preset.description }}</span>
            </span>
            <span class="text-xs text-soft">
              {{ items.some((r) => r.code === preset.code) ? '已存在' : '创建' }}
            </span>
          </button>
        </div>
      </section>
    </template>

    <AppModal
      v-model="modalOpen"
      :title="isEdit ? '编辑角色' : '新建角色'"
      :desc="isEdit ? `角色 #${editing?.id}，编码不可修改` : '角色编码一经创建不可修改'"
      size="sm"
    >
      <div class="stack-sm">
        <div class="field">
          <label class="field-label" for="ro-code">角色编码<span class="req">*</span></label>
          <input
            id="ro-code"
            v-model="form.code"
            class="input mono"
            :class="{ 'is-invalid': errors.code }"
            :disabled="isEdit"
            maxlength="32"
            placeholder="小写字母、数字、下划线"
          />
          <p v-if="errors.code" class="field-error">{{ errors.code }}</p>
        </div>
        <div class="field">
          <label class="field-label" for="ro-name">角色名称<span class="req">*</span></label>
          <input
            id="ro-name"
            v-model="form.name"
            class="input"
            :class="{ 'is-invalid': errors.name }"
            maxlength="64"
            placeholder="例如：运营人员"
          />
          <p v-if="errors.name" class="field-error">{{ errors.name }}</p>
        </div>
        <div class="field">
          <label class="field-label" for="ro-desc">描述</label>
          <input id="ro-desc" v-model="form.description" class="input" maxlength="255" />
        </div>
        <div class="field">
          <label class="field-label" for="ro-sort">排序</label>
          <input id="ro-sort" v-model.number="form.sort_order" class="input" type="number" min="0" />
        </div>
        <div v-if="isEdit" class="field">
          <label class="field-label" for="ro-status">状态</label>
          <select id="ro-status" v-model="form.status" class="select">
            <option value="enabled">启用</option>
            <option value="disabled">停用</option>
          </select>
          <p class="field-hint">停用后该角色不再参与权限判定</p>
        </div>
      </div>

      <template #footer>
        <button class="btn" type="button" @click="modalOpen = false">取消</button>
        <button class="btn btn-primary" type="button" :disabled="saving" @click="save">
          <span v-if="saving" class="spinner spinner-light" />
          {{ saving ? '保存中…' : '保存' }}
        </button>
      </template>
    </AppModal>
  </div>
</template>

<style scoped>
.preset {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 260px;
  flex: 1;
  padding: 11px 13px;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: var(--surface);
  color: var(--ink-700);
  cursor: pointer;
  transition: border-color var(--dur-fast) var(--ease), background var(--dur-fast) var(--ease);
}
.preset:hover:not(:disabled) { border-color: var(--brand-300); background: var(--brand-50); }
.preset:disabled { opacity: 0.55; cursor: not-allowed; }
.preset-desc { display: block; margin-top: 1px; }
</style>
