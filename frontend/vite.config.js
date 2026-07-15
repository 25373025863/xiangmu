import { defineConfig } from 'vite'

export default defineConfig({
  server: {
    port: 5173,
    strictPort: false,
    proxy: {
      '/api': 'http://127.0.0.1:8000'
    }
  }
})
