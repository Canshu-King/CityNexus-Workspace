import { expect, test } from "@playwright/test";

test("V10 live execution panel exposes the server clock and evidence trail", async ({
  page,
  request,
}) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/v8/live");
  await expect(page.getByRole("heading", { name: "Choose your next leg." })).toBeVisible();

  const panel = page.getByTestId("v10-live-execution-panel");
  await expect(panel).toBeVisible();
  await expect(panel.getByText("CLOCK", { exact: true })).toBeVisible();
  await expect(panel.getByText("read-only ready", { exact: true })).toBeVisible();

  const journeyId = await page.evaluate(() => localStorage.getItem("citynexus.v8.journey_id"));
  expect(journeyId).toBeTruthy();
  const clockResponse = await request.get(
    `/api/v1/journeys/${journeyId}/execution-clock`,
  );
  expect(clockResponse.ok()).toBeTruthy();
  const clock = await clockResponse.json();
  expect(clock.source).toBe("EXECUTION_CLOCK");
  expect(clock.timezone).toBe("Asia/Shanghai");

  await panel.locator("summary").click();
  await expect(panel.getByText(/No web observation is authoritative/)).toBeVisible();
});
