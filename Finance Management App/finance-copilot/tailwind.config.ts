import type { Config } from 'tailwindcss'

const config: Config = {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        navy: {
          950: '#080d1a',
          900: '#0d1526',
          850: '#111d33',
          800: '#162140',
          750: '#1a2850',
          700: '#1f3060',
          600: '#263a73',
          500: '#2d4487',
          400: '#4d6aa8',
          300: '#7a97c8',
          200: '#a8bcd8',
          100: '#d4e0ee',
          50:  '#eef3f9',
        },
        emerald: {
          950: '#022c1e',
          900: '#064e34',
          800: '#0a7a52',
          700: '#0fa86f',
          600: '#12c97d',
          500: '#10b981',
          400: '#34d399',
          300: '#6ee7b7',
          200: '#a7f3d0',
          100: '#d1fae5',
          50:  '#ecfdf5',
        },
        rose: {
          950: '#2a0612',
          900: '#500d22',
          800: '#881337',
          700: '#be1b4a',
          600: '#e11d48',
          500: '#f43f5e',
          400: '#fb7185',
          300: '#fda4af',
          200: '#fecdd3',
          100: '#ffe4e6',
          50:  '#fff1f2',
        },
        amber: {
          950: '#241202',
          900: '#451a03',
          800: '#78350f',
          700: '#b45309',
          600: '#d97706',
          500: '#f59e0b',
          400: '#fbbf24',
          300: '#fcd34d',
          200: '#fde68a',
          100: '#fef3c7',
          50:  '#fffbeb',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'Cascadia Code', 'monospace'],
      },
      fontSize: {
        '2xs': ['0.625rem', { lineHeight: '0.875rem' }],
      },
      boxShadow: {
        'card-inner': 'inset 0 1px 0 0 rgba(255,255,255,0.06)',
        'emerald-glow': '0 0 20px -4px rgba(18,201,125,0.35)',
        'rose-glow':    '0 0 20px -4px rgba(225,29,72,0.35)',
      },
      keyframes: {
        'fade-in': {
          '0%':   { opacity: '0', transform: 'translateY(4px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        'skeleton-pulse': {
          '0%, 100%': { opacity: '1' },
          '50%':       { opacity: '0.4' },
        },
        shimmer: {
          '0%':   { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
        'slide-up': {
          '0%':   { opacity: '0', transform: 'translateY(8px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
      animation: {
        'fade-in':        'fade-in 200ms ease-out',
        'skeleton-pulse': 'skeleton-pulse 1.8s ease-in-out infinite',
        'shimmer':        'shimmer 2s linear infinite',
        'slide-up':       'slide-up 250ms ease-out',
      },
      gridTemplateColumns: {
        'app':           '288px 1fr',
        'app-collapsed': '64px 1fr',
        'dashboard':     'repeat(12, 1fr)',
      },
    },
  },
  plugins: [],
}

export default config
