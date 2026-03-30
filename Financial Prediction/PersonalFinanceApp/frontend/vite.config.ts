import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// In Docker, backend is at host "backend"; locally it's localhost
const apiTarget = process.env.VITE_API_PROXY_TARGET || 'http://localhost:8000'

/** Dev-only: serve static admin SPA the same way nginx does in Docker. */
function adminSpaPlugin() {
  return {
    name: 'finance-admin-spa',
    configureServer(server) {
      server.middlewares.use((req: any, _res: unknown, next: () => void) => {
        const url = req.url?.split('?')[0] ?? ''
        if (url === '/admin' || url === '/admin/') {
          req.url = '/admin/index.html' + (req.url?.includes('?') ? '?' + (req.url.split('?')[1] ?? '') : '')
        }
        next()
      })
    },
  }
}

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react(), adminSpaPlugin()],
  server: {
    host: '0.0.0.0', // needed for Docker: accept connections from outside the container
    port: 3000,
    proxy: {
      '/api': {
        target: apiTarget,
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
  },
}) 