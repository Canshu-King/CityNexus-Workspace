import { defineConfig } from "@playwright/test";
import { existsSync } from "node:fs";

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
  use: { baseURL: "http://127.0.0.1:4173" },
  webServer: [
    {
      command: `${backendPython} -m uvicorn app.main:app --host 127.0.0.1 --port 8000`,
      cwd: "../backend",
      url: "http://127.0.0.1:8000/api/v1/health",
      reuseExistingServer: true,
      timeout: 120000,
    },
    {
      command: "npm run dev -- --host 127.0.0.1 --port 4173",
      cwd: ".",
      url: "http://127.0.0.1:4173",
      reuseExistingServer: true,
      timeout: 120000,
    },
  ],
});
