<script setup>
/** 懒加载路由的占位视图，避免切换页面时出现空白闪烁 */
import LoadingBlock from './LoadingBlock.vue'
</script>

<template>
  <div class="page">
    <div class="container">
      <LoadingBlock text="页面加载中…" min-height="52vh" />
    </div>
  </div>
</template>
