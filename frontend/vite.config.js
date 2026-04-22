import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: 'dist',
    emptyOutDir: true,
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/perguntar': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/resumir_pdf': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/resumir_video': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/health': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/consulta': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
})
