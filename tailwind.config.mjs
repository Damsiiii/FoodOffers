/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{astro,html,js,jsx,md,mdx,svelte,ts,tsx,vue}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['"Space Grotesk"', '"Inter"', 'system-ui', 'sans-serif'],
        display: ['"Space Grotesk"', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
      colors: {
        background: '#FDFAD8', // Butter Bean
        foreground: '#47510B', // Grassy Green
        muted: {
          DEFAULT: '#CAD23C', // Seed Green
          foreground: '#47510B', // Grassy Green
        },
        accent: {
          DEFAULT: '#FF5B03', // Sungold Orange
          foreground: '#FFFFFF',
        },
        border: '#47510B', // Grassy Green
        brand: {
          orange: '#FF5B03', // Sungold Orange
          yellow: '#FFF24D', // Lemon Yellow
          cream: '#FDFAD8',  // Butter Bean
          beet: '#AB1717',    // Beet Red
          green: '#47510B',   // Grassy Green
          pink: '#FFB6A9',    // Petal Pink
          seed: '#CAD23C',    // Seed Green
          blue: '#A1AED1',    // Blue Linen
        },
      },
      borderRadius: {
        DEFAULT: '0px',
        none: '0px',
        sm: '2px',
      },
      borderWidth: {
        DEFAULT: '1px',
        '2': '2px',
        '4': '4px',
      },
      keyframes: {
        marquee: {
          '0%': { transform: 'translateX(0%)' },
          '100%': { transform: 'translateX(-50%)' },
        },
      },
      animation: {
        marquee: 'marquee 25s linear infinite',
        'marquee-fast': 'marquee 15s linear infinite',
      },
    },
  },
  plugins: [],
}
