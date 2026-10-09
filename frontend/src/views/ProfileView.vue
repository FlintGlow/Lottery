<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import AppIcon from '@/components/AppIcon.vue'
import ImagePicker from '@/components/ImagePicker.vue'
import LoadingBlock from '@/components/LoadingBlock.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'
import { useRouter } from '@/router'
import { ROLE_LABEL, ROLE_STATUS, USER_STATUS } from '@/utils/constants'
import { formatDateTime, initial } from '@/utils/format'

const auth = useAuthStore()
const toast = useToastStore()
const router = useRouter()

const loading = ref(true)
const savingProfile = ref(false)
const savingPassword = ref(false)
const tab = ref('profile')

const profile = reactive({ name: '', phone_number: '', avatar_url: '' })
const password = reactive({ old_password: '', new_password: '', confirm: '' })
const errors = reactive({})

const user = computed(() => auth.user)

const roleLabel = (code) => ROLE_LABEL[code] || code

async function load() {
  loading.value = true
  try {
    const me = await auth.fetchMe()
    if (me) {
      profile.name = me.username || ''
      profile.phone_number = me.phone_number || ''
      profile.avatar_url = me.avatar_url || ''
    }
  } catch (err) {
    toast.fromError(err, '资料加载失败')
  } finally {
    loading.value = false
  }
}

async function saveProfile() {
  Object.keys(errors).forEach((key) => delete errors[key])
  if (profile.name && !/^[a-zA-Z0-9_\u4e00-\u9fa5]{1,64}$/.test(profile.name)) {
    errors.name = '仅支持中文、字母、数字与下划线，最长 64 位'
  }
  if (profile.phone_number && !/^1[3-9]\d{9}$/.test(profile.phone_number)) {
    errors.phone_number = '请输入有效的 11 位手机号'
  }
  if (Object.keys(errors).length) return

  savingProfile.value = true
  try {
    const payload = {}
    if (profile.name && profile.name !== user.value?.username) payload.name = profile.name
    if (profile.phone_number && profile.phone_number !== user.value?.phone_number) {
      payload.phone_number = profile.phone_number
    }
    if (profile.avatar_url !== (user.value?.avatar_url || '')) payload.avatar_url = profile.avatar_url
    if (!Object.keys(payload).length) {
      toast.info('没有需要保存的修改')
      return
    }
    await auth.updateProfile(payload)
    toast.success('资料已更新')
  } catch (err) {
    toast.fromError(err, '保存失败')
  } finally {
    savingProfile.value = false
  }
}

async function savePassword() {
  Object.keys(errors).forEach((key) => delete errors[key])
  if (!password.old_password) errors.old_password = '请输入当前密码'
  if (!password.new_password) errors.new_password = '请输入新密码'
  else if (password.new_password.length < 8 || password.new_password.length > 64) {
    errors.new_password = '密码长度 8–64 位'
  }
  if (password.confirm !== password.new_password) errors.confirm = '两次输入的密码不一致'
  if (Object.keys(errors).length) return

  savingPassword.value = true
  try {
    await auth.changePassword({
      old_password: password.old_password,
      new_password: password.new_password,
    })
    toast.success('密码已修改，其它设备上的登录状态仍然有效')
    password.old_password = ''
    password.new_password = ''
    password.confirm = ''
  } catch (err) {
    toast.fromError(err, '修改失败')
  } finally {
    savingPassword.value = false
  }
}

async function onAvatarChange(url) {
  profile.avatar_url = url
  if (!url) return
  try {
    await auth.updateProfile({ avatar_url: url })
    toast.success('头像已更新')
  } catch (err) {
    toast.fromError(err, '头像保存失败')
  }
}

onMounted(load)
</script>

<template>
  <div class="page">
    <div class="container">
      <h1 class="page-title mb-5">个人中心</h1>

      <LoadingBlock v-if="loading" />

      <div v-else class="profile-grid">
        <!-- 概览卡 -->
        <aside class="card card-pad-lg overview">
          <div class="overview-head">
            <img v-if="user?.avatar_url" class="avatar avatar-lg" :src="user.avatar_url" alt="" />
            <span v-else class="avatar avatar-lg">{{ initial(user?.username) }}</span>
            <h2 class="overview-name">{{ user?.username }}</h2>
            <div class="row gap-2 wrap" style="justify-content: center">
              <StatusBadge :map="USER_STATUS" :value="user?.status" />
              <span class="badge badge-plain st-brand">{{ user?.id }}</span>
            </div>
          </div>

          <hr class="divider" />

          <div class="overview-body">
            <div class="kv">
              <span class="kv-key">手机号</span>
              <span class="kv-val">{{ user?.phone_number || '未绑定' }}</span>
            </div>
            <div class="kv">
              <span class="kv-key">注册时间</span>
              <span class="kv-val">{{ formatDateTime(user?.created_at) }}</span>
            </div>
            <div class="kv">
              <span class="kv-key">最后登录</span>
              <span class="kv-val">{{ formatDateTime(user?.last_login) }}</span>
            </div>
            <div class="kv">
              <span class="kv-key">拥有角色</span>
              <span class="kv-val">
                <template v-if="user?.roles?.length">
                  <span v-for="role in user.roles" :key="role.id" class="role-pill">
                    {{ roleLabel(role.code) }}
                  </span>
                </template>
                <template v-else>普通用户</template>
              </span>
            </div>
          </div>

          <hr class="divider" />

          <div class="overview-actions">
            <button class="btn btn-block" type="button" @click="router.push('/winnings')">
              <AppIcon name="trophy" :size="15" /> 我的奖品
            </button>
            <button class="btn btn-block" type="button" @click="router.push('/records')">
              <AppIcon name="ticket" :size="15" /> 抽奖记录
            </button>
            <button
              v-if="auth.isOperator"
              class="btn btn-block btn-soft"
              type="button"
              @click="router.push('/admin')"
            >
              <AppIcon name="chart" :size="15" /> 运营后台
            </button>
          </div>
        </aside>

        <!-- 编辑区 -->
        <section class="card">
          <div class="card-head">
            <div class="tabs" style="max-width: 320px">
              <button
                class="tab"
                :class="{ 'is-active': tab === 'profile' }"
                type="button"
                @click="tab = 'profile'"
              >
                基本资料
              </button>
              <button
                class="tab"
                :class="{ 'is-active': tab === 'password' }"
                type="button"
                @click="tab = 'password'"
              >
                修改密码
              </button>
            </div>
          </div>

          <div class="card-body">
            <!-- 资料 -->
            <form v-if="tab === 'profile'" class="stack" @submit.prevent="saveProfile">
              <div class="field">
                <label class="field-label">头像</label>
                <div class="avatar-row">
                  <ImagePicker
                    :model-value="profile.avatar_url"
                    target="user"
                    height="130px"
                    hint="建议使用 1:1 的正方形图片"
                    @update:model-value="onAvatarChange"
                  />
                </div>
              </div>

              <div class="field">
                <label class="field-label" for="p-name">用户名</label>
                <input
                  id="p-name"
                  v-model="profile.name"
                  class="input"
                  :class="{ 'is-invalid': errors.name }"
                  placeholder="中文、字母、数字或下划线"
                />
                <p v-if="errors.name" class="field-error">{{ errors.name }}</p>
                <p v-else class="field-hint">用户名全局唯一，修改后需使用新用户名登录</p>
              </div>

              <div class="field">
                <label class="field-label" for="p-phone">手机号</label>
                <input
                  id="p-phone"
                  v-model="profile.phone_number"
                  class="input"
                  :class="{ 'is-invalid': errors.phone_number }"
                  inputmode="numeric"
                  maxlength="11"
                  placeholder="11 位手机号"
                />
                <p v-if="errors.phone_number" class="field-error">{{ errors.phone_number }}</p>
                <p v-else class="field-hint">手机号用于登录与领奖联系</p>
              </div>

              <div class="row" style="justify-content: flex-end">
                <button class="btn btn-primary" type="submit" :disabled="savingProfile">
                  <span v-if="savingProfile" class="spinner spinner-light" />
                  {{ savingProfile ? '保存中…' : '保存修改' }}
                </button>
              </div>
            </form>

            <!-- 密码 -->
            <form v-else class="stack" @submit.prevent="savePassword">
              <div class="alert alert-info">
                <AppIcon class="alert-icon" name="info" :size="16" />
                <span>
                  修改密码后，已签发的访问令牌在有效期内仍然可用；如需强制下线，请在各设备上重新登录。
                </span>
              </div>

              <div class="field">
                <label class="field-label" for="old">当前密码<span class="req">*</span></label>
                <input
                  id="old"
                  v-model="password.old_password"
                  class="input"
                  :class="{ 'is-invalid': errors.old_password }"
                  type="password"
                  autocomplete="current-password"
                  placeholder="请输入当前密码"
                />
                <p v-if="errors.old_password" class="field-error">{{ errors.old_password }}</p>
              </div>

              <div class="field">
                <label class="field-label" for="new">新密码<span class="req">*</span></label>
                <input
                  id="new"
                  v-model="password.new_password"
                  class="input"
                  :class="{ 'is-invalid': errors.new_password }"
                  type="password"
                  autocomplete="new-password"
                  placeholder="8–64 位"
                />
                <p v-if="errors.new_password" class="field-error">{{ errors.new_password }}</p>
              </div>

              <div class="field">
                <label class="field-label" for="confirm">确认新密码<span class="req">*</span></label>
                <input
                  id="confirm"
                  v-model="password.confirm"
                  class="input"
                  :class="{ 'is-invalid': errors.confirm }"
                  type="password"
                  autocomplete="new-password"
                  placeholder="请再次输入新密码"
                />
                <p v-if="errors.confirm" class="field-error">{{ errors.confirm }}</p>
              </div>

              <div class="row" style="justify-content: flex-end">
                <button class="btn btn-primary" type="submit" :disabled="savingPassword">
                  <span v-if="savingPassword" class="spinner spinner-light" />
                  {{ savingPassword ? '提交中…' : '确认修改' }}
                </button>
              </div>
            </form>
          </div>
        </section>
      </div>
    </div>
  </div>
</template>

<style scoped>
.profile-grid {
  display: grid;
  grid-template-columns: minmax(0, 320px) minmax(0, 1fr);
  gap: var(--sp-5);
  align-items: start;
}
.overview-head {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--sp-3);
  text-align: center;
  padding-bottom: var(--sp-4);
}
.overview-name { font-size: 18px; font-weight: 700; }
.overview-body { padding-block: var(--sp-3); }
.overview-actions { display: flex; flex-direction: column; gap: var(--sp-2); padding-top: var(--sp-4); }
.role-pill {
  display: inline-flex;
  margin-left: 6px;
  padding: 2px 9px;
  border-radius: var(--radius-pill);
  background: var(--brand-50);
  color: var(--brand-700);
  font-size: 11.5px;
  font-weight: 650;
}
.avatar-row { max-width: 320px; }

@media (max-width: 940px) {
  .profile-grid { grid-template-columns: minmax(0, 1fr); }
}
</style>
