import { defineConfig } from 'vite';

export default defineConfig({
    // Route all /api requests to the backend during development.
    // This avoids CORS issues in the browser during local dev.
    server: {
        port: 3000,
        proxy: {
            '/api': {
                target: 'http://localhost:8000',
                changeOrigin: true,
            },
        },
    },
    build: {
        outDir: 'dist',
        sourcemap: true,
    },
});
