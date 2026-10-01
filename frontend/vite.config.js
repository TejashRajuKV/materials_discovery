import path from 'node:path';
import { fileURLToPath } from 'node:url';
import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';

const here = path.dirname(fileURLToPath(import.meta.url));

export default defineConfig({
  root: here,
  plugins: [react()],
  server: {
    port: 5173,
    proxy: { '/api': process.env.VITE_API_TARGET || 'http://localhost:3000' },
  },
  build: { outDir: path.resolve(here, '..', 'dist'), emptyOutDir: true },
  test: {
    root: path.resolve(here, '..'),
    environment: 'jsdom',
    include: ['tests/frontend/**/*.test.{js,jsx}'],
    setupFiles: [path.resolve(here, 'src/test-setup.js')],
  },
});
