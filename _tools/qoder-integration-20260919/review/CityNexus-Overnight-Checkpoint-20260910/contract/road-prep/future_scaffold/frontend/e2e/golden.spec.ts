import { expect, test } from "@playwright/test";
import { testIds } from "../src/contracts/testIds";

test("CityNexus commitment-aware journey recovery", async ({ page }) => {
  // Route names are placeholders until the React router is frozen.
  await page.goto("/");

  await expect(page.getByTestId(testIds.journeyStatus)).toBeVisible();
  await expect(page.getByTestId(testIds.journeyMap)).toBeVisible();

  await page.getByTestId(testIds.eventSimulator).click();
  await page.getByTestId(testIds.eventClosureButton).click();

  await expect(page.getByTestId(testIds.replanPanel)).toBeVisible();
  await expect(page.getByTestId(testIds.replanDiff)).toContainText("Tech Art");
  await expect(page.getByTestId(testIds.protectedCommitment)).toContainText("River Cruise");

  await page.getByTestId(testIds.acceptReplan).click();
  await expect(page.getByTestId(testIds.journeyStatus)).toContainText("ACTIVE");

  await page.reload();
  await expect(page.getByTestId(testIds.protectedCommitment)).toContainText("River Cruise");
});
