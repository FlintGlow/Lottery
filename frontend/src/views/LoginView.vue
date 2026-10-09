<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import AppIcon from '@/components/AppIcon.vue'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'
import { useRoute, useRouter } from '@/router'

const auth = useAuthStore()
const toast = useToastStore()
const router = useRouter()
const route = useRoute()

const tab = ref('login')
const showPassword = ref(false)
const submitting = ref(false)
const formError = ref('')

const loginForm = reactive({ account: '', password: '' })
const registerForm = reactive({ username: '', password: '', confirm: '', phone_number: '' })

const errors = reactive({})

const HIGHLIGHTS = [
  { icon: 'sparkles', title: '实时开奖', desc: 'Redis 预扣 + 异步落库，结果秒级可查' },
  { icon: 'shield', title: '库存透明', desc: '每件奖品的剩余数量与中出情况公开可查' },
  { icon: 'trophy', title: '在线领奖', desc: '实物奖品提交收货信息，运营侧跟进发放' },
]

const isLogin = computed(() => tab.value === 'login')

function switchTab(next) {
  tab.value = next
  formError.value = ''
  Object.keys(errors).forEach((key) => delete errors[key])
}

function validateLogin() {
  Object.keys(errors).forEach((key) => delete errors[key])
  if (!loginForm.account.trim()) errors.account = '请输入用户名或手机号'
  if (!loginForm.password) errors.password = '请输入密码'
  else if (loginForm.password.length < 8) errors.password = '密码至少 8 位'
  return !Object.keys(errors).length
}

function validateRegister() {
  Object.keys(errors).forEach((key) => delete errors[key])
  const { username, password, confirm, phone_number } = registerForm
  if (!username) errors.username = '请输入用户名'
  else if (!/^[a-zA-Z0-9_-]{3,64}$/.test(username)) {
    errors.username = '3–64 位，仅支持字母、数字、下划线与连字符'
  }
  if (!password) errors.password = '请输入密码'
  else if (password.length < 8 || password.length > 64) errors.password = '密码长度 8–64 位'
  if (confirm !== password) errors.confirm = '两次输入的密码不一致'
  if (!phone_number) errors.phone_number = '请输入手机号'
  else if (!/^1[3-9]\d{9}$/.test(phone_number)) errors.phone_number = '请输入有效的 11 位手机号'
  return !Object.keys(errors).length
}

async function submit() {
  formError.value = ''
  if (isLogin.value ? !validateLogin() : !validateRegister()) return

  submitting.value = true
  try {
    if (isLogin.value) {
      await auth.login({ account: loginForm.account.trim(), password: loginForm.password })
      toast.success('登录成功')
    } else {
      await auth.register({
        username: registerForm.username.trim(),
        password: registerForm.password,
        phone_number: registerForm.phone_number.trim(),
      })
      toast.success('注册成功，已自动登录')
    }
    const redirect = route.query.redirect
    router.push(redirect && redirect.startsWith('/') ? redirect : '/')
  } catch (err) {
    formError.value = err?.message || '操作失败，请稍后重试'
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  if (route.query.tab === 'register') tab.value = 'register'
})
</script>

<template>
  <div class="auth">
    <!-- 左侧品牌区 -->
    <aside class="auth-aside">
      <div class="aside-inner">
        <a class="aside-brand" href="#/" @click.prevent="router.push('/')">
          <span class="brand-mark"><AppIcon name="sparkles" :size="20" /></span>
          <div>
            <strong>幸运抽奖系统</strong>
            <small>LUCKY DRAW PLATFORM</small>
          </div>
        </a>

        <div class="aside-copy">
          <h1>每一次点击<br />都可能遇见惊喜</h1>
          <p>登录后即可参与活动抽奖、查看中奖记录，并在线上完成领奖。</p>
        </div>

        <ul class="aside-list">
          <li v-for="item in HIGHLIGHTS" :key="item.title">
            <span class="aside-icon"><AppIcon :name="item.icon" :size="17" /></span>
            <div>
              <p class="strong">{{ item.title }}</p>
              <p class="text-xs">{{ item.desc }}</p>
            </div>
          </li>
        </ul>
      </div>
      <div class="aside-glow" aria-hidden="true" />
    </aside>

    <!-- 右侧表单 -->
    <section class="auth-main">
      <div class="auth-card">
        <div class="tabs">
          <button
            class="tab"
            :class="{ 'is-active': isLogin }"
            type="button"
            @click="switchTab('login')"
          >
            登录
          </button>
          <button
            class="tab"
            :class="{ 'is-active': !isLogin }"
            type="button"
            @click="switchTab('register')"
          >
            注册
          </button>
        </div>

        <div class="auth-head">
          <h2>{{ isLogin ? '欢迎回来' : '创建账号' }}</h2>
          <p class="text-sm text-muted">
            {{ isLogin ? '使用用户名或手机号登录' : '填写以下信息，注册后自动登录' }}
          </p>
        </div>

        <div v-if="formError" class="alert alert-danger mb-4">
          <AppIcon class="alert-icon" name="alert" :size="16" />
          <span>{{ formError }}</span>
        </div>

        <form class="stack-sm" @submit.prevent="submit">
          <template v-if="isLogin">
            <div class="field">
              <label class="field-label" for="account">用户名或手机号</label>
              <input
                id="account"
                v-model="loginForm.account"
                class="input"
                :class="{ 'is-invalid': errors.account }"
                autocomplete="username"
                placeholder="请输入用户名或手机号"
              />
              <p v-if="errors.account" class="field-error">{{ errors.account }}</p>
            </div>
            <div class="field">
              <label class="field-label" for="password">密码</label>
              <div class="password-wrap">
                <input
                  id="password"
                  v-model="loginForm.password"
                  class="input"
                  :class="{ 'is-invalid': errors.password }"
                  :type="showPassword ? 'text' : 'password'"
                  autocomplete="current-password"
                  placeholder="请输入密码"
                />
                <button
                  class="eye"
                  type="button"
                  :aria-label="showPassword ? '隐藏密码' : '显示密码'"
                  @click="showPassword = !showPassword"
                >
                  <AppIcon :name="showPassword ? 'eyeOff' : 'eye'" :size="16" />
                </button>
              </div>
              <p v-if="errors.password" class="field-error">{{ errors.password }}</p>
            </div>
          </template>

          <template v-else>
            <div class="field">
              <label class="field-label" for="username">用户名<span class="req">*</span></label>
              <input
                id="username"
                v-model="registerForm.username"
                class="input"
                :class="{ 'is-invalid': errors.username }"
                autocomplete="username"
                placeholder="3–64 位字母、数字、下划线或连字符"
              />
              <p v-if="errors.username" class="field-error">{{ errors.username }}</p>
            </div>
            <div class="field">
              <label class="field-label" for="phone">手机号<span class="req">*</span></label>
              <input
                id="phone"
                v-model="registerForm.phone_number"
                class="input"
                :class="{ 'is-invalid': errors.phone_number }"
                inputmode="numeric"
                maxlength="11"
                placeholder="11 位手机号"
              />
              <p v-if="errors.phone_number" class="field-error">{{ errors.phone_number }}</p>
            </div>
            <div class="field">
              <label class="field-label" for="reg-password">密码<span class="req">*</span></label>
              <div class="password-wrap">
                <input
                  id="reg-password"
                  v-model="registerForm.password"
                  class="input"
                  :class="{ 'is-invalid': errors.password }"
                  :type="showPassword ? 'text' : 'password'"
                  autocomplete="new-password"
                  placeholder="8–64 位"
                />
                <button
                  class="eye"
                  type="button"
                  :aria-label="showPassword ? '隐藏密码' : '显示密码'"
                  @click="showPassword = !showPassword"
                >
                  <AppIcon :name="showPassword ? 'eyeOff' : 'eye'" :size="16" />
                </button>
              </div>
              <p v-if="errors.password" class="field-error">{{ errors.password }}</p>
            </div>
            <div class="field">
              <label class="field-label" for="confirm">确认密码<span class="req">*</span></label>
              <input
                id="confirm"
                v-model="registerForm.confirm"
                class="input"
                :class="{ 'is-invalid': errors.confirm }"
                :type="showPassword ? 'text' : 'password'"
                autocomplete="new-password"
                placeholder="请再次输入密码"
              />
              <p v-if="errors.confirm" class="field-error">{{ errors.confirm }}</p>
            </div>
          </template>

          <button class="btn btn-lg btn-primary btn-block mt-2" type="submit" :disabled="submitting">
            <span v-if="submitting" class="spinner spinner-light" />
            {{ submitting ? '处理中…' : isLogin ? '登录' : '注册并登录' }}
          </button>
        </form>

        <p class="auth-foot text-sm text-muted">
          {{ isLogin ? '还没有账号？' : '已经有账号了？' }}
          <button class="link-btn" type="button" @click="switchTab(isLogin ? 'register' : 'login')">
            {{ isLogin ? '立即注册' : '去登录' }}
          </button>
        </p>

        <button class="back-home" type="button" @click="router.push('/')">
          <AppIcon name="chevronLeft" :size="15" />
          返回活动广场
        </button>
      </div>
    </section>
  </div>
</template>

<style scoped>
.auth {
  display: grid;
  grid-template-columns: minmax(0, 1.05fr) minmax(0, 1fr);
  min-height: 100vh;
}

/* ---------- 左 ---------- */
.auth-aside {
  position: relative;
  overflow: hidden;
  background: linear-gradient(150deg, #2a1a5e 0%, #4c1d95 52%, #6d28d9 100%);
  color: #fff;
  padding: var(--sp-8) var(--sp-9);
  display: flex;
  align-items: center;
}
.aside-glow {
  position: absolute;
  width: 520px;
  height: 520px;
  right: -180px;
  bottom: -200px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(251, 191, 36, 0.42), transparent 68%);
  filter: blur(50px);
  pointer-events: none;
}
.aside-inner { position: relative; max-width: 460px; }
.aside-brand { display: flex; align-items: center; gap: 11px; color: #fff; }
.aside-brand:hover { color: #fff; }
.aside-brand strong { display: block; font-size: 16px; font-weight: 700; }
.aside-brand small {
  font-size: 10px;
  letter-spacing: 0.16em;
  color: rgba(255, 255, 255, 0.55);
  font-weight: 600;
}
.brand-mark {
  display: grid;
  place-items: center;
  width: 42px;
  height: 42px;
  border-radius: 13px;
  background: rgba(255, 255, 255, 0.16);
  border: 1px solid rgba(255, 255, 255, 0.22);
}
.aside-copy { margin-top: var(--sp-9); }
.aside-copy h1 {
  font-size: clamp(26px, 2.6vw, 36px);
  font-weight: 750;
  line-height: 1.28;
  letter-spacing: -0.03em;
  color: #fff;
}
.aside-copy p {
  margin-top: var(--sp-4);
  font-size: 14.5px;
  line-height: 1.8;
  color: rgba(255, 255, 255, 0.72);
}
.aside-list {
  margin-top: var(--sp-8);
  display: flex;
  flex-direction: column;
  gap: var(--sp-4);
}
.aside-list li { display: flex; gap: 12px; }
.aside-list p { color: rgba(255, 255, 255, 0.72); }
.aside-list .strong { color: #fff; }
.aside-icon {
  display: grid;
  place-items: center;
  width: 34px;
  height: 34px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.13);
  flex-shrink: 0;
}

/* ---------- 右 ---------- */
.auth-main {
  display: grid;
  place-items: center;
  padding: var(--sp-8) var(--sp-6);
  background: var(--bg);
}
.auth-card {
  width: 100%;
  max-width: 420px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-md);
  padding: var(--sp-6);
}
.auth-head { margin-top: var(--sp-5); margin-bottom: var(--sp-5); }
.auth-head h2 { font-size: 21px; font-weight: 720; letter-spacing: -0.02em; }
.auth-head p { margin-top: 3px; }

.password-wrap { position: relative; }
.password-wrap .input { padding-right: 40px; }
.eye {
  position: absolute;
  right: 6px;
  top: 50%;
  transform: translateY(-50%);
  width: 30px;
  height: 30px;
  display: grid;
  place-items: center;
  border: 0;
  background: transparent;
  color: var(--ink-400);
  border-radius: var(--radius-xs);
  cursor: pointer;
}
.eye:hover { color: var(--ink-700); background: var(--ink-100); }

.auth-foot { margin-top: var(--sp-5); text-align: center; }
.link-btn {
  border: 0;
  background: transparent;
  color: var(--brand-700);
  font-weight: 650;
  cursor: pointer;
  padding: 0 2px;
}
.link-btn:hover { text-decoration: underline; }
.back-home {
  display: flex;
  align-items: center;
  gap: 4px;
  margin: var(--sp-5) auto 0;
  border: 0;
  background: transparent;
  color: var(--text-muted);
  font-size: 13px;
  cursor: pointer;
}
.back-home:hover { color: var(--brand-700); }

@media (max-width: 940px) {
  .auth { grid-template-columns: minmax(0, 1fr); }
  .auth-aside { display: none; }
}
</style>
