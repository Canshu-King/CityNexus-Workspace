import { expect, test } from "@playwright/test";
import { testIds } from "../src/contracts/testIds";

test("CityNexus commitment-aware journey recovery", async ({ page }) => {
  // Route names are placeholders until the React router is frozen.
  await page.goto("/");

  await expect(page.getByTestId(testIds.journeyStatus)).toBeVisible();
  await expect(page.getByTestId(testIds.journeyMap)).toBeVisible();
  await expect(page.getByTestId(testIds.journeyTimeline)).toContainText("Tech Art Center");
  await expect(page.getByTestId(testIds.budgetRemaining)).toContainText("¥5,600");
  await expect(page.getByTestId(testIds.nextCommitmentBuffer)).toContainText("55 min");
  await expect(page.getByTestId(testIds.feasibilityEnvelope)).toContainText("hard constraints pass");
  await expect(page.getByTestId(testIds.providerDegradation)).toContainText("ready");
  await expect(page.getByTestId(testIds.upcomingCommitments)).toContainText("River Cruise");
  await expect(page.getByTestId(testIds.mapCurrentMarker)).toBeVisible();
  await expect(page.getByTestId(testIds.mapProtectedMarker)).toBeVisible();

  await page.getByTestId(testIds.eventSimulator).click();
  await page.getByTestId(testIds.eventClosureButton).click();

  await expect(page.getByTestId(testIds.replanPanel)).toBeVisible();
  await expect(page.getByTestId(testIds.mapEventMarker)).toBeVisible();
  await expect(page.getByTestId(testIds.mapNewRoute)).toBeVisible();
  await expect(page.getByTestId(testIds.replanDiff)).toContainText("Tech Art");
  await expect(page.getByTestId(testIds.protectedCommitment)).toContainText("River Cruise");
  await expect(page.getByTestId(testIds.replanCandidateFamilies)).toContainText("F3_OPPORTUNITY_WINDOW");
  await expect(page.getByTestId(testIds.replanScore)).toContainText("0.84");
  await expect(page.getByTestId(testIds.replanEvidence)).toContainText("C4 preserved");
  await expect(page.getByTestId(testIds.replanDeltas)).toContainText("travel");

  await page.getByTestId(testIds.acceptReplan).click();
  await expect(page.getByTestId(testIds.journeyStatus)).toContainText("ACTIVE");

  await page.reload();
  await expect(page.getByTestId(testIds.protectedCommitment)).toContainText("River Cruise");
});
