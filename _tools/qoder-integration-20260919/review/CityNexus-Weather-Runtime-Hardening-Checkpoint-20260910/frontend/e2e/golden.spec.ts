import { expect, test } from "@playwright/test";
import { testIds } from "../src/contracts/testIds";

test("Journey Mode uses backend truth for closure recovery", async ({ page }) => {
  await page.goto("/");

  const status = page.getByTestId(testIds.journeyStatus);
  await expect(status).toHaveAttribute("data-source", "backend");
  await expect(status).toContainText("ACTIVE");
  await expect(page.getByTestId(testIds.journeyMap)).toBeVisible();
  await expect(page.getByTestId(testIds.journeyTimeline)).toContainText("Tech Art Center");
  await expect(page.getByTestId(testIds.journeyTimeline)).toContainText("River Cruise");
  await expect(page.getByTestId(testIds.currentActivity)).toContainText("Tech Art Center");
  await expect(page.getByTestId(testIds.budgetRemaining)).toContainText("130");
  await expect(page.getByTestId(testIds.feasibilityEnvelope)).toContainText("persisted backend");
  await expect(page.getByTestId(testIds.providerDegradation)).toContainText("ready");
  await expect(page.getByTestId(testIds.upcomingCommitments)).toContainText("River Cruise");
  await expect(page.getByTestId(testIds.mapCurrentMarker)).toBeVisible();
  await expect(page.getByTestId(testIds.mapProtectedMarker)).toBeVisible();

  const initialStorageKeys = await page.evaluate(() => Object.keys(localStorage));
  expect(initialStorageKeys).toEqual(["citynexus.demo.journey_id"]);

  await page.getByTestId(testIds.eventSimulator).click();
  const eventResponse = page.waitForResponse(
    (response) =>
      response.url().includes("/api/v1/journeys/") &&
      response.url().endsWith("/events") &&
      response.request().method() === "POST" &&
      response.status() === 201,
  );
  const proposalsResponse = page.waitForResponse(
    (response) =>
      response.url().includes("/api/v1/journeys/") &&
      response.url().endsWith("/replans") &&
      response.request().method() === "GET" &&
      response.status() === 200,
  );
  await page.getByTestId(testIds.eventClosureButton).click();
  const event = await (await eventResponse).json();
  const proposals = await (await proposalsResponse).json();
  expect(event.event_type).toBe("CLOSURE");
  expect(proposals.filter((item: { status: string }) => item.status === "PRESENTED").length).toBeGreaterThanOrEqual(2);
  const f3 = proposals.find(
    (item: {
      diff?: {
        candidate_family?: string;
        opportunity_window_evidence?: {
          origin_key?: string;
          window_opens_at?: string;
        };
      };
    }) => item.diff?.candidate_family === "F3_OPPORTUNITY_WINDOW",
  );
  expect(f3).toBeTruthy();
  if (!f3) throw new Error("F3 proposal was not returned by backend");
  expect(f3.diff?.opportunity_window_evidence?.origin_key).toBe("place-tech-art");
  expect(f3.diff?.opportunity_window_evidence?.window_opens_at).toBe(
    "2026-10-10T13:25:00+08:00",
  );

  await expect(page.getByTestId(testIds.replanPanel)).toBeVisible();
  await expect(page.getByTestId(testIds.mapEventMarker)).toBeVisible();
  await expect(page.getByTestId(testIds.mapNewRoute)).toBeVisible();
  await expect(page.getByTestId(testIds.replanCandidateFamilies)).toContainText(
    "F3_OPPORTUNITY_WINDOW",
  );
  await expect(page.getByTestId(testIds.replanEvidence)).toContainText("C4 preserved");
  await expect(page.getByTestId(testIds.replanScore)).toContainText(/\d+\.\d+/);
  await expect(page.getByTestId(testIds.replanDiff)).toContainText("Tech Art");
  await expect(page.getByTestId(testIds.replanDeltas)).toContainText("travel");

  const acceptResponse = page.waitForResponse(
    (response) =>
      response.url().includes("/api/v1/replans/") &&
      response.url().endsWith("/accept") &&
      response.request().method() === "POST" &&
      response.status() === 200,
  );
  await page.getByTestId(testIds.acceptReplan).click();
  const accepted = await (await acceptResponse).json();
  expect(accepted.journey.active_plan_version_id).toBeTruthy();
  expect(accepted.twin.active_plan_version_id).toBe(accepted.journey.active_plan_version_id);
  await expect(status).toContainText("ACTIVE");
  await expect(page.getByTestId(testIds.protectedCommitment)).toContainText("River Cruise");

  const acceptedStorageKeys = await page.evaluate(() => Object.keys(localStorage));
  expect(acceptedStorageKeys).toEqual(["citynexus.demo.journey_id"]);

  const reloadTwinResponse = page.waitForResponse(
    (response) =>
      response.url().includes("/api/v1/journeys/") &&
      response.url().includes("/twin") &&
      response.request().method() === "GET" &&
      response.status() === 200,
  );
  await page.reload();
  const reloadedTwin = await (await reloadTwinResponse).json();
  expect(reloadedTwin.active_plan_version_id).toBe(accepted.twin.active_plan_version_id);
  await expect(page.getByTestId(testIds.journeyStatus)).toHaveAttribute("data-source", "backend");
  await expect(page.getByTestId(testIds.protectedCommitment)).toContainText("River Cruise");
  await expect(page.getByTestId(testIds.upcomingCommitments)).toContainText("C4_Anchored");
});
