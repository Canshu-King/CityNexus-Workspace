import { expect, test, type Page } from "@playwright/test";

async function updatePolicy(page: Page, selector: string, value: string) {
  const response = page.waitForResponse(
    (item) =>
      item.url().includes("/agent-policy") &&
      item.request().method() === "PUT" &&
      item.status() === 200,
  );
  await page.locator(selector).fill(value);
  await response;
}

test("V6 Predictive Real-City Twin prevents a Journey weakness autonomously", async ({ page }) => {
  const reset = await page.request.post("/api/v1/demo/reset");
  expect(reset.ok()).toBeTruthy();
  let guardianScanRequests = 0;
  page.on("request", (request) => {
    if (request.url().endsWith("/guardian/scan")) guardianScanRequests += 1;
  });

  await page.goto("/");
  await expect(page.getByTestId("journey-status")).toHaveAttribute("data-source", "backend");
  const modeResponse = page.waitForResponse(
    (item) =>
      item.url().includes("/agent-policy") &&
      item.request().method() === "PUT" &&
      item.status() === 200,
  );
  await page.getByTestId("agent-mode").selectOption("AUTONOMOUS");
  await modeResponse;
  await updatePolicy(page, "#agent-cost-limit", "5000");
  await updatePolicy(page, "#agent-drift-limit", "120");
  const autoAccept = page.getByTestId("agent-auto-accept");
  if (!(await autoAccept.isChecked())) {
    const autoAcceptResponse = page.waitForResponse(
      (item) =>
        item.url().includes("/agent-policy") &&
        item.request().method() === "PUT" &&
        item.status() === 200,
    );
    await autoAccept.check();
    await autoAcceptResponse;
  }
  await page.getByTestId("agent-command").fill(
    "Keep the cruise and dinner protected, prefer indoor alternatives, allow autonomous reversible recovery.",
  );

  await page.getByTestId("activate-guardian-mission").click();
  await expect(page.getByTestId("guardian-standing-mission")).toContainText("ACTIVE");

  const riskFixture = page.waitForResponse(
    (response) =>
      response.url().endsWith("/guardian/provider-fixture") &&
      response.request().method() === "POST" &&
      response.status() === 200,
  );
  await page.getByTestId("guardian-provider-risk-forecast").click();
  expect((await (await riskFixture).json()).state).toBe("RISK_FORECAST");

  await expect(page.getByTestId("guardian-decision")).toContainText("PREEMPTIVE_RECOVERY", {
    timeout: 45_000,
  });
  await expect(page.getByTestId("guardian-predictive-resilience")).toContainText(
    "PREDICTIVE_WEAKNESS",
  );
  await expect(page.getByTestId("guardian-predictive-resilience")).toContainText("real-city POIs");
  await expect(page.getByTestId("guardian-provenance")).toContainText("ORTOOLS_CP_SAT_V2");
  await expect(page.getByTestId("guardian-provenance")).toContainText("ALLOW_AUTO");
  await expect(page.getByTestId("guardian-provenance")).toContainText("EXECUTED");
  await expect(page.getByTestId("guardian-predictive-result")).toContainText("EXECUTED");
  await expect(page.getByTestId("guardian-trace")).toContainText("request_replan");
  await expect(page.getByTestId("guardian-trace")).toContainText("accept_replan");
  await expect(page.getByTestId("protected-commitment")).toContainText("River Cruise");
  await expect(page.getByTestId("journey-map")).toHaveAttribute(
    "data-basemap-provider",
    "openfreemap",
  );
  expect(guardianScanRequests).toBe(0);

  await page.reload();
  await expect(page.getByTestId("guardian-decision")).toContainText("PREEMPTIVE_RECOVERY");
  await expect(page.getByTestId("guardian-predictive-resilience")).toContainText("PREDICTIVE_WEAKNESS");
  await expect(page.getByTestId("guardian-predictive-result")).toContainText("EXECUTED");

  const journeyId = await page.evaluate(() => localStorage.getItem("citynexus.demo.journey_id"));
  expect(journeyId).toBeTruthy();
  await page.request.post(`/api/v1/journeys/${journeyId}/guardian/autopilot/stop`);
});
