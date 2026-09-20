import { defineConfig } from "@playwright/test";
import {
  announce,
  backendCommand,
  backendEnv,
  resolveE2eEnvironment,
} from "./playwrightEnv";

const env = resolveE2eEnvironment("sw-lifecycle");
announce(env, "sw-lifecycle");

export default defineConfig({
  testDir: "./e2e",
  testMatch: /qoder-sw-lifecycle\.spec\.ts/,
  timeout: 90_000,
  expect: { timeout: 15_000 },
  workers: 1,
  use: {
    baseURL: `http://127.0.0.1:${env.frontendPort}`,
    serviceWorkers: "allow",
  },
  webServer: [
    {
      command: backendCommand(env),
      cwd: "../backend",
      env: backendEnv(env),
      url: `http://127.0.0.1:${env.backendPort}/api/v1/health`,
      reuseExistingServer: false,
      timeout: 120_000,
      stdout: "pipe",
      stderr: "pipe",
    },
    {
      // This gate is intentionally production-only. Running against Vite dev
      // would prove exactly the wrong lifecycle because dev must not register a
      // production service worker.
      command: `npm run build && npm exec -- vite preview --host 127.0.0.1 --port ${env.frontendPort}`,
      cwd: ".",
      url: `http://127.0.0.1:${env.frontendPort}/v8/live`,
      reuseExistingServer: false,
      timeout: 180_000,
      stdout: "pipe",
      stderr: "pipe",
    },
  ],
});
