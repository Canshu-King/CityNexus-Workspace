import { defineConfig } from "@playwright/test";
import { existsSync } from "node:fs";

const E2E_PORT = Number(process.env.CITYNEXUS_E2E_PORT ?? 4173);
const BACKEND_PORT = Number(process.env.CITYNEXUS_BACKEND_PORT ?? 8000);
const backendPython =
  process.env.CITYNEXUS_PYTHON ??
  (process.platform === "win32" && existsSync("../.venv/Scripts/python.exe")
    ? "..\\.venv\\Scripts\\python.exe"
    : "python");

export default defineConfig({
  testDir: "./e2e",
  // Guardian recovery is an asynchronous provider -> solver -> policy ->
  // mutation path.  Windows CI occasionally needs longer than Playwright's
  // 30s default while the browser reloads and the shared local SQLite worker
  // drains; the product assertions retain their own targeted time budgets.
  timeout: 60_000,
  expect: { timeout: 10_000 },
  // The local demo intentionally uses one shared SQLite process/database;
  // serial workers keep reset-and-replay scenarios isolated.
  workers: 1,
  /* globalSetup would run before this config's webServer entries have a live
     port, so the seed is a Playwright setup *project*: it runs against the very
     servers Playwright starts, then every test replays its storageState. */
  projects: [
    { name: "real-seed", testMatch: /_qoderRealSeed\.setup\.ts/ },
    {
      name: "chromium",
      dependencies: ["real-seed"],
      use: { storageState: "./e2e/.qoder-seed-state.json" },
    },
  ],
  use: { baseURL: `http://127.0.0.1:${E2E_PORT}` },
  webServer: [
    {
      command: `${backendPython} -m uvicorn app.main:app --host 127.0.0.1 --port ${BACKEND_PORT}`,
      cwd: "../backend",
      url: `http://127.0.0.1:${BACKEND_PORT}/api/v1/health`,
      reuseExistingServer: true,
      timeout: 120000,
    },
    {
      command: `npm run dev -- --host 127.0.0.1 --port ${E2E_PORT}`,
      cwd: ".",
      url: `http://127.0.0.1:${E2E_PORT}`,
      reuseExistingServer: true,
      timeout: 120000,
    },
  ],
});
