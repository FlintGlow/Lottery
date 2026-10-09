<script setup>
/**
 * 通用弹窗：Teleport 到 body，支持 ESC 关闭、点击遮罩关闭、滚动锁定。
 */
import { onBeforeUnmount, watch } from 'vue'
import AppIcon from './AppIcon.vue'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  title: { type: String, default: '' },
  desc: { type: String, default: '' },
  size: { type: String, default: 'md' }, // sm | md | lg
  closeOnMask: { type: Boolean, default: true },
})
const emit = defineEmits(['update:modelValue'])

function close() {
  emit('update:modelValue', false)
}

function onKeydown(event) {
  if (event.key === 'Escape') close()
}

watch(
  () => props.modelValue,
  (open) => {
    if (open) {
      document.addEventListener('keydown', onKeydown)
      document.body.style.overflow = 'hidden'
    } else {
      document.removeEventListener('keydown', onKeydown)
      document.body.style.overflow = ''
    }
  },
  { immediate: true },
)

onBeforeUnmount(() => {
  document.removeEventListener('keydown', onKeydown)
  document.body.style.overflow = ''
})
</script>

<template>
  <Teleport to="body">
    <Transition name="fade">
      <div
        v-if="modelValue"
        class="modal-mask"
        role="dialog"
        aria-modal="true"
        @click.self="closeOnMask && close()"
      >
        <Transition name="pop" appear>
          <div class="modal" :class="size === 'sm' ? 'modal-sm' : size === 'lg' ? 'modal-lg' : ''">
            <header class="modal-head">
              <div>
                <h3 class="modal-title">{{ title }}</h3>
                <p v-if="desc" class="modal-desc">{{ desc }}</p>
              </div>
              <button class="btn-icon btn" type="button" aria-label="关闭" @click="close">
                <AppIcon name="close" :size="17" />
              </button>
            </header>
            <div class="modal-body">
              <slot />
            </div>
            <footer v-if="$slots.footer" class="modal-foot">
              <slot name="footer" />
            </footer>
          </div>
        </Transition>
      </div>
    </Transition>
  </Teleport>
</template>
