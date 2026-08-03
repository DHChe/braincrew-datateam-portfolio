import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "tests/frontend/e2e",
  fullyParallel: false,
  reporter: "list",
  use: {
    baseURL: "http://127.0.0.1:4173",
    browserName: "chromium",
  },
  webServer: {
    command: "npm run serve:static",
    port: 4173,
    reuseExistingServer: false,
  },
});
