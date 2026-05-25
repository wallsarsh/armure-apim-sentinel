/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        zinc: {
          150: '#e4e4e7',
          350: '#a1a1aa',
          450: '#71717a',
          550: '#52525b',
          650: '#3f3f46',
          750: '#2d2d32',
          850: '#1f1f23',
          950: '#0a0a0b',
        },
        emerald: {
          450: '#34d399',
          550: '#059669',
        },
        rose: {
          450: '#fb7185',
        },
      },
    },
  },
  plugins: [],
}
