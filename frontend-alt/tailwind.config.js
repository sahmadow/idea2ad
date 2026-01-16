/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          lime: '#D4FF31',
          dark: '#141414',
          gray: '#202020',
          light: '#F5F5F5',
        }
      },
      fontFamily: {
        display: ['"Space Grotesk"', 'sans-serif'],
        body: ['Inter', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
      backgroundImage: {
        'grid-pattern': 'radial-gradient(circle, #333 1px, transparent 1px)',
      },
      backgroundSize: {
        'grid-pattern': '20px 20px',
      }
    },
  },
  plugins: [],
}
