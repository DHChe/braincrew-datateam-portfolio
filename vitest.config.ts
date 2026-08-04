import { configDefaults, defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    include: ["tests/frontend/**/*.test.ts"],
    exclude: [
      ...configDefaults.exclude,
      "tests/frontend/build-output/**/*.test.ts",
    ],
  },
});
