import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// Boş → "/", dolu → başı ve sonu "/" ile normalize edilir (örn. "patent" → "/patent/").
function normalizeBase(value: string): string {
  const trimmed = value.trim().replace(/^\/+|\/+$/g, '')
  return trimmed ? `/${trimmed}/` : '/'
}

// Kök dizindeki .env okunur (ortam değişkeni .env'e göre önceliklidir).
const envDir = decodeURIComponent(new URL('..', import.meta.url).pathname)

export default defineConfig(({ mode }) => {
  // VITE_BASE_PATH build zamanında gömülür; değişirse yeniden build gerekir.
  const base = normalizeBase(loadEnv(mode, envDir, 'VITE_').VITE_BASE_PATH ?? '')
  const baseWithoutSlash = base.slice(0, -1)

  return {
    base,
    envDir,
    plugins: [react()],
    // Yalnızca geliştirme sunucusu: backend prefix'siz yolları bekler (proxy prefix'i siler varsayımı).
    server: {
      host: '127.0.0.1', // Node 26'da 'localhost' yalnızca IPv6'ya bağlanabiliyor; backend ile aynı loopback
      port: 5173,
      strictPort: true,
      proxy: {
        [`${base}api`]: {
          target: 'http://127.0.0.1:8001',
          rewrite: (path: string) => path.slice(baseWithoutSlash.length),
        },
      },
    },
  }
})
