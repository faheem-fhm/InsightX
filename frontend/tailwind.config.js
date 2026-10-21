/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // The Modern Enterprise Tech Look (Dark Theme)
        navy: {
          deep: '#070B19',
          cadet: '#121829',
        },
        cyan: {
          electric: '#00F2FE',
        },
        purple: {
          neon: '#9B51E0',
        },
        ice: {
          blue: '#A5B4FC',
        },
        brand: {
          bg: '#070B19',
          card: '#121829',
          cyan: '#00F2FE',
          purple: '#9B51E0',
          ice: '#A5B4FC',
        }
      }
    },
  },
  plugins: [],
}
