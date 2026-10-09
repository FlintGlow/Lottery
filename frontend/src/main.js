import './styles/tokens.css'
import './styles/base.css'
import './styles/components.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'

const app = createApp(App)

app.use(createPinia())

// 先解析当前地址，再挂载：首屏就能拿到正确的路由（登录守卫需要 pinia 已就绪）
router.start()
app.mount('#app')

// 令牌彻底失效时统一跳转登录页
window.addEventListener('lottery:unauthorized', () => {
  if (!window.location.hash.startsWith('#/login')) {
    router.push(`/login?redirect=${encodeURIComponent(router.current.path)}`)
  }
})
