/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{astro,html,js,jsx,md,mdx,svelte,ts,tsx,vue}'],
  theme: {
    extend: {
      fontFamily: {
        serif: ['"Newsreader"', 'Georgia', 'serif'],
        sans: ['"Outfit"', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
      colors: {
        paper: {
          950: '#0F0E0D',
          900: '#181614',
          850: '#221F1C',
          800: '#2C2825',
          700: '#443E3A',
          200: '#E7E5E4',
          100: '#F5F5F4',
          50: '#FAFAF9',
        },
        spice: {
          600: '#D97706',
          700: '#C2410C',
          800: '#9A3412',
          900: '#7C2D12',
        }
      }
    },
  },
  plugins: [],
}
