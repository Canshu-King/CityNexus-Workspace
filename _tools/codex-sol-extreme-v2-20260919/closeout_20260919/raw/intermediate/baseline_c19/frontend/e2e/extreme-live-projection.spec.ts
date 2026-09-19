import { expect, test, type Page } from "@playwright/test";

const JID = "extreme-projection";

function activity(id: string, title: string, sequence_no: number) {
  return { id, sequence_no, type: "visit", title, start_at: `2026-10-09T${9 + sequence_no}:00:00+08:00`, end_at: `2026-10-09T${10 + sequence_no}:00:00+08:00`, locked: false, protected: false, metadata: {} };
}

async function open(page: Page, cursor: string | null) {
  await page.addInitScript(() => {
    localStorage.setItem("citynexus.v8.journey_id", "extreme-projection");
    localStorage.setItem("citynexus.locale", "en-US");
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    (navigator as any).serviceWorker.register = () => Promise.resolve({});
  });
  const activities = [activity("a", "Alpha", 1), activity("b", "Bravo", 2), activity("c", "Charlie", 3)];
  const experience = {
    journey: { id: JID, traveler_id: "t", title: "Projection", city_code: "CN-XIAMEN", timezone: "Asia/Shanghai", start_at: "2026-10-09T09:00:00+08:00", end_at: "2026-10-10T09:00:00+08:00", budget: { amount_minor: 100000, currency: "CNY" } },
    trip: { arrival_anchor: {}, departure_anchor: {}, party_size: 1, occupancy: {}, stay_budget: { amount_minor: 0, currency: "CNY" }, baggage: { present: false, luggage_drop_required: false } },
    offers: [], options: [], selected_option_id: null, mobility_facts: [],
    active_plan: { id: "p", version_no: 1, status: "ACTIVE", source: "EXTREME", current_activity_id: cursor, activities, legs: [], user_location: null, disruptions: [] },
    recovery: null, experience_flags: { needs_review: false, recovery_required: false, staleness: cursor === "stale", feasibility_failures: [] },
  };
  await page.route(/\/api\/v1\//, route => {
    const path = new URL(route.request().url()).pathname;
    const body = path.endsWith("/experience") ? experience
      : path.endsWith("/replans") || path.endsWith("/plans") ? []
      : path.endsWith("/offline-snapshot") ? { journey_id: JID, sequence: 1, snapshot: { read_only: true }, provider_freshness: {}, updated_at: "2026-10-09T10:00:00Z" }
      : path.endsWith("/agent-policy") ? { mode: "ADVISORY", auto_accept_replan: false, version: 1 }
      : path.endsWith("/wallet") ? { reservations: [], commitments: [], offline_ready: true }
      : path.endsWith("/execution-clock") ? { now: "2026-10-09T11:00:00+08:00", timezone: "Asia/Shanghai", current_activity_id: cursor }
      : path.endsWith("/web-observations") ? []
      : path.endsWith("/twin") ? { id: "twin", current_activity_id: cursor, context: {} } : {};
    return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(body) });
  });
  await page.goto("/v8/live", { waitUntil: "domcontentloaded" });
}

test("middle cursor drives Live Now and Next", async ({ page }) => {
  await open(page, "b");
  await expect(page.getByTestId("live-journey-current")).toHaveText("Bravo");
  await expect(page.locator("body")).toContainText("Charlie");
});

test("final cursor has no fabricated Next", async ({ page }) => {
  await open(page, "c");
  await expect(page.getByTestId("live-journey-current")).toHaveText("Charlie");
  await expect(page.getByText(/Alpha|Bravo/)).toHaveCount(0);
});

test("absent cursor permits pre-execution fallback", async ({ page }) => {
  await open(page, null);
  await expect(page.getByTestId("live-journey-current")).toHaveText("Alpha");
  await expect(page.getByText(/Bravo/).first()).toBeVisible();
});

test("present but unknown cursor fails closed", async ({ page }) => {
  await open(page, "stale");
  await expect(page.getByTestId("live-journey-current")).not.toHaveText(/Alpha|Bravo|Charlie/);
  await expect(page.getByText(/Alpha|Bravo|Charlie/)).toHaveCount(0);
});
