import { expect, test } from "@playwright/test";

test("real-world trip operations: inbox to luggage-aware autonomous recovery", async ({ page, request }) => {
  const reset = await request.post("/api/v1/demo/reset");
  const ids = await reset.json();
  const created = await request.post("/api/v1/journeys", {
    data: {
      traveler_id: ids.traveler_id,
      title: "Tianjin rail arrival · real trip operations",
      city_code: "CN-TIANJIN",
      timezone: "Asia/Shanghai",
      start_at: "2026-10-09T08:00:00+08:00",
      end_at: "2026-10-11T15:00:00+08:00",
      budget: { amount_minor: 120000, currency: "CNY" },
      stay_budget: { amount_minor: 70000, currency: "CNY" },
      party_size: 2,
      occupancy: { adults: 2, rooms: 1 },
      arrival_anchor: { at: "2026-10-09T08:00:00+08:00", location: "Tianjin West Station" },
      departure_anchor: { at: "2026-10-11T15:00:00+08:00", location: "Tianjin Binhai Airport" },
    },
  });
  expect(created.ok()).toBeTruthy();
  const journey = await created.json();
  await request.put(`/api/v1/journeys/${journey.id}/operations/luggage`, {
    data: { baggage_present: true, baggage_size_class: "MEDIUM", luggage_drop_required: true },
  });
  await page.context().grantPermissions(["geolocation"], { origin: "http://127.0.0.1:4173" });
  await page.context().setGeolocation({ latitude: 39.1366, longitude: 117.1696, accuracy: 12 });

  await page.addInitScript((journeyId) => localStorage.setItem("citynexus.v8.journey_id", journeyId), journey.id);
  await page.goto("/v8/bookings");
  await expect(page.getByRole("heading", { name: "Your real reservations, protected." })).toBeVisible();
  const reservation = {
    reservation_type: "RAIL",
    provider_key: "user-confirmed-rail",
    confirmation_ref: "G12345-V9-UI",
    origin: { name: "Shanghai Hongqiao" },
    destination: { name: "Tianjin West Station", latitude: 39.1366, longitude: 117.1696 },
    scheduled_departure_at: "2026-10-09T03:30:00+08:00",
    scheduled_arrival_at: "2026-10-09T08:00:00+08:00",
    price_amount_minor: 55300,
    currency: "CNY",
    price_status: "KNOWN",
  };
  await page.getByLabel("Reservation JSON").fill(JSON.stringify(reservation));
  await page.getByRole("button", { name: "Review and protect" }).click();
  await expect(page.getByText("Reservation confirmed and protected")).toBeVisible();
  await expect(page.getByTestId("wallet-reservation")).toContainText("G12345-V9-UI");

  const generated = await request.post(`/api/v1/journeys/${journey.id}/stay-options/generate`);
  expect(generated.ok()).toBeTruthy();
  await page.goto("/v8/stay");
  await page.getByTestId("stay-offer-card").first().click();
  await expect(page.getByText("Stay selected · Journey impact recalculated")).toBeVisible();

  await page.getByRole("button", { name: "Intelligence" }).click();
  await page.getByRole("button", { name: "Enable reversible recovery" }).click();
  await expect(page.getByText("Autonomous recovery is enabled")).toBeVisible();
  await page.getByRole("button", { name: "Live Journey" }).click();
  await expect(page.getByText(/Provider-backed route/)).toContainText("WGS84");
  await expect(page.getByRole("heading", { name: /Luggage drop/ })).toBeVisible();
  await expect(page.getByRole("link", { name: "NAVIGATE →" })).toHaveAttribute(
    "href",
    /uri\.amap\.com\/navigation\?to=.*coordinate=wgs84/,
  );
  await page.getByRole("button", { name: "Update location" }).click();
  await expect(page.getByText(/Location updated · accuracy 12 m/)).toBeVisible();
  await expect(page.getByRole("button", { name: /Your location/ })).toBeVisible();
  await page.getByRole("button", { name: "Rain detected" }).click();
  await expect(page.getByText(/Autopilot recovered the exposed leg/)).toBeVisible();

  const experience = await request.get(`/api/v1/journeys/${journey.id}/experience`);
  const body = await experience.json();
  expect(body.active_plan.id).toBeTruthy();
  expect(body.active_plan.legs.length).toBe(body.active_plan.activities.length - 1);
  expect(body.active_plan.activities.map((item: { metadata: { role: string } }) => item.metadata.role)).toEqual(expect.arrayContaining(["LUGGAGE_DROP", "CHECK_IN"]));

  await page.setViewportSize({ width: 390, height: 844 });
  await expect(page.getByText("NOW", { exact: true })).toBeVisible();
  await expect(page.getByText("NEXT · LEAVE BY", { exact: true })).toBeVisible();
  await expect(page.locator(".v9-map-marker").first()).toBeVisible();
  for (const button of await page.getByRole("navigation", { name: "Mobile navigation" }).getByRole("button").all()) {
    const box = await button.boundingBox();
    expect(box?.height).toBeGreaterThanOrEqual(44);
  }
  const navigateBox = await page.getByRole("link", { name: "NAVIGATE →" }).boundingBox();
  expect(navigateBox?.height).toBeGreaterThanOrEqual(44);
  const contrast = await page.getByTestId("live-journey-current").evaluate((element) => {
    const parse = (value: string) => value.match(/\d+/g)?.slice(0, 3).map(Number) ?? [0, 0, 0];
    const luminance = (rgb: number[]) => rgb.map((value) => value / 255).map((value) => value <= 0.03928 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4).reduce((sum, value, index) => sum + value * [0.2126, 0.7152, 0.0722][index], 0);
    const style = getComputedStyle(element);
    const foreground = luminance(parse(style.color));
    const background = luminance(parse(getComputedStyle(element.closest(".v8-live-now")!).backgroundColor));
    return (Math.max(foreground, background) + 0.05) / (Math.min(foreground, background) + 0.05);
  });
  expect(contrast).toBeGreaterThanOrEqual(4.5);
  await page.screenshot({ path: "../reports/product-v9/ui/live-journey-mobile.png", fullPage: true });
  await page.getByRole("button", { name: "Switch language" }).click();
  await expect(page.getByRole("navigation", { name: "Mobile navigation" }).getByText("旅行票夹")).toBeVisible();

  const manifest = await request.get("/manifest.webmanifest");
  expect(manifest.ok()).toBeTruthy();
  expect((await manifest.json()).display).toBe("standalone");
  await expect.poll(async () => page.evaluate(() => navigator.serviceWorker?.ready.then(() => true))).toBeTruthy();
  await page.reload();
  await expect(page.getByTestId("v8-live-journey")).toBeVisible();
  await expect.poll(async () => page.evaluate(() => Boolean(navigator.serviceWorker?.controller))).toBeTruthy();
  await page.context().setOffline(true);
  await page.reload();
  await expect(page.getByRole("heading", { name: "Your next 24 hours are saved." })).toBeVisible();
  await expect(page.getByText(/Financial actions are disabled offline/)).toBeVisible();
  await page.screenshot({ path: "../reports/product-v9/ui/offline-journey-mobile.png", fullPage: true });
  await page.context().setOffline(false);
});
