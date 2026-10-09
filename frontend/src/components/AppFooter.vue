<script setup>
import AppIcon from './AppIcon.vue'

const year = new Date().getFullYear()
</script>

<template>
  <footer class="app-footer">
    <div class="container footer-inner">
      <div class="footer-brand">
        <span class="brand-mark">
          <AppIcon name="sparkles" :size="17" />
        </span>
        <div>
          <p class="strong">幸运抽奖系统</p>
          <p class="text-xs text-muted">公平 · 透明 · 实时开奖</p>
        </div>
      </div>
      <p class="text-xs text-muted">© {{ year }} Lucky Draw · 仅用于演示与内部使用</p>
    </div>
  </footer>
</template>

<style scoped>
.app-footer {
  border-top: 1px solid var(--border);
  background: var(--surface);
  padding-block: var(--sp-6);
}
.footer-inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--sp-4);
  flex-wrap: wrap;
}
.footer-brand { display: flex; align-items: center; gap: 10px; }
.brand-mark {
  display: grid;
  place-items: center;
  width: 32px;
  height: 32px;
  border-radius: 10px;
  background: linear-gradient(135deg, var(--brand-500), var(--brand-800));
  color: #fff;
}
</style>
