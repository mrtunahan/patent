/** @type {import('tailwindcss').Config} */
// Tema (font, renk, köşe yuvarlaklığı) yalnızca burada tanımlanır; ana sisteme uyarlamak için tek nokta.
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        // Sistem yığını: dış CDN/font indirme yok, uygulama internetsiz çalışır.
        sans: [
          'system-ui',
          '-apple-system',
          '"Segoe UI"',
          'Roboto',
          '"Helvetica Neue"',
          'Arial',
          'sans-serif',
        ],
      },
      colors: {
        brand: {
          50: '#eff6ff',
          100: '#dbeafe',
          600: '#2563eb',
          700: '#1d4ed8',
          900: '#1e3a8a',
        },
        surface: '#f8fafc',
        ink: '#0f172a',
        muted: '#64748b',
        line: '#e2e8f0',
      },
      borderRadius: {
        ui: '0.5rem',
      },
    },
  },
  plugins: [],
}
