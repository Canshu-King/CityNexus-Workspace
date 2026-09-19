import { expect, test } from "@playwright/test";

test.describe("V8 product experience", () => {
  test("completes the multi-day stay and autonomous recovery journey", async ({ page }) => {
    await page.goto("/v8");
    await expect(page.getByRole("heading", { name: "Your next city, already considered." })).toBeVisible();
    await expect(page.getByTestId("v8-maplibre-panel")).toBeVisible();
    await page.screenshot({ path: "../reports/product-v8/ui/after/journey-hub-desktop.png", fullPage: true });

    await page.getByRole("button", { name: "Stay Explorer" }).click();
    await expect(page.getByTestId("v8-stay-explorer")).toBeVisible();
    await expect(page.getByTestId("stay-offer-card")).toHaveCount(4);
    await page.screenshot({ path: "../reports/product-v8/ui/after/stay-explorer-desktop.png", fullPage: true });
    await page.getByTestId("stay-offer-card").nth(1).click();

    await page.getByRole("button", { name: "Trip Studio" }).click();
    await expect(page.getByTestId("v8-trip-studio")).toBeVisible();
    await page.screenshot({ path: "../reports/product-v8/ui/after/trip-studio-desktop.png", fullPage: true });

    await page.getByRole("button", { name: "Intelligence" }).click();
    await page.getByRole("button", { name: "Enable reversible recovery" }).click();
    await expect(page.getByText("Autonomous recovery is enabled")).toBeVisible();
    await page.screenshot({ path: "../reports/product-v8/ui/after/intelligence-desktop.png", fullPage: true });

    await page.getByRole("button", { name: "Live Journey" }).click();
    await expect(page.getByTestId("live-journey-current")).toBeVisible();
    await page.getByRole("button", { name: "Rain detected" }).click();
    await expect(page.getByText(/Autopilot recovered the exposed leg/)).toBeVisible();
    await page.getByRole("button", { name: "Compare all modes" }).click();
    await expect(page.getByRole("dialog", { name: "Choose a calm route" })).toBeVisible();
    await page.screenshot({ path: "../reports/product-v8/ui/after/mobility-sheet-desktop.png", fullPage: true });
    await page.getByRole("button", { name: "Close mobility comparison" }).click();

    await page.reload();
    await expect(page.getByTestId("live-journey-current")).toBeVisible();
    await expect(page.getByText(/Provider-backed route/)).toContainText("WGS84");
  });

  test("keeps the mobile Journey, Map, AI, Bookings, Me composition usable", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto("/v8/live");
    await expect(page.getByTestId("v8-live-journey")).toBeVisible();
    await expect(page.getByRole("navigation", { name: "Mobile navigation" }).getByRole("button", { name: "Map" })).toBeVisible();
    await page.getByRole("button", { name: "Compare all modes" }).click();
    await expect(page.getByRole("dialog")).toBeVisible();
    await page.screenshot({ path: "../reports/product-v8/ui/after/mobility-sheet-mobile.png", fullPage: true });
    await page.getByRole("button", { name: "Close mobility comparison" }).click();
    await page.getByRole("navigation", { name: "Mobile navigation" }).getByRole("button", { name: "AI" }).click();
    await expect(page.getByTestId("v8-agent-composer")).toBeVisible();
    await page.screenshot({ path: "../reports/product-v8/ui/after/agent-composer-mobile.png", fullPage: true });
    await page.getByTestId("v8-agent-submit").click();
    await expect(page.getByText(/Mission (captured|activated)/)).toBeVisible();
    await page.getByRole("navigation", { name: "Mobile navigation" }).getByRole("button", { name: "Travel Wallet" }).click();
    await expect(page.getByTestId("v8-bookings")).toBeVisible();
    await page.getByRole("navigation", { name: "Mobile navigation" }).getByRole("button", { name: "Me" }).click();
    await expect(page.getByText("Your preferences, your boundary.")).toBeVisible();
    await page.getByRole("navigation", { name: "Mobile navigation" }).getByRole("button", { name: "Journey" }).click();
    await expect(page.getByRole("heading", { name: "Your next city, already considered." })).toBeVisible();
  });
});
