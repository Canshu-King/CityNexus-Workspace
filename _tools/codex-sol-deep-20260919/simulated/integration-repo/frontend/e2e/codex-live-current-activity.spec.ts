import { expect, test } from "@playwright/test";

const journeyId = "codex-current-activity";

test("Live follows current_activity_id after the journey advances", async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem("citynexus.v8.journey_id", "codex-current-activity");
    localStorage.setItem("citynexus.locale", "en-US");
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    (navigator as any).serviceWorker.register = () => Promise.resolve({});
  });

  const activities = ["Completed museum", "Current lunch", "Next ferry"].map(
    (title, index) => ({
      id: `act-${index + 1}`,
      sequence_no: index + 1,
      type: "visit",
      title,
      start_at: `2026-10-09T${10 + index}:00:00+08:00`,
      end_at: `2026-10-09T${11 + index}:00:00+08:00`,
      locked: false,
      protected: false,
      metadata: {},
    }),
  );
  const leg = (id: string, mode: string, duration_min: number) => ({
    id, from_key: `${id}-from`, to_key: `${id}-to`, mode, duration_min,
    provider_key: "fixture", provenance: "EXPLICIT_FROZEN_FIXTURE", crs: "EPSG:4326",
    geometry: { type: "Feature", properties: {}, geometry: { type: "LineString", coordinates: [[118.08, 24.46], [118.09, 24.47]] } },
  });
  const legs = [leg("leg-1", "WALK", 10), leg("leg-2", "TRANSIT", 25)];
  const experience = {
    journey: { id: journeyId, traveler_id: "traveler", title: "Cursor repro", city_code: "CN-XIAMEN", timezone: "Asia/Shanghai", start_at: "2026-10-09T09:00:00+08:00", end_at: "2026-10-10T09:00:00+08:00", budget: { amount_minor: 100000, currency: "CNY" } },
    trip: { arrival_anchor: {}, departure_anchor: {}, party_size: 1, occupancy: {}, stay_budget: { amount_minor: 0, currency: "CNY" }, baggage: { present: false, luggage_drop_required: false } },
    offers: [], options: [], selected_option_id: null, mobility_facts: [],
    active_plan: { id: "plan-1", version_no: 1, status: "ACTIVE", source: "CODEX_REPRO", current_activity_id: "act-2", activities, legs, user_location: null, disruptions: [] },
    recovery: null,
    experience_flags: { needs_review: false, recovery_required: false, staleness: false, feasibility_failures: [] },
  };

  await page.route(/\/api\/v1\//, (route) => {
    const path = new URL(route.request().url()).pathname;
    const body = path.endsWith("/experience") ? experience
      : path.endsWith("/replans") || path.endsWith("/plans") ? []
      : path.endsWith("/offline-snapshot") ? { journey_id: journeyId, sequence: 1, snapshot: { read_only: true }, provider_freshness: {}, updated_at: "2026-10-09T10:00:00Z" }
      : path.endsWith("/agent-policy") ? { mode: "ADVISORY", auto_accept_replan: false, version: 1 }
      : path.endsWith("/wallet") ? { reservations: [], commitments: [], offline_ready: true }
      : path.endsWith("/twin") ? { id: "twin", context: {} }
      : {};
    return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(body) });
  });

  await page.goto("/v8/live", { waitUntil: "domcontentloaded" });
  await expect(page.getByTestId("live-journey-current")).toHaveText("Current lunch");
  await expect(page.getByText(/Next ferry/).first()).toBeVisible();
});
