<script setup>
/**
 * 图片上传：点击或拖拽选择，前端先校验类型与大小（与后端限制一致），
 * 上传成功后通过 v-model 回传公开访问 URL。
 */
import { computed, ref } from 'vue'
import AppIcon from './AppIcon.vue'
import { fileApi } from '@/api'
import { useToastStore } from '@/stores/toast'

const props = defineProps({
  modelValue: { type: String, default: '' },
  target: { type: String, default: 'admin' }, // admin | user
  height: { type: String, default: '150px' },
  hint: { type: String, default: '支持 PNG / JPG / GIF / WEBP，不超过 5MB' },
})
const emit = defineEmits(['update:modelValue'])

const toast = useToastStore()
const uploading = ref(false)
const dragOver = ref(false)
const inputRef = ref(null)

const MAX_SIZE = 5 * 1024 * 1024
const ALLOWED = ['image/png', 'image/jpeg', 'image/gif', 'image/webp']

const preview = computed(() => props.modelValue || '')

function pick() {
  if (uploading.value) return
  inputRef.value?.click()
}

async function handleFiles(files) {
  const file = files?.[0]
  if (!file) return
  if (!ALLOWED.includes(file.type)) {
    toast.error('仅支持 PNG / JPG / GIF / WEBP 格式的图片')
    return
  }
  if (file.size > MAX_SIZE) {
    toast.error('图片大小不能超过 5MB')
    return
  }
  const form = new FormData()
  form.append('file', file)
  uploading.value = true
  try {
    const result = props.target === 'user'
      ? await fileApi.uploadUserImage(form)
      : await fileApi.uploadAdminImage(form)
    emit('update:modelValue', result?.url || '')
    toast.success('上传成功')
  } catch (error) {
    toast.fromError(error, '上传失败')
  } finally {
    uploading.value = false
    if (inputRef.value) inputRef.value.value = ''
  }
}

function onDrop(event) {
  dragOver.value = false
  handleFiles(event.dataTransfer?.files)
}

function clear() {
  emit('update:modelValue', '')
}
</script>

<template>
  <div class="image-picker">
    <div
      class="drop-zone"
      :class="{ 'is-over': dragOver, 'is-uploading': uploading }"
      :style="{ minHeight: height }"
      role="button"
      tabindex="0"
      @click="pick"
      @keydown.enter.prevent="pick"
      @keydown.space.prevent="pick"
      @dragover.prevent="dragOver = true"
      @dragleave.prevent="dragOver = false"
      @drop.prevent="onDrop"
    >
      <img v-if="preview" class="preview" :src="preview" alt="预览" />
      <div v-else class="placeholder">
        <AppIcon :name="uploading ? 'refresh' : 'image'" :size="22" :class="{ spin: uploading }" />
        <p class="text-sm strong">{{ uploading ? '上传中…' : '点击或拖拽图片到此处' }}</p>
        <p class="text-xs text-soft">{{ hint }}</p>
      </div>
      <div v-if="uploading" class="mask"><span class="spinner spinner-light" /></div>
    </div>
    <div v-if="preview" class="actions">
      <button class="btn btn-sm" type="button" @click="pick">
        <AppIcon name="refresh" :size="14" /> 更换
      </button>
      <button class="btn btn-sm btn-danger" type="button" @click="clear">
        <AppIcon name="trash" :size="14" /> 清除
      </button>
    </div>
    <input
      ref="inputRef"
      class="sr-only"
      type="file"
      accept="image/png,image/jpeg,image/gif,image/webp"
      @change="handleFiles($event.target.files)"
    />
  </div>
</template>

<style scoped>
.image-picker { display: flex; flex-direction: column; gap: 8px; }
.drop-zone {
  position: relative;
  display: grid;
  place-items: center;
  border: 1.5px dashed var(--border-strong);
  border-radius: var(--radius);
  background: var(--surface-2);
  cursor: pointer;
  overflow: hidden;
  transition: border-color var(--dur-fast) var(--ease), background var(--dur-fast) var(--ease);
}
.drop-zone:hover,
.drop-zone.is-over {
  border-color: var(--brand-400);
  background: var(--brand-50);
}
.placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 5px;
  color: var(--ink-500);
  padding: var(--sp-5);
  text-align: center;
}
.preview { width: 100%; height: 100%; max-height: 240px; object-fit: contain; padding: 6px; }
.mask {
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
  background: rgba(26, 23, 48, 0.35);
}
.actions { display: flex; gap: 8px; }
.spin { animation: spin 0.9s linear infinite; }
</style>
