import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'https://marketing-ttok-tti-functionappv2-bxayc6f7b4f5fhg0.swedencentral-01.azurewebsites.net',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '/api'),
        headers: {
          'x-functions-key': 'YOUR_AZURE_FUNCTION_KEY'
        }
      }
    }
  }
})
