import { useEffect, useMemo, useState } from "react";
import { Icon } from "../components/v8/Icon";
import { MapPanel } from "../components/v8/MapPanel";
import { AgentComposer } from "../features/agent/AgentComposer";
import { MobilitySheet } from "../features/mobility/MobilitySheet";
import { StayExplorer } from "../features/stay/StayExplorer";
import { ControlTowerPanel } from "../features/intelligence/ControlTowerPanel";
import { V10LiveExecutionPanel } from "../features/execution/V10LiveExecutionPanel";
import { BookingArtifactScanner } from "../features/inbox/BookingArtifactScanner";
import { JourneyInboxWorkbench } from "../features/inbox/JourneyInboxWorkbench";
import { PushCapabilityCard } from "../features/notifications/PushCapabilityCard";
import { TwinPanel } from "../features/traveler-twin/TwinPanel";
import { SortableActivityList } from "../features/studio/SortableActivityList";
import { V12AuthoritativeJourneyPanel } from "../features/execution/V12AuthoritativeJourneyPanel";
import { V12TripStudioPanel } from "../features/studio/V12TripStudioPanel";
import {
  useAuthoritativePlans,
  useAuthoritativeTwin,
  type JourneyTwin,
  type PlanVersion,
} from "../api/v12Authoritative";
import { desktopRoutes, mobileRoutes } from "../routes/v8Routes";
import {
  readOfflineJourney,
  saveOfflineJourney,
  type OfflineJourney,
} from "../lib/offlineJourney";
import { tripCopy, type TripLocale } from "../i18n/tripOperations";
import { v8Modes, type V8Data, type V8Mode } from "./v8Types";

type Policy = {
  mode: "ADVISORY" | "ASSISTED" | "AUTONOMOUS";
  auto_accept_replan: boolean;
  version: number;
  max_auto_replan_cost_delta_minor: number;
  max_auto_loss_minor: number;
  max_auto_schedule_drift_min: number;
};
type Wallet = {
  reservations: Array<{
    id: string;
    type: string;
    confirmation_ref: string;
    scheduled_departure_at: string;
    scheduled_arrival_at: string;
    realtime_status: string;
    price: {
      amount_minor: number | null;
      currency: string | null;
      status: string;
    };
  }>;
  commitments: Array<{
    id: string;
    level: string;
    kind: string;
    external_ref: string | null;
    status: string;
  }>;
  offline_ready: boolean;
};

async function v8Request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    ...init,
  });
  const body = await response.json();
  if (!response.ok)
    throw new Error(
      body?.detail ??
        body?.error?.message ??
        `Request failed (${response.status})`,
    );
  return body as T;
}

function money(minor: number | null | undefined, currency = "CNY") {
  return minor == null
    ? "Provider price unavailable"
    : new Intl.NumberFormat("zh-CN", {
        style: "currency",
        currency,
        maximumFractionDigits: 0,
      }).format(minor / 100);
}
function date(value?: string) {
  return value
    ? new Intl.DateTimeFormat("en-GB", {
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
        hour12: false,
      }).format(new Date(value))
    : "—";
}

export function V8Experience() {
  const [route, setRoute] = useState(
    window.location.pathname.replace(/^\/v8\/?/, "") || "hub",
  );
  const [data, setData] = useState<V8Data | null>(null);
  const [mode, setMode] = useState<V8Mode>("TRANSIT");
  const [comparison, setComparison] = useState<V8Data["mobility_facts"]>([]);
  const [policy, setPolicy] = useState<Policy | null>(null);
  const [busy, setBusy] = useState(true);
  const [message, setMessage] = useState<string | null>(null);
  const [sheetOpen, setSheetOpen] = useState(false);
  const [wallet, setWallet] = useState<Wallet | null>(null);
  const [offline, setOffline] = useState<OfflineJourney | null>(null);
  const [locale, setLocale] = useState<TripLocale>(() =>
    localStorage.getItem("citynexus.locale") === "zh-CN" ? "zh-CN" : "en",
  );
  const copy = tripCopy(locale);
  const authoritativePlans = useAuthoritativePlans(data?.journey.id ?? null);
  const authoritativeTwin = useAuthoritativeTwin(data?.journey.id ?? null);
  const authoritativePlan =
    authoritativePlans.data?.find((item) => item.status === "ACTIVE" || item.status === "SELECTED") ??
    authoritativePlans.data?.[0] ??
    null;

  const load = async (journeyId: string) => {
    const experience = await v8Request<V8Data>(
      `/api/v1/journeys/${journeyId}/experience`,
    );
    setData(experience);
    const selected =
      experience.options.find(
        (item) => item.id === experience.selected_option_id,
      ) ?? experience.options[0];
    const firstLeg = selected?.leg_mode_map[0];
    if (firstLeg)
      setComparison(
        experience.mobility_facts.filter(
          (item) =>
            item.from_key === firstLeg.from_key &&
            item.to_key === firstLeg.to_key,
        ),
      );
    const [nextPolicy, nextWallet, nextOffline] = await Promise.all([
      v8Request<Policy>(
        `/api/v1/travelers/${experience.journey.traveler_id}/agent-policy`,
      ),
      v8Request<Wallet>(`/api/v1/journeys/${journeyId}/wallet`),
      v8Request<OfflineJourney>(
        `/api/v1/journeys/${journeyId}/offline-snapshot`,
      ),
    ]);
    setPolicy(nextPolicy);
    setWallet(nextWallet);
    setOffline(nextOffline);
    await saveOfflineJourney(nextOffline);
  };

  useEffect(() => {
    let cancelled = false;
    async function boot() {
      setBusy(true);
      try {
        let journeyId = localStorage.getItem("citynexus.v8.journey_id");
        if (journeyId) {
          try {
            await load(journeyId);
          } catch (error) {
            const saved = await readOfflineJourney(journeyId);
            if (saved) {
              if (!cancelled) {
                setOffline(saved);
                setMessage(
                  "Network unavailable · showing your read-only saved journey.",
                );
                setBusy(false);
              }
              return;
            }
            localStorage.removeItem("citynexus.v8.journey_id");
            journeyId = null;
            if (error instanceof Error && !navigator.onLine) throw error;
          }
        }
        if (!journeyId) {
          const traveler = await v8Request<{ id: string }>(
            "/api/v1/travelers",
            {
              method: "POST",
              body: JSON.stringify({
                display_name: "City traveler",
                locale: "en-GB",
                timezone: "Asia/Shanghai",
              }),
            },
          );
          const journey = await v8Request<{ id: string }>("/api/v1/journeys", {
            method: "POST",
            body: JSON.stringify({
              traveler_id: traveler.id,
              title: "Tianjin · stay-aware weekend",
              city_code: "CN-TIANJIN",
              timezone: "Asia/Shanghai",
              start_at: "2026-10-09T18:00:00+08:00",
              end_at: "2026-10-11T15:00:00+08:00",
              budget: { amount_minor: 120000, currency: "CNY" },
              stay_budget: { amount_minor: 70000, currency: "CNY" },
              party_size: 2,
              occupancy: { adults: 2, rooms: 1 },
              arrival_anchor: {
                at: "2026-10-09T18:00:00+08:00",
                location: "Tianjin West Station",
              },
              departure_anchor: {
                at: "2026-10-11T15:00:00+08:00",
                location: "Tianjin Binhai Airport",
              },
            }),
          });
          journeyId = journey.id;
          localStorage.setItem("citynexus.v8.journey_id", journeyId);
          await v8Request(
            `/api/v1/journeys/${journeyId}/stay-options/generate`,
            { method: "POST" },
          );
          await load(journeyId);
        }
        if (!cancelled) setMessage(null);
      } catch (error) {
        const journeyId = localStorage.getItem("citynexus.v8.journey_id");
        const saved = journeyId ? await readOfflineJourney(journeyId) : null;
        if (!cancelled) {
          setOffline(saved);
          setMessage(
            saved
              ? "Network unavailable · showing your read-only saved journey."
              : error instanceof Error
                ? error.message
                : "Unable to load the journey",
          );
        }
      }
      if (!cancelled) setBusy(false);
    }
    void boot();
    return () => {
      cancelled = true;
    };
  }, []);

  const selected =
    data?.options.find((item) => item.id === data.selected_option_id) ??
    data?.options[0] ??
    null;
  const navigate = (next: string) => {
    const value = next || "hub";
    window.history.pushState({}, "", `/v8/${value}`);
    setRoute(value);
  };
  const switchLocale = () => {
    const next = locale === "en" ? "zh-CN" : "en";
    localStorage.setItem("citynexus.locale", next);
    document.documentElement.lang = next;
    setLocale(next);
  };
  const selectOption = async (id: string) => {
    if (!data) return;
    setBusy(true);
    try {
      await v8Request(
        `/api/v1/journeys/${data.journey.id}/stay-options/${id}/select`,
        { method: "POST" },
      );
      await load(data.journey.id);
      setMessage(
        "Stay selected · Journey impact recalculated from captured evidence.",
      );
    } finally {
      setBusy(false);
    }
  };
  const changeMode = async (next: V8Mode) => {
    if (!data || !selected) return;
    setMode(next);
    setBusy(true);
    try {
      await v8Request(
        `/api/v1/journeys/${data.journey.id}/stay-options/${selected.id}/mode`,
        { method: "POST", body: JSON.stringify({ mode: next }) },
      );
      const response = await v8Request<{ facts: V8Data["mobility_facts"] }>(
        `/api/v1/journeys/${data.journey.id}/mobility/compare`,
        { method: "POST", body: JSON.stringify({ mode: next }) },
      );
      const firstLeg = selected.leg_mode_map[0];
      setComparison(
        firstLeg
          ? response.facts.filter(
              (item) =>
                item.from_key === firstLeg.from_key &&
                item.to_key === firstLeg.to_key,
            )
          : response.facts,
      );
      await load(data.journey.id);
    } finally {
      setBusy(false);
    }
  };
  const triggerRain = async () => {
    if (!data || !selected) return;
    setBusy(true);
    try {
      const result = await v8Request<{
        decision: string;
        executed: boolean;
        after_mode: string;
        reason_codes: string[];
      }>(
        `/api/v1/journeys/${data.journey.id}/stay-options/${selected.id}/autopilot/recover`,
        { method: "POST", body: JSON.stringify({ state: "RAIN" }) },
      );
      await load(data.journey.id);
      setMessage(
        result.executed
          ? `Autopilot recovered the exposed leg with ${result.after_mode.toLowerCase()} · protected commitments preserved.`
          : `Autopilot paused for confirmation · ${result.reason_codes.join(" · ")}.`,
      );
    } finally {
      setBusy(false);
    }
  };
  const activateAutonomy = async () => {
    if (!data) return;
    setBusy(true);
    try {
      const next = await v8Request<Policy>(
        `/api/v1/travelers/${data.journey.traveler_id}/agent-policy`,
        {
          method: "PUT",
          body: JSON.stringify({
            mode: "AUTONOMOUS",
            auto_accept_replan: true,
            max_auto_replan_cost_delta_minor: 5000,
            max_auto_loss_minor: 0,
            max_auto_schedule_drift_min: 20,
            allowed_activity_types: ["transport"],
            allowed_booking_types: [],
            protected_commitment_levels: ["C3_Guaranteed", "C4_Anchored"],
            allow_auto_commitment_management: false,
            allow_auto_when_provider_degraded: false,
            allow_auto_on_critical_event: false,
          }),
        },
      );
      setPolicy(next);
      setMessage(
        "Autonomous recovery is enabled for reversible transport changes inside this envelope.",
      );
    } finally {
      setBusy(false);
    }
  };
  const submitMission = async (command: string) => {
    if (!data) return;
    setBusy(true);
    try {
      const run = await v8Request<{ run?: { status?: string } }>(
        `/api/v1/journeys/${data.journey.id}/agent/commands`,
        {
          method: "POST",
          body: JSON.stringify({
            command,
            requested_autonomy: "EXECUTE_WITHIN_BOUNDS",
          }),
        },
      );
      await v8Request(`/api/v1/journeys/${data.journey.id}/guardian/mission`, {
        method: "PUT",
        body: JSON.stringify({
          command,
          requested_autonomy: "EXECUTE_WITHIN_BOUNDS",
        }),
      });
      setMessage(
        run.run?.status === "UNAVAILABLE"
          ? "Mission captured · external model unavailable, so the deterministic CityNexus path remains active."
          : "Mission activated · CityNexus will monitor the journey inside the current authority envelope.",
      );
    } finally {
      setBusy(false);
    }
  };
  const importReservation = async (reservation: Record<string, unknown>) => {
    if (!data) return;
    setBusy(true);
    try {
      const draft = await v8Request<{ id: string; status: string }>(
        `/api/v1/journeys/${data.journey.id}/inbox/import`,
        {
          method: "POST",
          body: JSON.stringify({
            artifact_type: "STRUCTURED_JSON",
            payload: { reservation },
          }),
        },
      );
      if (draft.status === "READY_FOR_CONFIRMATION")
        await v8Request(
          `/api/v1/journeys/${data.journey.id}/inbox/${draft.id}/confirm`,
          { method: "POST" },
        );
      await load(data.journey.id);
      setMessage(
        draft.status === "READY_FOR_CONFIRMATION"
          ? "Reservation confirmed and protected in your Travel Wallet."
          : "Reservation needs review before it can become a commitment.",
      );
    } finally {
      setBusy(false);
    }
  };
  const shareForegroundLocation = async () => {
    if (!data || !navigator.geolocation) return;
    navigator.geolocation.getCurrentPosition(
      async (position) => {
        await v8Request(`/api/v1/journeys/${data.journey.id}/location`, {
          method: "POST",
          body: JSON.stringify({
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
            accuracy_m: position.coords.accuracy,
            captured_at: new Date(position.timestamp).toISOString(),
          }),
        });
        await load(data.journey.id);
        setMessage(
          `Location updated · accuracy ${Math.round(position.coords.accuracy)} m.`,
        );
      },
      () => setMessage("Location permission was not granted."),
      { enableHighAccuracy: true, maximumAge: 30000 },
    );
  };

  if (busy && !data)
    return (
      <div className="v8-loading">
        <div className="v8-brand-mark">CN</div>
        <p>Preparing a captured city weekend…</p>
        <span>Anchors · stays · mobility facts · feasibility</span>
      </div>
    );
  if (!data && offline)
    return <OfflineJourneyView value={offline} message={message} />;
  if (!data)
    return (
      <div className="v8-loading">
        <div className="v8-brand-mark">CN</div>
        <p>{message ?? "No journey available"}</p>
      </div>
    );

  return (
    <div className="v8-product-shell">
      <aside className="v8-sidebar">
        <div className="v8-brand">
          <div className="v8-brand-mark">CN</div>
          <div>
            <strong>CityNexus</strong>
            <span>journey intelligence</span>
          </div>
        </div>
        <div className="v8-workspace-label">
          Workspace <span>Trip operations</span>
        </div>
        <nav className="v8-nav" aria-label="Product navigation">
          {desktopRoutes.map((item) => (
            <button
              key={item.key}
              className={route === item.key ? "active" : ""}
              onClick={() => navigate(item.key)}
            >
              <Icon name={item.icon} />
              <span>{copy[item.key]}</span>
              {item.key === "live" && <i />}
            </button>
          ))}
        </nav>
        <div className="v8-sidebar-bottom">
          <div className="v8-sync">
            <span className="status-dot" />
            Journey facts synced<div>{data.options.length} plans · 5 modes</div>
          </div>
          <button className="v8-user" onClick={() => navigate("me")}>
            <span>CT</span>
            <div>
              <b>City traveler</b>
              <small>Asia/Shanghai</small>
            </div>
            <em>•••</em>
          </button>
        </div>
      </aside>
      <main className="v8-main">
        <header className="v8-topbar">
          <button
            className="v8-mobile-menu"
            aria-label="Open navigation"
            onClick={() => navigate("hub")}
          >
            Menu
          </button>
          <div className="v8-breadcrumb">
            <span>Journeys</span>
            <b>/</b>
            <strong>
              {copy[(route in copy ? route : "hub") as keyof typeof copy]}
            </strong>
          </div>
          <div className="v8-top-actions">
            <span className="v8-runtime">
              <span className="status-dot" />
              {policy?.mode === "AUTONOMOUS"
                ? "Autonomy envelope active"
                : "Journey facts ready"}
            </span>
            <button
              className="v9-language"
              aria-label="Switch language"
              onClick={switchLocale}
            >
              {copy.language}
            </button>
            <button className="v8-icon-button" aria-label="Notifications">
              ◌
            </button>
            <button className="v8-avatar" onClick={() => navigate("me")}>
              CT
            </button>
          </div>
        </header>
        {message && (
          <div className="v8-message" role="status">
            {message}
            <button onClick={() => setMessage(null)}>Dismiss</button>
          </div>
        )}
        <div className="v8-content">
          {route === "hub" && (
            <Hub data={data} selected={selected} onNavigate={navigate} />
          )}
          {route === "studio" && (
            <Studio
              data={data}
              selected={selected}
              onNavigate={navigate}
              onRain={triggerRain}
            />
          )}
          {route === "stay" && (
            <StayExplorer
              data={data}
              selected={selected}
              onSelect={(id) => void selectOption(id)}
            />
          )}
          {route === "live" && (
            <>
              <Live
                data={data}
                selected={selected}
                mode={mode}
                comparison={comparison}
                onMode={changeMode}
                onRain={triggerRain}
                onSheet={() => setSheetOpen(true)}
                onLocation={shareForegroundLocation}
                offline={offline}
              />
              <V10LiveExecutionPanel journeyId={data.journey.id} />
            </>
          )}
          {route === "map" && (
            <MapPage
              data={data}
              selected={selected}
              comparison={comparison}
              onSheet={() => setSheetOpen(true)}
            />
          )}
          {route === "bookings" && (
            <>
              <Bookings
                data={data}
                selected={selected}
                wallet={wallet}
                onImport={importReservation}
                busy={busy}
              />
              <div className="v8-page">
                <BookingArtifactScanner />
              </div>
              <div className="v8-page">
                <JourneyInboxWorkbench
                  journeyId={data.journey.id}
                  onConfirmed={() => load(data.journey.id)}
                />
              </div>
            </>
          )}
          {route === "intelligence" && (
            <ControlTowerPanel policy={policy} onActivate={activateAutonomy} />
          )}
          {route === "twin" && <TwinPanel data={data} />}
          {route === "authoritative" && (
            <AuthoritativeExecution
              journeyId={data.journey.id}
              plan={authoritativePlan}
              twin={authoritativeTwin.data ?? null}
              loading={authoritativePlans.isLoading || authoritativeTwin.isLoading}
              onRefresh={() => void Promise.all([authoritativePlans.refetch(), authoritativeTwin.refetch()])}
            />
          )}
          {route === "agent" && (
            <AgentComposer data={data} onSubmit={submitMission} busy={busy} />
          )}
          {route === "me" && (
            <Me data={data} policy={policy} onActivate={activateAutonomy} />
          )}
        </div>
      </main>
      <nav className="v8-mobile-nav" aria-label="Mobile navigation">
        {mobileRoutes.map((item) => (
          <button
            key={item.key}
            className={
              route === item.key || (item.key === "map" && route === "live")
                ? "active"
                : ""
            }
            onClick={() => navigate(item.key)}
          >
            <Icon name={item.icon} />
            <span>{copy[item.key]}</span>
          </button>
        ))}
      </nav>
      {sheetOpen && (
        <MobilitySheet
          facts={comparison.length ? comparison : data.mobility_facts}
          selectedMode={mode}
          onSelect={(next) => void changeMode(next)}
          onClose={() => setSheetOpen(false)}
        />
      )}
    </div>
  );
}

function Hub({
  data,
  selected,
  onNavigate,
}: {
  data: V8Data;
  selected: V8Data["options"][number] | null;
  onNavigate: (route: string) => void;
}) {
  return (
    <section className="v8-page">
      <div className="v8-page-intro">
        <div>
          <p className="v8-kicker">Good afternoon</p>
          <h1>Your next city, already considered.</h1>
          <p className="v8-lede">
            A calm, evidence-backed journey with the stay, movement, luggage,
            and protected moments working as one.
          </p>
        </div>
        <button className="v8-primary" onClick={() => onNavigate("studio")}>
          <Icon name="spark" />
          Open Trip Studio
        </button>
      </div>
      <div className="v8-hero-grid">
        <article className="v8-trip-hero">
          <div className="v8-trip-hero-head">
            <div>
              <span className="v8-status-pill">
                <span className="status-dot" />
                Planning ready
              </span>
              <h2>{data.journey.title}</h2>
              <p>
                <Icon name="calendar" />
                {date(data.journey.start_at)} — {date(data.journey.end_at)}{" "}
                <span>·</span> {data.trip.party_size} travelers
              </p>
            </div>
            <button
              className="v8-quiet-button"
              onClick={() => onNavigate("studio")}
            >
              View plan →
            </button>
          </div>
          <div className="v8-trip-metrics">
            <div>
              <span>Stay budget</span>
              <strong>{money(data.trip.stay_budget.amount_minor)}</strong>
              <small>verified total target</small>
            </div>
            <div>
              <span>Protected margin</span>
              <strong>{selected?.protected_margin_min ?? 0} min</strong>
              <small>deterministic gate</small>
            </div>
            <div>
              <span>Plan health</span>
              <strong className="green">
                {selected?.hard_constraints_passed ? "Feasible" : "Review"}
              </strong>
              <small>weather-aware</small>
            </div>
          </div>
          <div className="v8-anchor-row">
            <div>
              <span>ARRIVAL</span>
              <b>{date(data.trip.arrival_anchor.at)}</b>
              <small>{data.trip.arrival_anchor.location}</small>
            </div>
            <div className="anchor-line" />
            <div>
              <span>DEPARTURE</span>
              <b>{date(data.trip.departure_anchor.at)}</b>
              <small>{data.trip.departure_anchor.location}</small>
            </div>
          </div>
        </article>
        <MapPanel data={data} option={selected} />
      </div>
      <div className="v8-section-heading">
        <div>
          <p className="v8-kicker">Plan at a glance</p>
          <h2>Every day, connected.</h2>
        </div>
        <button className="v8-text-button" onClick={() => onNavigate("stay")}>
          Compare stays →
        </button>
      </div>
      <div className="v8-day-row">
        {selected?.days.map((day) => (
          <button
            key={day.day}
            className="v8-day-card"
            onClick={() => onNavigate("studio")}
          >
            <span>DAY {day.day}</span>
            <strong>{day.label.split(" · ")[0]}</strong>
            <p>{day.activities.join(" · ")}</p>
            <small>
              <span className="mode-mark">{day.mode}</span>{" "}
              {day.anchor.toLowerCase()} anchor
            </small>
          </button>
        ))}
      </div>
    </section>
  );
}

function Studio({
  data,
  selected,
  onNavigate,
  onRain,
}: {
  data: V8Data;
  selected: V8Data["options"][number] | null;
  onNavigate: (route: string) => void;
  onRain: () => Promise<void>;
}) {
  const [draftImpact, setDraftImpact] = useState<{ day: number; count: number } | null>(null);
  return (
    <section className="v8-page" data-testid="v8-trip-studio">
      <div className="v8-page-intro compact">
        <div>
          <p className="v8-kicker">Trip Studio · multi-day plan</p>
          <h1>Shape the journey around what matters.</h1>
          <p className="v8-lede">
            Switch the hotel or a leg mode and CityNexus recomputes the travel
            impact against the same hard commitments.
          </p>
        </div>
        <button className="v8-outline-button" onClick={() => void onRain()}>
          Report rain disruption
        </button>
      </div>
      <div className="v8-studio-layout">
        <div className="v8-days-column">
          {selected?.days.map((day) => (
            <article className="v8-day-detail" key={day.day}>
              <div className="v8-day-detail-title">
                <span>0{day.day}</span>
                <div>
                  <b>{day.label}</b>
                  <small>
                    {day.anchor} anchor · {day.mode}
                  </small>
                </div>
              </div>
              <div className="v8-activity-list">
                <SortableActivityList
                  activities={day.activities}
                  protectedFirst={day.anchor !== "STAY"}
                  onDraft={(draft) => setDraftImpact({ day: day.day, count: draft.length })}
                />
              </div>
            </article>
          ))}
        </div>
        {draftImpact && (
          <div className="v8-impact-drawer" role="status" data-testid="v12-impact-preview">
            <b>Draft reorder preview</b>
            <span>Day {draftImpact.day} · {draftImpact.count} activities</span>
            <small>Feasibility, mobility, cost, opening hours, and protected C4 impact will be checked before acceptance.</small>
          </div>
        )}
        <aside className="v8-studio-aside">
          <div className="v8-aside-heading">
            <span>SELECTED STAY</span>
            <button onClick={() => onNavigate("stay")}>Change</button>
          </div>
          {selected && (
            <div className="v8-selected-stay">
              <div className="v8-hotel-thumb">
                <Icon name="bed" />
              </div>
              <div>
                <b>{selected.stay.property_name}</b>
                <span>{selected.stay.room_type}</span>
                <strong>
                  {money(selected.stay.total_amount_minor)} <small>total</small>
                </strong>
              </div>
            </div>
          )}
          <div className="v8-cost-lines">
            <div>
              <span>Stay total</span>
              <b>{money(selected?.stay_total_minor)}</b>
            </div>
            <div>
              <span>Daily movement</span>
              <b>{money(selected?.daily_travel_minor)}</b>
            </div>
            <div>
              <span>Walking exposure</span>
              <b>{selected?.walking_min} min</b>
            </div>
            <div className="total">
              <span>Plan health</span>
              <b className="green">
                Protected · {selected?.protected_margin_min} min slack
              </b>
            </div>
          </div>
          <div className="v8-feasibility">
            <span className="status-dot" />
            <div>
              <b>Deterministic feasibility passed</b>
              <small>
                Arrival, departure, budget, and protected commitments verified.
              </small>
            </div>
          </div>
        </aside>
      </div>
    </section>
  );
}

function AuthoritativeExecution({
  journeyId,
  plan,
  twin,
  loading,
  onRefresh,
}: {
  journeyId: string;
  plan: PlanVersion | null;
  twin: JourneyTwin | null;
  loading: boolean;
  onRefresh: () => void;
}) {
  const execution = (twin?.context as { execution?: { next_activity_id?: string | null } } | undefined)?.execution;
  return (
    <section className="v8-page" data-testid="v12-authoritative-page">
      <div className="v8-page-intro compact">
        <div>
          <p className="v8-kicker">V12 · plan, mobile, Edge, and twin</p>
          <h1>Authoritative trip execution.</h1>
          <p className="v8-lede">
            One frozen PlanVersion feeds the live JourneyTwin, the offline
            snapshot, the map, and the PIC Edge companion.
          </p>
        </div>
        <button className="v8-outline-button" type="button" onClick={onRefresh}>
          Refresh truth
        </button>
      </div>
      {loading && <p className="v8-muted">Loading authoritative state…</p>}
      {!loading && !plan && (
        <div className="v8-feasibility">
          <span className="status-dot" />
          <div>
            <b>No authoritative PlanVersion yet.</b>
            <small>Compose from the server Trip Studio to create the frozen multi-day execution path.</small>
          </div>
        </div>
      )}
      {plan && (
        <>
          <V12AuthoritativeJourneyPanel
            journeyId={journeyId}
            plan={plan}
            nowActivityId={twin?.current_activity_id}
            nextActivityId={execution?.next_activity_id ?? null}
            onTransition={onRefresh}
          />
          <V12TripStudioPanel journeyId={journeyId} plan={plan} onAccepted={onRefresh} />
        </>
      )}
    </section>
  );
}

function Live({
  data,
  selected,
  mode,
  comparison,
  onMode,
  onRain,
  onSheet,
  onLocation,
  offline,
}: {
  data: V8Data;
  selected: V8Data["options"][number] | null;
  mode: V8Mode;
  comparison: V8Data["mobility_facts"];
  onMode: (mode: V8Mode) => Promise<void>;
  onRain: () => Promise<void>;
  onSheet: () => void;
  onLocation: () => Promise<void>;
  offline: OfflineJourney | null;
}) {
  const now = data.active_plan?.activities[0];
  const next = data.active_plan?.activities[1];
  const nextLeg = data.active_plan?.legs[0];
  const destination =
    next?.metadata.longitude != null && next?.metadata.latitude != null
      ? data.journey.city_code.startsWith("CN-")
        ? `https://uri.amap.com/navigation?to=${next.metadata.longitude},${next.metadata.latitude},${encodeURIComponent(next.title)}&mode=walk&coordinate=wgs84&callnative=1`
        : `https://www.google.com/maps/dir/?api=1&destination=${next.metadata.latitude},${next.metadata.longitude}`
      : null;
  return (
    <section className="v8-page" data-testid="v8-live-journey">
      <div className="v8-page-intro compact">
        <div>
          <p className="v8-kicker">
            Live Journey ·{" "}
            {offline ? `saved ${date(offline.updated_at)}` : "syncing"}
          </p>
          <h1>Choose your next leg.</h1>
          <p className="v8-lede">
            Current step, next protected moment, leave-by guidance, and one
            clear recovery path.
          </p>
        </div>
        <div className="v9-live-actions">
          <button
            className="v8-outline-button"
            onClick={() => void onLocation()}
          >
            Update location
          </button>
          <button
            className="v8-rain-button"
            aria-label="Rain detected"
            onClick={() => void onRain()}
          >
            Report rain
          </button>
        </div>
      </div>
      <div className="v8-live-grid">
        <div className="v8-live-main">
          <MapPanel data={data} option={selected} />
          <div className="v8-live-now">
            <span className="v8-live-label">
              <span className="status-dot pulse" />
              NOW
            </span>
            <div>
              <h2 data-testid="live-journey-current">
                {now
                  ? now.title
                  : `Awaiting plan${selected?.stay.property_name ? ` · ${selected.stay.property_name}` : ""}`}
              </h2>
              <p>
                {next
                  ? `NEXT · ${next.title} · ${nextLeg?.mode?.toLowerCase() ?? mode.toLowerCase()} · ${nextLeg?.duration_min ?? "duration pending"}${nextLeg ? " min" : ""}`
                  : "NEXT · Select a plan to calculate the next leg"}
              </p>
            </div>
            <strong>
              {now ? date(now.start_at).split(", ").at(-1) : "AWAITING PLAN"}
            </strong>
          </div>
          <div className="v8-mode-chooser">
            <div>
              <span>Mode for next leg</span>
              <b>Choose a calm route</b>
            </div>
            <div className="v8-mode-chips">
              {v8Modes.map((item) => (
                <button
                  data-testid={`mode-${item.toLowerCase()}`}
                  key={item}
                  className={mode === item ? "active" : ""}
                  onClick={() => void onMode(item)}
                >
                  {item.replace("_", " ")}
                </button>
              ))}
            </div>
            <button className="v8-compare-button" onClick={onSheet}>
              Compare all modes
            </button>
          </div>
        </div>
        <aside className="v8-live-side">
          <div className="v8-next-card">
            <span>NEXT · LEAVE BY</span>
            <h3>{next?.title ?? "Awaiting plan"}</h3>
            <p>
              {next
                ? `Arrive by ${date(next.start_at)}`
                : "Select a plan to calculate your route"}{" "}
              · {selected?.protected_margin_min ?? 0} min slack
            </p>
            <div className="v8-eta">
              <strong>
                {next ? date(next.start_at).split(", ").at(-1) : "—"}
              </strong>
              <span>ETA · {nextLeg?.mode ?? mode}</span>
            </div>
            {destination && (
              <a
                className="v9-navigate"
                href={destination}
                target="_blank"
                rel="noreferrer"
              >
                NAVIGATE →
              </a>
            )}
            <div className="v9-risk">
              <b>RISK</b>
              <span>
                {data.active_plan?.disruptions.length
                  ? `${data.active_plan.disruptions[0].severity} · Guardian monitoring`
                  : "LOW · route evidence current"}
              </span>
            </div>
          </div>
          <details className="v8-comparison v9-evidence-drawer">
            <summary className="v9-evidence-summary">
              <span>EVIDENCE</span>
              <small>Provider route, freshness, cost and feasibility</small>
            </summary>
            <div className="v8-aside-heading">
              <span>ROUTE EVIDENCE</span>
              <button onClick={onSheet}>Compare</button>
            </div>
            {comparison.slice(0, 2).map((fact) => (
              <div
                className="v8-route-row"
                key={`${fact.from_key}-${fact.to_key}-${fact.mode}`}
              >
                <b>{fact.mode}</b>
                <span>
                  {fact.duration_min} min · {fact.walking_min} min walk
                </span>
                <strong>
                  {fact.cost_amount_minor == null
                    ? "—"
                    : money(fact.cost_amount_minor, fact.currency ?? "CNY")}
                </strong>
              </div>
            ))}
            <small>Provider facts · unknown costs never become zero</small>
          </details>
        </aside>
      </div>
    </section>
  );
}

function MapPage({
  data,
  selected,
  comparison,
  onSheet,
}: {
  data: V8Data;
  selected: V8Data["options"][number] | null;
  comparison: V8Data["mobility_facts"];
  onSheet: () => void;
}) {
  return (
    <section className="v8-page">
      <div className="v8-page-intro compact">
        <div>
          <p className="v8-kicker">Map · one glance</p>
          <h1>The city, with the plan on top.</h1>
          <p className="v8-lede">
            Captured route geometry and provider facts stay visible while you
            move through the Journey.
          </p>
        </div>
        <button className="v8-primary" onClick={onSheet}>
          Compare modes
        </button>
      </div>
      <div className="v8-map-page-grid">
        <MapPanel data={data} option={selected} />
        <div className="v8-map-facts">
          <span className="v8-kicker">Next leg</span>
          <h2>Tianjin Museum</h2>
          {comparison.slice(0, 3).map((fact) => (
            <div className="v8-route-row" key={fact.mode}>
              <b>{fact.mode}</b>
              <span>
                {fact.duration_min} min · {fact.walking_min} walk
              </span>
              <strong>
                {fact.cost_amount_minor == null
                  ? "—"
                  : money(fact.cost_amount_minor, fact.currency ?? "CNY")}
              </strong>
            </div>
          ))}
          <small>Unknown costs remain unknown.</small>
        </div>
      </div>
    </section>
  );
}

function Bookings({
  selected,
  wallet,
  onImport,
  busy,
}: {
  data: V8Data;
  selected: V8Data["options"][number] | null;
  wallet: Wallet | null;
  onImport: (reservation: Record<string, unknown>) => Promise<void>;
  busy: boolean;
}) {
  const [input, setInput] = useState("");
  const submit = async () => {
    const value = JSON.parse(input) as Record<string, unknown>;
    await onImport(value);
    setInput("");
  };
  return (
    <section className="v8-page" data-testid="v8-bookings">
      <div className="v8-page-intro compact">
        <div>
          <p className="v8-kicker">Journey Inbox · Travel Wallet</p>
          <h1>Your real reservations, protected.</h1>
          <p className="v8-lede">
            Paste structured reservation JSON, review it, then bind confirmed
            facts to the Journey as a durable commitment.
          </p>
        </div>
      </div>
      <div className="v9-wallet-layout">
        <div className="v8-booking-grid">
          <article className="v8-booking-card selected">
            <div className="v8-booking-icon">
              <Icon name="bed" />
            </div>
            <div>
              <span className="v8-selected-label">STAY EVIDENCE</span>
              <h2>{selected?.stay.property_name ?? "No stay selected"}</h2>
              <p>
                {selected?.stay.room_type} ·{" "}
                {selected?.stay.refundable
                  ? "Free cancellation"
                  : "Non-refundable"}
              </p>
              <strong>{money(selected?.stay.total_amount_minor)} total</strong>
            </div>
            <span className="v8-booking-state">Not booked</span>
          </article>
          {wallet?.reservations.map((item) => (
            <article
              className="v8-booking-card"
              key={item.id}
              data-testid="wallet-reservation"
            >
              <div className="v8-booking-icon muted">
                <Icon name="ticket" />
              </div>
              <div>
                <span className="v8-selected-label neutral">
                  {item.type} · {item.realtime_status}
                </span>
                <h2>{item.confirmation_ref}</h2>
                <p>
                  {date(item.scheduled_departure_at)} →{" "}
                  {date(item.scheduled_arrival_at)}
                </p>
                <strong>
                  {item.price.amount_minor == null
                    ? "Price unknown"
                    : money(
                        item.price.amount_minor,
                        item.price.currency ?? "CNY",
                      )}
                </strong>
              </div>
              <span className="v8-booking-state safe">Protected C4</span>
            </article>
          ))}
        </div>
        <aside className="v9-inbox">
          <span className="v8-kicker">IMPORT CONFIRMATION</span>
          <label htmlFor="reservation-json">Reservation JSON</label>
          <textarea
            id="reservation-json"
            value={input}
            onChange={(event) => setInput(event.target.value)}
            placeholder={'{"reservation_type":"RAIL", "confirmation_ref":"…"}'}
          />
          <button
            className="v8-primary"
            disabled={busy || input.trim().length < 2}
            onClick={() => void submit()}
          >
            Review and protect
          </button>
          <small>
            Critical origin, destination, time, provider and reference facts are
            never invented.
          </small>
        </aside>
      </div>
      <div className="v8-no-payment">
        <b>Authority remains explicit</b>
        <span>
          Importing a confirmed reservation protects it. Any payment,
          cancellation or irreversible change still passes the Delegation
          Policy.
        </span>
      </div>
    </section>
  );
}

function OfflineJourneyView({
  value,
  message,
}: {
  value: OfflineJourney;
  message: string | null;
}) {
  return (
    <main className="v9-offline">
      <div className="v8-brand-mark">CN</div>
      <span className="v8-status-pill">OFFLINE · READ ONLY</span>
      <h1>Your next 24 hours are saved.</h1>
      <p>{message}</p>
      {value.snapshot.execution && (
        <div className="v12-offline-now-next">
          <article>
            <span>NOW · {value.snapshot.execution.now_state.replaceAll("_", " ")}</span>
            <b>{value.snapshot.execution.now?.title ?? "Journey complete"}</b>
          </article>
          <article>
            <span>NEXT · {value.snapshot.execution.next_state?.replaceAll("_", " ") ?? "—"}</span>
            <b>{value.snapshot.execution.next?.title ?? "No next step"}</b>
          </article>
        </div>
      )}
      <div>
        {value.snapshot.next_24h.map((item) => (
          <article key={item.id}>
            <b>{item.title}</b>
            <span>
              {date(item.start_at)} → {date(item.end_at)}
            </span>
          </article>
        ))}
      </div>
      <small>
        Provider data last refreshed{" "}
        {value.provider_freshness.latest_provider_capture_at
          ? date(value.provider_freshness.latest_provider_capture_at)
          : "before this snapshot"}
        . Financial actions are disabled offline.
      </small>
    </main>
  );
}

function Me({
  data,
  policy,
  onActivate,
}: {
  data: V8Data;
  policy: Policy | null;
  onActivate: () => Promise<void>;
}) {
  return (
    <section className="v8-page">
      <div className="v8-page-intro compact">
        <div>
          <p className="v8-kicker">Me · authority envelope</p>
          <h1>Your preferences, your boundary.</h1>
          <p className="v8-lede">
            CityNexus makes the scope of delegated autonomy legible before it
            acts.
          </p>
        </div>
      </div>
      <div className="v8-me-grid">
        <article className="v8-me-card">
          <span className="v8-kicker">CURRENT MODE</span>
          <strong>{policy?.mode ?? "ADVISORY"}</strong>
          <p>
            Version {policy?.version ?? "—"}.{" "}
            {policy?.mode === "AUTONOMOUS"
              ? "Reversible transport recovery is allowed."
              : "Actions pause for confirmation."}
          </p>
          <button className="v8-primary" onClick={() => void onActivate()}>
            {policy?.mode === "AUTONOMOUS"
              ? "Envelope enabled"
              : "Enable transport recovery"}
          </button>
        </article>
        <article className="v8-me-card">
          <span className="v8-kicker">PRE-AUTHORIZED</span>
          <ul>
            <li>
              Maximum added cost:{" "}
              {money(policy?.max_auto_replan_cost_delta_minor ?? 5000)}
            </li>
            <li>Maximum loss: {money(policy?.max_auto_loss_minor ?? 0)}</li>
            <li>
              Schedule drift: {policy?.max_auto_schedule_drift_min ?? 20}{" "}
              minutes
            </li>
            <li>Protected: arrival, departure, C3/C4 moments</li>
          </ul>
        </article>
        <article className="v8-me-card">
          <span className="v8-kicker">TRIP CONTEXT</span>
          <strong>
            {data.trip.party_size} travelers ·{" "}
            {data.trip.occupancy.adults ?? data.trip.party_size} adults
          </strong>
          <p>
            Stay budget {money(data.trip.stay_budget.amount_minor)} ·{" "}
            {data.journey.city_code}
          </p>
        </article>
        <PushCapabilityCard travelerId={data.journey.traveler_id} />
      </div>
    </section>
  );
}
