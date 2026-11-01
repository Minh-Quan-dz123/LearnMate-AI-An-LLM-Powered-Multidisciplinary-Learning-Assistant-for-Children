import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    // Proxy các request /api sang Backend FastAPI chạy cổng 8000
    // Giúp FE và BE liên kết mượt mà không gặp lỗi CORS khi chạy local
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
    },
  },
})
