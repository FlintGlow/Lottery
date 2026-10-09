<script setup>
import { computed } from 'vue'
import AppIcon from './AppIcon.vue'
import StatusBadge from './StatusBadge.vue'
import { PRIZE_TYPE } from '@/utils/constants'

const props = defineProps({
  prize: { type: Object, required: true },
  /** 展示剩余库存（用户端）或库存进度（管理端） */
  variant: { type: String, default: 'public' }, // public | admin
})

const level = computed(() => props.prize.prize_level || props.prize.level || '')
const remain = computed(() => Number(props.prize.remain_stock ?? 0))
const total = computed(() => Number(props.prize.total_stock ?? 0))
const soldOut = computed(() => remain.value <= 0)

const percent = computed(() => {
  if (!total.value) return 0
  return Math.max(0, Math.min(100, Math.round((remain.value / total.value) * 100)))
})

const tone = computed(() => {
  if (soldOut.value) return 'is-out'
  if (percent.value <= 20) return 'is-low'
  return ''
})
</script>

<template>
  <article class="prize-card" :class="{ 'is-out': soldOut }">
    <div class="thumb">
      <img v-if="prize.img_url" :src="prize.img_url" :alt="prize.name" />
      <div v-else class="thumb-fallback">
        <AppIcon name="gift" :size="28" />
      </div>
      <span v-if="level" class="level-tag">{{ level }}</span>
      <span v-if="soldOut" class="sold-out">已抽完</span>
    </div>

    <div class="info">
      <h4 class="name truncate" :title="prize.name">{{ prize.name }}</h4>
      <p v-if="prize.description" class="desc clamp-2">{{ prize.description }}</p>
      <div class="tags">
        <StatusBadge :map="PRIZE_TYPE" :value="prize.prize_type" />
      </div>

      <template v-if="variant === 'admin'">
        <div class="progress mt-2">
          <div class="progress-bar" :class="tone" :style="{ width: `${percent}%` }" />
        </div>
        <p class="stock text-xs">
          剩余 <strong>{{ remain }}</strong> / {{ total }}
        </p>
      </template>
      <p v-else class="stock text-xs">
        剩余 <strong>{{ remain }}</strong> 份
      </p>
    </div>
  </article>
</template>

<style scoped>
.prize-card {
  display: flex;
  flex-direction: column;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  overflow: hidden;
  transition: transform var(--dur) var(--ease-out), box-shadow var(--dur) var(--ease),
    border-color var(--dur) var(--ease);
}
.prize-card:hover {
  transform: translateY(-3px);
  box-shadow: var(--shadow-md);
  border-color: var(--brand-200);
}
.prize-card.is-out { opacity: 0.72; }
.prize-card.is-out:hover { transform: none; box-shadow: var(--shadow-xs); }

.thumb {
  position: relative;
  aspect-ratio: 4 / 3;
  background: linear-gradient(160deg, var(--brand-50), var(--surface-3));
  overflow: hidden;
}
.thumb img { width: 100%; height: 100%; object-fit: cover; }
.thumb-fallback {
  width: 100%;
  height: 100%;
  display: grid;
  place-items: center;
  color: var(--brand-300);
}
.level-tag {
  position: absolute;
  top: 8px;
  left: 8px;
  padding: 3px 9px;
  border-radius: var(--radius-pill);
  background: linear-gradient(135deg, var(--gold-400), var(--gold-600));
  color: #4a2c00;
  font-size: 11.5px;
  font-weight: 700;
  box-shadow: var(--shadow-xs);
}
.sold-out {
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
  background: rgba(26, 23, 48, 0.42);
  color: #fff;
  font-size: 14px;
  font-weight: 700;
  letter-spacing: 0.08em;
}

.info {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: var(--sp-3) var(--sp-4) var(--sp-4);
  flex: 1;
}
.name { font-size: 14.5px; font-weight: 650; }
.desc { font-size: 12.5px; color: var(--text-muted); }
.tags { display: flex; gap: 6px; flex-wrap: wrap; }
.stock { color: var(--text-muted); margin-top: auto; }
.stock strong { color: var(--brand-700); font-size: 14px; }
</style>
