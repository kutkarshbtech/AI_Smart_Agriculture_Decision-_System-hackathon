import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://swadesh-ai-alb-dev-426896629.ap-south-1.elb.amazonaws.com',
        changeOrigin: true,
      }
    }
  }
})
