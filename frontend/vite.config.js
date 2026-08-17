import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  // 注：未用 manualChunks 手动分包——路由懒加载已让 echarts 等重依赖自动按页拆分，
  // 手动 vendor 分包会导致 element-plus 内的 dayjs 实例分裂（日期面板报 hour is not a function）
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      }
    }
  }
})
