import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  // `vite preview` (used for the Railway production serve) rejects requests
  // from hosts it doesn't recognise. Railway serves the app from a generated
  // *.up.railway.app domain, so allow all hosts for the preview server.
  preview: {
    allowedHosts: true,
  },
})
