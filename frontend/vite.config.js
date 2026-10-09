import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'

// 后端地址：默认与本机 FastAPI 服务一致，可用 VITE_BACKEND 覆盖
const BACKEND = process.env.VITE_BACKEND || 'http://127.0.0.1:8000'

// 开发与预览都通过代理访问后端，避免跨域问题（后端 CORS 默认只放行 5173）
const proxy = {
  '/api': { target: BACKEND, changeOrigin: true },
  '/health': { target: BACKEND, changeOrigin: true },
}

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue(), vueDevTools()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    port: 5173,
    proxy,
  },
  preview: {
    port: 4173,
    proxy,
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
    chunkSizeWarningLimit: 900,
  },
})
