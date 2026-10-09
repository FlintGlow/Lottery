<script setup>
import { computed } from 'vue'
import { meta as metaOf } from '@/utils/constants'

const props = defineProps({
  map: { type: Object, required: true },
  value: { type: [String, Number, null], default: null },
  size: { type: String, default: 'md' }, // md | lg
  plain: { type: Boolean, default: false },
})

const info = computed(() => metaOf(props.map, props.value))
</script>

<template>
  <span class="badge" :class="[info.cls, size === 'lg' ? 'badge-lg' : '', plain ? 'badge-plain' : '']">
    {{ info.label }}
  </span>
</template>
