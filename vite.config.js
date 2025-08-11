import { defineConfig } from 'vite';

export default defineConfig({
  build: {
    minify: 'esbuild',
    cssCodeSplit: true,
    lib: {
      entry: 'sandbox-js/test_main.js',
      name: 'Sandbox',
      fileName: 'bundle'
    }
  }
});
