import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    include: ["tests/frontend/build-output/**/*.test.ts"],
  },
});
