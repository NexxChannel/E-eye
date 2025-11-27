import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    middlewareMode: false,
    proxy: {
      '/users': 'http://127.0.0.1:8000',
      '/auth': 'http://127.0.0.1:8000',
      '/me': 'http://127.0.0.1:8000',
      '/health': 'http://127.0.0.1:8000',
      '/projects': 'http://127.0.0.1:8000',
      '/drawings': 'http://127.0.0.1:8000',
      '/static': 'http://127.0.0.1:8000',
      '/debug': 'http://127.0.0.1:8000',
    }
  }
})
