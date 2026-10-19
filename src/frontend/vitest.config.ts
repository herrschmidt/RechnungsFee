import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'

// Reine Unit-Tests (jsdom) – bewusst eigene Config, damit die Vite-Dev-/Build-Config
// (Proxy, Tauri, Tailwind-Plugin) davon unberührt bleibt.
export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    setupFiles: ['./vitest.setup.ts'],
    include: ['src/**/*.test.{ts,tsx}'],
  },
})
