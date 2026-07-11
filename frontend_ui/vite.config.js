import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// Gọn nhẹ, sạch sẽ, tự động nhận diện React và Tailwind v4
export default defineConfig({
  plugins: [react(), tailwindcss()],
})