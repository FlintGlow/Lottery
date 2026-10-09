<script setup>
import AppIcon from './AppIcon.vue'
import { useToastStore } from '@/stores/toast'

const toast = useToastStore()

const ICONS = {
  success: 'checkCircle',
  error: 'alert',
  warning: 'alert',
  info: 'info',
}
</script>

<template>
  <div class="toast-host" role="status" aria-live="polite">
    <TransitionGroup name="pop">
      <div v-for="item in toast.items" :key="item.id" class="toast" :class="`toast-${item.type}`">
        <AppIcon class="toast-icon" :name="ICONS[item.type] || 'info'" :size="18" />
        <p class="toast-text">{{ item.message }}</p>
        <button class="toast-close" type="button" aria-label="关闭" @click="toast.remove(item.id)">
          <AppIcon name="close" :size="15" />
        </button>
      </div>
    </TransitionGroup>
  </div>
</template>
