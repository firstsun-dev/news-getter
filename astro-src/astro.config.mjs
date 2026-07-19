import { defineConfig } from 'astro/config';

export default defineConfig({
  site: 'https://firstsun-dev.github.io',
  base: '/news-getter',
  outDir: '../dist',
  publicDir: 'public',
  trailingSlash: 'ignore',
  build: {
    format: 'directory',
  },
});