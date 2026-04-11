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
        background: {
          DEFAULT: '#F5F3EF',   // warm off-white, not pure white
          dark: '#0D1117'       // deep blue-black, not pure black
        },
        surface: {
          DEFAULT: '#FDFCFA',   // warm paper white
          dark: '#1A233A'       // dark navy
        },
        primary: '#3B82F6',
        accent: '#F59E0B'
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
