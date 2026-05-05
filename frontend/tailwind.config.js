/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        'mono': ['"DM Mono"', 'monospace'],
        'sans': ['"DM Sans"', 'system-ui', 'sans-serif'],
      },
      colors: {
        'bg-base': '#04070f',
        'bg-surface': '#0c1221',
        'bg-secondary': '#080d1a',
        'accent': '#7c6fff',
        'accent-light': '#a89fff',
        'positive': '#00e5b0',
        'negative': '#ff5572',
        'neutral': '#7a8fa8',
      },
      animation: {
        'fade-in': 'fadeIn 0.3s ease forwards',
        'pulse-dot': 'pulseDot 1.5s ease-in-out infinite',
      },
      keyframes: {
        fadeIn: {
          'from': { opacity: '0', transform: 'translateY(6px)' },
          'to': { opacity: '1', transform: 'translateY(0)' },
        },
        pulseDot: {
          '0%, 100%': { opacity: '1', transform: 'scale(1)' },
          '50%': { opacity: '0.4', transform: 'scale(0.7)' },
        },
      },
    },
  },
  plugins: [],
}
