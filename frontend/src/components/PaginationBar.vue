<script setup>
import { computed } from 'vue'
import AppIcon from './AppIcon.vue'

const props = defineProps({
  page: { type: Number, default: 1 },
  pageSize: { type: Number, default: 20 },
  total: { type: Number, default: 0 },
  unit: { type: String, default: '条' },
})
const emit = defineEmits(['update:page'])

const pages = computed(() => Math.max(1, Math.ceil(props.total / props.pageSize)))

const items = computed(() => {
  const last = pages.value
  const current = props.page
  if (last <= 7) return Array.from({ length: last }, (_, i) => i + 1)
  const list = [1]
  const start = Math.max(2, current - 1)
  const end = Math.min(last - 1, current + 1)
  if (start > 2) list.push('…')
  for (let i = start; i <= end; i += 1) list.push(i)
  if (end < last - 1) list.push('…')
  list.push(last)
  return list
})

const from = computed(() => (props.total === 0 ? 0 : (props.page - 1) * props.pageSize + 1))
const to = computed(() => Math.min(props.page * props.pageSize, props.total))

function go(target) {
  if (typeof target !== 'number') return
  if (target < 1 || target > pages.value || target === props.page) return
  emit('update:page', target)
}
</script>

<template>
  <div v-if="total > 0" class="pagination">
    <p class="pagination-info">
      共 <strong>{{ total }}</strong> {{ unit }} · 当前 {{ from }}–{{ to }}
    </p>
    <div class="pagination-list">
      <button
        class="page-btn"
        type="button"
        :disabled="page <= 1"
        aria-label="上一页"
        @click="go(page - 1)"
      >
        <AppIcon name="chevronLeft" :size="15" />
      </button>
      <template v-for="(item, index) in items" :key="`${item}-${index}`">
        <span v-if="item === '…'" class="page-ellipsis">…</span>
        <button
          v-else
          class="page-btn"
          :class="{ 'is-active': item === page }"
          type="button"
          @click="go(item)"
        >
          {{ item }}
        </button>
      </template>
      <button
        class="page-btn"
        type="button"
        :disabled="page >= pages"
        aria-label="下一页"
        @click="go(page + 1)"
      >
        <AppIcon name="chevronRight" :size="15" />
      </button>
    </div>
  </div>
</template>
