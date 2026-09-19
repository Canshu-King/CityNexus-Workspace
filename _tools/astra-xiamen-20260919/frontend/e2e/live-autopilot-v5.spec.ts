import { expect, test, type Page } from "@playwright/test";
import { testIds } from "../src/contracts/testIds";

async function openJourney(page: Page) {
  await page.goto("/");
  await expect(page.getByTestId(testIds.journeyStatus)).toHaveAttribute("data-source", "backend");
  await expect(page.getByTestId(testIds.currentActivity)).toContainText("Tech Art Center");
}

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

test("V5 zero-touch Autopilot recovers through provider pulse, CP-SAT V2, and reload", async ({
  page,
}) => {
  const reset = await page.request.post("/api/v1/demo/reset");
  expect(reset.ok()).toBeTruthy();
  let guardianScanRequests = 0;
  page.on("request", (request) => {
    if (request.url().endsWith("/guardian/scan")) guardianScanRequests += 1;
  });

  await openJourney(page);
  await page.getByTestId("agent-mode").selectOption("AUTONOMOUS");
  await updatePolicy(page, "#agent-cost-limit", "5000");
  await updatePolicy(page, "#agent-drift-limit", "120");
  const autoAcceptResponse = page.waitForResponse(
    (item) =>
      item.url().includes("/agent-policy") &&
      item.request().method() === "PUT" &&
      item.status() === 200,
  );
  await page.getByTestId("agent-auto-accept").check();
  await autoAcceptResponse;

  await page.getByTestId("agent-command").fill(
    "游船和晚餐别动，优先室内、少走路，最多多花五十元，允许自动调整。",
  );
  const missionResponse = page.waitForResponse(
    (item) =>
      item.url().endsWith("/guardian/mission") &&
      item.request().method() === "PUT" &&
      item.status() === 200,
  );
  await page.getByTestId("activate-guardian-mission").click();
  const mission = await (await missionResponse).json();
  expect(mission.status).toBe("ACTIVE");
  expect(mission.protected_activity_ids.length).toBeGreaterThanOrEqual(2);

  const startResponse = page.waitForResponse(
    (item) =>
      item.url().endsWith("/guardian/autopilot/start") &&
      item.request().method() === "POST" &&
      item.status() === 200,
  );
  await page.getByTestId("guardian-autopilot-start").click();
  await startResponse;
  await expect(page.getByTestId("guardian-autopilot-status")).toContainText("RUNNING");
  await expect(page.getByTestId("guardian-provider-disrupted")).toBeEnabled();

  const fixtureResponse = page.waitForResponse(
    (item) =>
      item.url().endsWith("/guardian/provider-fixture") &&
      item.request().method() === "POST" &&
      item.status() === 200,
  );
  await page.getByTestId("guardian-provider-disrupted").click();
  const fixture = await (await fixtureResponse).json();
  expect(fixture.state).toBe("DISRUPTED");

  await expect(page.getByTestId("guardian-decision")).toContainText("RECOVERY_REQUIRED", {
    timeout: 45_000,
  });
  await expect(page.getByTestId("guardian-provenance")).toContainText("ORTOOLS_CP_SAT_V2", {
    timeout: 45_000,
  });
  await expect(page.getByTestId("guardian-provenance")).toContainText("ALLOW_AUTO");
  await expect(page.getByTestId("guardian-provenance")).toContainText("EXECUTED");
  await expect(page.getByTestId("guardian-trace")).toContainText("request_replan");
  await expect(page.getByTestId("guardian-trace")).toContainText("accept_replan");
  await expect(page.getByTestId("guardian-live-operations")).toContainText(
    /guardian_wake|city_signal_received|solver_candidates_generated/i,
  );
  await expect(page.getByTestId(testIds.protectedCommitment)).toContainText("River Cruise");
  await expect(page.getByTestId(testIds.journeyTimeline)).toContainText("Dinner");
  await expect(page.getByTestId(testIds.mapOldRoute)).toBeVisible();
  await expect(page.getByTestId(testIds.mapNewRoute)).toBeVisible();
  expect(guardianScanRequests).toBe(0);

  const journeyId = await page.evaluate(() => localStorage.getItem("citynexus.demo.journey_id"));
  expect(journeyId).toBeTruthy();
  const beforeRepeat = await page.request
    .get(`/api/v1/journeys/${journeyId}/guardian/status`)
    .then((response) => response.json());
  const runCount = beforeRepeat.runs.length;

  await page.reload();
  await expect(page.getByTestId("guardian-decision")).toContainText("RECOVERY_REQUIRED");
  await expect(page.getByTestId("guardian-provenance")).toContainText("ORTOOLS_CP_SAT_V2");
  await expect(page.getByTestId("guardian-trace")).toContainText("accept_replan");
  await expect(page.getByTestId(testIds.protectedCommitment)).toContainText("River Cruise");
  await expect(page.getByTestId(testIds.journeyTimeline)).toContainText("Dinner");
  await expect(page.getByTestId(testIds.mapOldRoute)).toBeVisible();
  await expect(page.getByTestId(testIds.mapNewRoute)).toBeVisible();

  const repeatFixtureResponse = page.waitForResponse(
    (item) =>
      item.url().endsWith("/guardian/provider-fixture") &&
      item.request().method() === "POST" &&
      item.status() === 200,
  );
  await page.getByTestId("guardian-provider-disrupted").click();
  await repeatFixtureResponse;
  await page.waitForTimeout(1_000);
  const afterRepeat = await page.request
    .get(`/api/v1/journeys/${journeyId}/guardian/status`)
    .then((response) => response.json());
  expect(afterRepeat.runs).toHaveLength(runCount);
  expect(afterRepeat.current_active_plan_version_id).toBe(
    beforeRepeat.current_active_plan_version_id,
  );
  expect(guardianScanRequests).toBe(0);

  await page.request.post(`/api/v1/journeys/${journeyId}/guardian/autopilot/stop`);
});
