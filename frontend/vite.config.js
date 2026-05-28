import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: '0.0.0.0',       // Listen on all network interfaces
    cors: true,
    allowedHosts: true,    // Prevent Host Header blocks inside IDE proxies
    hmr: {
      host: '127.0.0.1',   // Secure WebSocket HMR connection binding
      port: 5173
    },
    headers: {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, PATCH, OPTIONS",
      "Access-Control-Allow-Headers": "X-Requested-With, content-type, Authorization"
    }
  }
})

