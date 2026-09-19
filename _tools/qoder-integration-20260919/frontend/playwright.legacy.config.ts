import { defineConfig } from "@playwright/test";
import { announce, backendCommand, backendEnv, resolveE2eEnvironment } from "./playwrightEnv";

/* ------------------------------------------------------------------ *
 * Archived legacy-surface tests.  Explicitly invoked, never gating.
 *
 *   npx playwright test --config playwright.legacy.config.ts
 *
 * These guard Journey Mode screens that the product moved behind /legacy on
 * purpose (src/main.tsx renders V8Experience everywhere else), so they are kept
 * runnable for historical regression while being absent from the acceptance
 * suite.  This config cannot be made authoritative: passing
 * CITYNEXUS_E2E_AUTHORITATIVE=1 here is reported and ignored, because a green
 * archived run must never be mistaken for merge evidence.
 * ------------------------------------------------------------------ */

const env = resolveE2eEnvironment("legacy", { allowAuthoritative: false });
announce(env, "legacy");
console.error(
  "[citynexus e2e] suite=legacy NON-GATING: results here cannot sign integration, merge or release.",
);

export default defineConfig({
  testDir: "./e2e/legacy",
  timeout: 60_000,
  expect: { timeout: 10_000 },
  workers: 1,
  use: { baseURL: `http://127.0.0.1:${env.frontendPort}` },
  webServer: [
    {
      command: backendCommand(env),
      cwd: "../backend",
      env: backendEnv(env),
      url: `http://127.0.0.1:${env.backendPort}/api/v1/health`,
      reuseExistingServer: env.reuseExistingServer,
      timeout: 120000,
      stdout: "pipe",
      stderr: "pipe",
    },
    {
      command: `npm run dev -- --host 127.0.0.1 --port ${env.frontendPort}`,
      cwd: ".",
      url: `http://127.0.0.1:${env.frontendPort}`,
      reuseExistingServer: env.reuseExistingServer,
      timeout: 120000,
    },
  ],
});
