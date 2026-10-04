import { defineConfig } from 'astro/config';
import tailwindcss from '@tailwindcss/vite';

// https://astro.build/config
export default defineConfig({
  site: 'https://x3m-industries.github.io',
  base: '/antigravity-packages',
  build: {
    format: 'file',
  },
  vite: {
    plugins: [tailwindcss()],
  },
});
