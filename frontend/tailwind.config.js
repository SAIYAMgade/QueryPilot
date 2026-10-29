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
        slate: {
          850: '#151e2e',
          900: '#0f172a',
          950: '#090d16',
        },
        oracle: {
          red: '#c74634',
          darkRed: '#a83222',
          blue: '#0284c7',
        }
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'Fira Code', 'ui-monospace', 'Menlo', 'monospace'],
      }
    },
  },
  plugins: [],
}
