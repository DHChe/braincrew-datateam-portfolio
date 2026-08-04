import { defineConfig } from "@playwright/test";

import { pagesBasePath } from "./dashboard/site-config.cjs";

export default defineConfig({
  testDir: "tests/frontend/e2e",
  fullyParallel: false,
  reporter: "list",
  use: {
    baseURL: `http://127.0.0.1:4173${pagesBasePath}/`,
    browserName: "chromium",
  },
  webServer: {
    command: "npm run serve:static",
    port: 4173,
    reuseExistingServer: false,
  },
});
