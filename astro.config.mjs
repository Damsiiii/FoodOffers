import { defineConfig } from 'astro/config';
import tailwind from '@astrojs/tailwind';

export default defineConfig({
  site: 'https://damsiiii.github.io',
  base: '/FoodOffers',
  integrations: [tailwind()],
});
