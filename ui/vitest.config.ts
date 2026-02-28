import { defineConfig } from 'vitest/config';

export default defineConfig({
    test: {
        // Use jsdom to simulate a browser DOM for Web Component unit tests.
        environment: 'jsdom',
        include: ['tests/unit/**/*.test.ts'],
        coverage: {
            provider: 'v8',
            reporter: ['text', 'html'],
            include: ['src/**/*.ts'],
            exclude: ['src/main.ts'],
        },
    },
});
