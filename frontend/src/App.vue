<script setup>
import { computed, onMounted } from 'vue'
import AppHeader from '@/components/AppHeader.vue'
import AppFooter from '@/components/AppFooter.vue'
import ToastHost from '@/components/ToastHost.vue'
import ConfirmDialog from '@/components/ConfirmDialog.vue'
import AdminLayout from '@/views/admin/AdminLayout.vue'
import RouteLoading from '@/components/RouteLoading.vue'
import { useRoute } from '@/router'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const auth = useAuthStore()

const view = computed(() => route.matched?.component)
const bare = computed(() => Boolean(route.meta?.bare))
const isAdminArea = computed(() => route.meta?.layout === 'admin')

onMounted(() => {
  auth.ensureLoaded()
})
</script>

<template>
  <div class="app-shell">
    <AppHeader v-if="!bare" />

    <main class="app-main">
      <!-- 首次进入时守卫可能还在等待 /users/me，此时先显示占位 -->
      <RouteLoading v-if="!view" />
      <Transition v-else name="view" mode="out-in">
        <AdminLayout v-if="isAdminArea" :key="`admin-${route.name}`">
          <component :is="view" :key="route.fullPath" />
        </AdminLayout>
        <component :is="view" v-else :key="route.fullPath" />
      </Transition>
    </main>

    <AppFooter v-if="!bare" />
    <ToastHost />
    <ConfirmDialog />
  </div>
</template>

<style scoped>
.app-shell {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}
.app-main {
  flex: 1;
  min-width: 0;
}
</style>
