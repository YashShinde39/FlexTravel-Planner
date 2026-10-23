import path from 'node:path'
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: { '@': path.resolve(import.meta.dirname, './src') },
  },
  build: {
    // The largest chunk is the lazily loaded map renderer (maplibre-gl, ~300 KB gzipped).
    chunkSizeWarningLimit: 1200,
  },
  server: {
    // Forward API calls to the FastAPI dev server (`make dev`).
    proxy: { '/api': 'http://127.0.0.1:8000' },
  },
})
