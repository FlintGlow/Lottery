<script setup>
defineProps({
  text: { type: String, default: '加载中…' },
  minHeight: { type: String, default: '220px' },
})
</script>

<template>
  <div class="loading-block" :style="{ minHeight }">
    <span class="spinner" />
    <span>{{ text }}</span>
  </div>
</template>
