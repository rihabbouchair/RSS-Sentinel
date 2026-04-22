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
        'bg-base': '#0d0f14',
        'bg-surface': '#111318',
        'accent': '#7c3aed',
        'accent-light': '#a78bfa',
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
