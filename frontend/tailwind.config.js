/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        dark: {
          950: '#030712',
          900: '#0b0f19',
          800: '#151c2c',
          700: '#1e293b',
          600: '#334155',
          500: '#64748b',
        },
        accent: {
          emerald: '#10b981',
          teal: '#14b8a6',
          blue: '#3b82f6',
          indigo: '#6366f1',
          purple: '#8b5cf6',
        }
      },
      fontFamily: {
        sans: ['Inter', 'Outfit', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
