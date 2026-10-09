<script setup>
/** 全局确认框：由 confirm store 驱动，业务侧 await confirm.ask(...) 即可 */
import { useConfirmStore } from '@/stores/confirm'
import AppIcon from './AppIcon.vue'

const confirm = useConfirmStore()
</script>

<template>
  <Teleport to="body">
    <Transition name="fade">
      <div v-if="confirm.state.open" class="modal-mask" @click.self="confirm.cancel()">
        <Transition name="pop" appear>
          <div class="modal modal-sm">
            <div class="modal-head">
              <div class="row gap-2" style="align-items: flex-start">
                <span
                  class="confirm-icon"
                  :class="confirm.state.tone === 'danger' ? 'is-danger' : 'is-brand'"
                >
                  <AppIcon
                    :name="confirm.state.tone === 'danger' ? 'alert' : 'info'"
                    :size="18"
                  />
                </span>
                <div>
                  <h3 class="modal-title">{{ confirm.state.title }}</h3>
                  <p v-if="confirm.state.message" class="modal-desc">{{ confirm.state.message }}</p>
                </div>
              </div>
            </div>
            <div v-if="confirm.state.detail" class="modal-body">
              <div class="alert alert-info">
                <AppIcon class="alert-icon" name="info" :size="16" />
                <span>{{ confirm.state.detail }}</span>
              </div>
            </div>
            <div class="modal-foot">
              <button class="btn" type="button" @click="confirm.cancel()">
                {{ confirm.state.cancelText }}
              </button>
              <button
                class="btn"
                :class="confirm.state.tone === 'danger' ? 'btn-danger-solid' : 'btn-primary'"
                type="button"
                @click="confirm.confirm()"
              >
                {{ confirm.state.confirmText }}
              </button>
            </div>
          </div>
        </Transition>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.confirm-icon {
  display: grid;
  place-items: center;
  width: 34px;
  height: 34px;
  border-radius: 50%;
  flex-shrink: 0;
}
.confirm-icon.is-brand {
  background: var(--brand-50);
  color: var(--brand-700);
}
.confirm-icon.is-danger {
  background: var(--danger-50);
  color: var(--danger-600);
}
</style>
