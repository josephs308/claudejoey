import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    env: { LOG_LEVEL: 'error', NODE_ENV: 'test' },
    include: ['test/**/*.test.ts'],
  },
});
