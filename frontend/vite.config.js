import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      // 백엔드 FastAPI(8000)로 프록시,
      '/auth': 'http://localhost:8000',
      '/me': 'http://localhost:8000',
    }
  }
})
