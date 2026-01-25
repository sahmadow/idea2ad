import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import fs from 'fs'
import path from 'path'

const keyPath = path.resolve(__dirname, '../certs/key.pem')
const certPath = path.resolve(__dirname, '../certs/cert.pem')
const certsExist = fs.existsSync(keyPath) && fs.existsSync(certPath)

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: certsExist ? {
    https: {
      key: fs.readFileSync(keyPath),
      cert: fs.readFileSync(certPath),
    },
  } : {},
})
