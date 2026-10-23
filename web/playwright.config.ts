import { defineConfig } from "@playwright/test";

const port = Number(process.env.E2E_PORT ?? 3123);

export default defineConfig({
  testDir: "e2e",
  use: { baseURL: process.env.E2E_BASE_URL ?? `http://localhost:${port}` },
  webServer: process.env.E2E_BASE_URL
    ? undefined
    : { command: `npx next start -p ${port}`, port, reuseExistingServer: true },
});
