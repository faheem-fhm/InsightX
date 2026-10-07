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
        primary: {
          50: '#f0f9ff',
          100: '#e0f2fe',
          500: '#0ea5e9',
          600: '#0284c7',
          700: '#0369a1',
          900: '#0c4a6e',
        },
        brand: {
          dark: '#0b0f19',
          card: '#111827',
          cardBorder: '#1f2937',
          accent: '#6366f1',
          hover: '#4f46e5'
        }
      }
    },
  },
  plugins: [],
}
