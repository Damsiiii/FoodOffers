import { defineConfig } from 'astro/config';
import tailwind from '@astrojs/tailwind';
import react from '@astrojs/react';

export default defineConfig({
  site: 'https://damsiiii.github.io',
  base: '/FoodOffers',
  integrations: [tailwind(), react()],
});
