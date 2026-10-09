<script setup>
import AppIcon from '@/components/AppIcon.vue'
import { useRouter } from '@/router'

const router = useRouter()
</script>

<template>
  <div class="page">
    <div class="container">
      <div class="not-found card">
        <div class="code">404</div>
        <h1 class="page-title">页面不存在</h1>
        <p class="text-muted mt-2">你访问的地址可能已被移除，或者链接输入有误。</p>
        <div class="row gap-3 mt-5" style="justify-content: center">
          <button class="btn btn-primary" type="button" @click="router.push('/')">
            <AppIcon name="home" :size="15" />
            返回活动广场
          </button>
          <button class="btn" type="button" @click="router.back()">返回上一页</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.not-found {
  padding: var(--sp-10) var(--sp-6);
  text-align: center;
}
.code {
  font-size: 82px;
  font-weight: 800;
  line-height: 1;
  letter-spacing: -0.05em;
  background: linear-gradient(135deg, var(--brand-400), var(--brand-800));
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  margin-bottom: var(--sp-4);
}
</style>
