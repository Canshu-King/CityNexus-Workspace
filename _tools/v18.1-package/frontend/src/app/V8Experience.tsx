import { useEffect, useMemo, useState } from "react";
import { Icon } from "../components/v8/Icon";
import { MapPanel } from "../components/v8/MapPanel";
import { AgentComposer } from "../features/agent/AgentComposer";
import { CopilotDock } from "../features/agent/CopilotDock";
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
import { V14RecoveryTruthPanel } from "../features/recovery/V14RecoveryTruthPanel";
import { V12TripStudioPanel } from "../features/studio/V12TripStudioPanel";
import { RealCityDiscoveryPanel } from "../features/discovery/RealCityDiscoveryPanel";
import {
  JourneyTrialSetup,
  localDateTimeInZoneToIso,
  type JourneyTrialDraft,
} from "../features/setup/JourneyTrialSetup";
import type { AgentRuntimeStatus } from "../api/citynexus";
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
import { useT, useLocale } from "../i18n/LocaleContext";
import { formatMinorMoney, majorToMinor } from "../lib/money";
import { withViewTransition } from "../lib/viewTransition";
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

const money = formatMinorMoney;
function date(value?: string, locale = "en-GB") {
  return value
    ? new Intl.DateTimeFormat(locale === "zh-CN" ? "zh-CN" : "en-GB", {
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
        hour12: false,
      }).format(new Date(value))
    : "—";
}

function routeFromPath() {
  return window.location.pathname.replace(/^\/v8\/?/, "") || "hub";
}

const drawerRoutes = [
  ...desktopRoutes,
  ...mobileRoutes.filter(
    (item) => !desktopRoutes.some((entry) => entry.key === item.key),
  ),
];

function greetingFor(hour: number, t: (key: string) => string) {
  if (hour < 5) return t("hub.greeting.night");
  if (hour < 12) return t("hub.greeting.morning");
  if (hour < 18) return t("hub.greeting.afternoon");
  return t("hub.greeting.evening");
}

function cityFromCode(code: string) {
  const segments = code.split("-");
  const raw = (segments.length > 1 ? segments.slice(1).join(" ") : code).replace(
    /_/g,
    " ",
  );
  return raw
    .split(" ")
    .filter(Boolean)
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join(" ");
}

function initialsFrom(name: string) {
  const words = name.split(/\s+/).filter(Boolean);
  const initials =
    words.length > 1
      ? words
          .slice(0, 2)
          .map((word) => word.charAt(0))
          .join("")
      : name.replace(/[^A-Za-z]/g, "").slice(0, 2);
  return (initials || "CN").toUpperCase();
}

// The authoritative current step is current_activity_id; falling back to a
// fixed index would show a stale "next" once the journey has advanced.
function nextActivityOf(plan: V8Data["active_plan"]) {
  if (!plan) return null;
  const index = plan.activities.findIndex(
    (item) => item.id === plan.current_activity_id,
  );
  return plan.activities[index >= 0 ? index + 1 : 1] ?? null;
}

export function V8Experience() {
  const [route, setRoute] = useState(routeFromPath);
  const [data, setData] = useState<V8Data | null>(null);
  const [mode, setMode] = useState<V8Mode>("TRANSIT");
  const [comparison, setComparison] = useState<V8Data["mobility_facts"]>([]);
  const [policy, setPolicy] = useState<Policy | null>(null);
  const [runtimeStatus, setRuntimeStatus] = useState<AgentRuntimeStatus | null>(null);
  const [busy, setBusy] = useState(true);
  const [message, setMessage] = useState<string | null>(null);
  const [sheetOpen, setSheetOpen] = useState(false);
  const [navOpen, setNavOpen] = useState(false);
  const [alertsOpen, setAlertsOpen] = useState(false);
  const [wallet, setWallet] = useState<Wallet | null>(null);
  const [offline, setOffline] = useState<OfflineJourney | null>(null);
  const [decodedArtifactText, setDecodedArtifactText] = useState<string | undefined>();
  const [setupOpen, setSetupOpen] = useState(false);
  const [setupBusy, setSetupBusy] = useState(false);
  const { locale, switchLocale } = useLocale();
  const t = useT();
  const disruptions = useMemo(
    () => data?.active_plan?.disruptions ?? [],
    [data],
  );
  const cityName = useMemo(
    () => (data ? cityFromCode(data.journey.city_code) : ""),
    [data],
  );
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
    const [nextPolicy, nextWallet, nextOffline, nextRuntimeStatus] = await Promise.all([
      v8Request<Policy>(
        `/api/v1/travelers/${experience.journey.traveler_id}/agent-policy`,
      ),
      v8Request<Wallet>(`/api/v1/journeys/${journeyId}/wallet`),
      v8Request<OfflineJourney>(
        `/api/v1/journeys/${journeyId}/offline-snapshot`,
      ),
      v8Request<AgentRuntimeStatus>(`/api/v1/agent/runtime-status`),
    ]);
    setPolicy(nextPolicy);
    setRuntimeStatus(nextRuntimeStatus);
    setWallet(nextWallet);
    setOffline(nextOffline);
    await saveOfflineJourney(nextOffline);
  };

  // Authoritative V12 mutations refetch PlanVersion/JourneyTwin through
  // TanStack Query.  Keep the browser's read-only Dexie cache on the same
  // server snapshot immediately after those mutations as well; it must never
  // become a second, lagging execution source of truth.
  const refreshAuthoritativeTruth = async (journeyId: string) => {
    await Promise.all([authoritativePlans.refetch(), authoritativeTwin.refetch()]);
    const nextOffline = await v8Request<OfflineJourney>(
      `/api/v1/journeys/${journeyId}/offline-snapshot`,
    );
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
                setMessage(t("shell.offlineMsg"));
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
          if (!cancelled) setSetupOpen(true);
          if (!cancelled) setBusy(false);
          return;
        }
        if (!cancelled) setMessage(null);
      } catch (error) {
        const journeyId = localStorage.getItem("citynexus.v8.journey_id");
        const saved = journeyId ? await readOfflineJourney(journeyId) : null;
        if (!cancelled) {
          setOffline(saved);
          setMessage(
            saved
              ? t("shell.offlineMsg")
              : error instanceof Error
                ? error.message
                : t("shell.loadError"),
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

  useEffect(() => {
    const onPopState = () => setRoute(routeFromPath());
    window.addEventListener("popstate", onPopState);
    return () => window.removeEventListener("popstate", onPopState);
  }, []);

  useEffect(() => {
    if (!navOpen && !alertsOpen) return;
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key !== "Escape") return;
      setNavOpen(false);
      setAlertsOpen(false);
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [navOpen, alertsOpen]);

  const selected =
    data?.options.find((item) => item.id === data.selected_option_id) ??
    data?.options[0] ??
    null;
  const navigate = (next: string) => {
    const value = next || "hub";
    withViewTransition(() => {
      window.history.pushState({}, "", `/v8/${value}`);
      setRoute(value);
      setNavOpen(false);
      setAlertsOpen(false);
    });
  };
  const createTianjinDemo = async () => {
    setSetupBusy(true);
    setMessage(null);
    try {
      const traveler = await v8Request<{ id: string }>(
        "/api/v1/travelers",
        {
          method: "POST",
          body: JSON.stringify({
            display_name: "City traveler",
            locale: locale === "zh-CN" ? "zh-CN" : "en-GB",
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
          arrival_anchor: { at: "2026-10-09T18:00:00+08:00", location: "Tianjin West Station" },
          departure_anchor: { at: "2026-10-11T15:00:00+08:00", location: "Tianjin Binhai Airport" },
        }),
      });
      localStorage.setItem("citynexus.v8.journey_id", journey.id);
      await v8Request(`/api/v1/journeys/${journey.id}/stay-options/generate`, { method: "POST" });
      await load(journey.id);
      setSetupOpen(false);
      navigate("discover");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : t("shell.loadError"));
    } finally {
      setSetupBusy(false);
    }
  };
  const createJourney = async (draft: JourneyTrialDraft) => {
    setSetupBusy(true);
    setMessage(null);
    try {
      const cityName = draft.cityName.trim();
      const cityCode = `${draft.countryCode.trim() || "CN"}-${cityName.toUpperCase().replace(/\s+/g, "-")}`;
      const startAt = localDateTimeInZoneToIso(draft.startAt, draft.timezone.trim());
      const endAt = localDateTimeInZoneToIso(draft.endAt, draft.timezone.trim());
      const traveler = await v8Request<{ id: string }>("/api/v1/travelers", {
        method: "POST",
        body: JSON.stringify({
          display_name: "City traveler",
          locale: locale === "zh-CN" ? "zh-CN" : "en-GB",
          timezone: draft.timezone.trim(),
        }),
      });
      const journey = await v8Request<{ id: string }>("/api/v1/journeys", {
        method: "POST",
        body: JSON.stringify({
          traveler_id: traveler.id,
          title: `${cityName} · journey`,
          city_code: cityCode,
          timezone: draft.timezone.trim(),
          start_at: startAt,
          end_at: endAt,
          budget: { amount_minor: majorToMinor(draft.budgetMajor, draft.currency), currency: draft.currency },
          stay_budget: { amount_minor: majorToMinor(draft.stayBudgetMajor, draft.currency), currency: draft.currency },
          party_size: draft.partySize,
          occupancy: { adults: draft.partySize, rooms: draft.rooms },
          arrival_anchor: { at: startAt, location: draft.arrivalLocation.trim() },
          departure_anchor: { at: endAt, location: draft.departureLocation.trim() },
        }),
      });
      localStorage.setItem("citynexus.v8.journey_id", journey.id);
      await v8Request(`/api/v1/journeys/${journey.id}/stay-options/generate`, {
        method: "POST",
        body: JSON.stringify({ query: `${cityName} stay-aware journey` }),
      });
      await load(journey.id);
      setSetupOpen(false);
      navigate("discover");
      setMessage(t("trial.createdLiveHint"));
    } catch (error) {
      setMessage(error instanceof Error ? error.message : t("shell.loadError"));
    } finally {
      setSetupBusy(false);
    }
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
      setMessage(t("shell.staySelected"));
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
          ? t("shell.autopilotRecovered", { mode: result.after_mode.toLowerCase() })
          : t("shell.autopilotPaused", { reasons: result.reason_codes.join(" · ") }),
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
            allowed_activity_types: ["transport", "visit"],
            allowed_booking_types: [],
            protected_commitment_levels: ["C3_Guaranteed", "C4_Anchored"],
            allow_auto_commitment_management: false,
            allow_auto_when_provider_degraded: false,
            allow_auto_on_critical_event: false,
          }),
        },
      );
      setPolicy(next);
      setMessage(t("shell.autonomyEnabled"));
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
          ? t("shell.reservationConfirmed")
          : t("shell.reservationReview"),
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
          t("shell.locationUpdated", { n: Math.round(position.coords.accuracy) }),
        );
      },
      () => setMessage(t("shell.locationDenied")),
      { enableHighAccuracy: true, maximumAge: 30000 },
    );
  };

  if (setupOpen)
    return (
      <JourneyTrialSetup
        onCreate={createJourney}
        onUseTianjinDemo={createTianjinDemo}
        onCancel={data ? () => setSetupOpen(false) : undefined}
        busy={setupBusy}
      />
    );
  if (busy && !data)
    return (
      <div className="v8-loading">
        <div className="v8-brand-mark">CN</div>
        <p>{t("shell.preparing")}</p>
        <span>{t("shell.preparingSub")}</span>
      </div>
    );
  if (!data && offline)
    return <OfflineJourneyView value={offline} message={message} />;
  if (!data)
    return (
      <div className="v8-loading">
        <div className="v8-brand-mark">CN</div>
        <p>{message ?? t("shell.noJourney")}</p>
      </div>
    );

  return (
    <div className="v8-product-shell">
      <aside className="v8-sidebar">
        <div className="v8-brand">
          <div className="v8-brand-mark">CN</div>
          <div>
            <strong>{t("shell.brand")}</strong>
            <span>{t("shell.tagline")}</span>
          </div>
        </div>
        <div className="v8-workspace-label">
          {t("shell.workspace")} <span>{t("shell.workspaceSub")}</span>
        </div>
        <nav className="v8-nav" aria-label="Product navigation">
          {desktopRoutes.map((item, index) => (
            <div key={item.key}>
              {(index === 0 || desktopRoutes[index - 1].group !== item.group) && (
                <span className="v8-nav-group">{item.group}</span>
              )}
              <button
                className={route === item.key ? "active" : ""}
                onClick={() => navigate(item.key)}
              >
                <Icon name={item.icon} />
                <span>{t("nav." + item.key)}</span>
                {item.key === "live" && <i />}
              </button>
            </div>
          ))}
        </nav>
        <div className="v8-sidebar-bottom">
          <div className="v8-sync">
            <span className="status-dot" />
            {t("shell.factsSynced")}<div>{t("shell.plansModes", { plans: data.options.length })}</div>
          </div>
          <button className="v8-user" onClick={() => navigate("me")}>
            <span>{initialsFrom(cityName)}</span>
            <div>
              <b>{cityName}</b>
              <small>{t("shell.travelers", { n: data.trip.party_size })}</small>
            </div>
            <em>•••</em>
          </button>
        </div>
      </aside>
      <main className="v8-main">
        <header className="v8-topbar">
          <button
            className="v8-mobile-menu"
            aria-label={t("shell.openNav")}
            aria-expanded={navOpen}
            aria-controls="v8-nav-drawer"
            onClick={() => setNavOpen(true)}
          >
            {t("shell.menu")}
          </button>
          <div className="v8-breadcrumb">
            <span>{t("shell.journeys")}</span>
            <b>/</b>
            <strong>
              {t("nav." + (route in { hub: 1, studio: 1, stay: 1, discover: 1, live: 1, bookings: 1, intelligence: 1, twin: 1, agent: 1, authoritative: 1, map: 1, me: 1 } ? route : "hub"))}
            </strong>
          </div>
          <div className="v8-top-actions">
            <span className="v8-runtime">
              <span className="status-dot" />
              {policy?.mode === "AUTONOMOUS"
                ? t("shell.autonomyActive")
                : t("shell.factsReady")}
            </span>
            <button
              className="v9-language"
              aria-label="Switch language"
              onClick={switchLocale}
            >
              {t("nav.language")}
            </button>
            <div className="v8-alerts">
              <button
                className="v8-icon-button"
                aria-label={
                  disruptions.length
                    ? t("shell.notifActive", { n: disruptions.length })
                    : t("shell.notifNone")
                }
                aria-expanded={alertsOpen}
                aria-haspopup="dialog"
                onClick={() => setAlertsOpen((open) => !open)}
              >
                ◌
                {disruptions.length > 0 && (
                  <i className="v8-alert-badge">{disruptions.length}</i>
                )}
              </button>
              {alertsOpen && (
                <>
                  <button
                    type="button"
                    className="v8-pop-backdrop"
                    aria-label={t("shell.closeNotif")}
                    onClick={() => setAlertsOpen(false)}
                  />
                  <div
                    className="v8-alert-pop"
                    role="dialog"
                    aria-label={t("shell.notifTitle")}
                  >
                    <span className="v8-kicker">{t("shell.signals")}</span>
                    {disruptions.length ? (
                      disruptions.map((item) => (
                        <article key={item.id}>
                          <b>{item.severity}</b>
                          <span>
                            {item.type.replaceAll("_", " ").toLowerCase()}
                          </span>
                          <small>{date(item.occurred_at, locale)}</small>
                        </article>
                      ))
                    ) : (
                      <p className="v8-muted">
                        {t("shell.noDisruptions")}
                      </p>
                    )}
                  </div>
                </>
              )}
            </div>
            <button className="v8-avatar" onClick={() => navigate("me")}>
              {initialsFrom(cityName)}
            </button>
          </div>
        </header>
        {message && (
          <div className="v8-message" role="status">
            {message}
            <button onClick={() => setMessage(null)}>{t("shell.dismiss")}</button>
          </div>
        )}
        <div className="v8-content">
          {route === "hub" && (
            <Hub data={data} selected={selected} onNavigate={navigate} onNewJourney={() => setSetupOpen(true)} />
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
          {route === "discover" && (
            <RealCityDiscoveryPanel
              journeyId={data.journey.id}
              cityCode={data.journey.city_code}
              onComplete={() => refreshAuthoritativeTruth(data.journey.id)}
              onOpenPlan={() => navigate("authoritative")}
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
                <BookingArtifactScanner onDecoded={setDecodedArtifactText} />
              </div>
              <div className="v8-page">
                <JourneyInboxWorkbench
                  journeyId={data.journey.id}
                  decodedText={decodedArtifactText}
                  onConfirmed={() => load(data.journey.id)}
                />
              </div>
            </>
          )}
          {route === "intelligence" && (
            <ControlTowerPanel policy={policy} runtimeStatus={runtimeStatus} onActivate={activateAutonomy} />
          )}
          {route === "twin" && <TwinPanel data={data} />}
          {route === "authoritative" && (
            <AuthoritativeExecution
              journeyId={data.journey.id}
              plan={authoritativePlan}
              twin={authoritativeTwin.data ?? null}
              policy={policy}
              loading={authoritativePlans.isLoading || authoritativeTwin.isLoading}
              onRefresh={() => void refreshAuthoritativeTruth(data.journey.id)}
            />
          )}
          {route === "agent" && (
            <AgentComposer data={data} busy={busy} onNavigate={navigate} />
          )}
          {route === "me" && (
            <Me data={data} policy={policy} onActivate={activateAutonomy} />
          )}
        </div>
      </main>
      <CopilotDock data={data} onNavigate={navigate} />
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
            <span>{t(({ hub: "mobile.today", agent: "mobile.copilot", bookings: "mobile.wallet" } as Record<string, string>)[item.key] ?? "nav." + item.key)}</span>
          </button>
        ))}
      </nav>
      {navOpen && (
        <>
          <button
            type="button"
            className="v8-drawer-backdrop"
            aria-label={t("shell.closeNav")}
            onClick={() => setNavOpen(false)}
          />
          <nav id="v8-nav-drawer" aria-label="Product navigation">
            <div className="v8-nav-drawer-head">
              <span className="v8-kicker">{t("shell.allRoutes")}</span>
              <button
                type="button"
                className="v8-quiet-button"
                onClick={() => setNavOpen(false)}
              >
                {t("shell.close")}
              </button>
            </div>
            {drawerRoutes.map((item, index) => (
              <div key={item.key}>
                {("group" in item && (index === 0 || !("group" in drawerRoutes[index - 1]) || drawerRoutes[index - 1].group !== item.group)) && (
                  <span className="v8-nav-group">{"group" in item ? item.group : "MORE"}</span>
                )}
                <button
                  className={route === item.key ? "active" : ""}
                  onClick={() => navigate(item.key)}
                >
                  <Icon name={item.icon} />
                  <span>{t("nav." + item.key)}</span>
                </button>
              </div>
            ))}
          </nav>
        </>
      )}
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
  onNewJourney,
}: {
  data: V8Data;
  selected: V8Data["options"][number] | null;
  onNavigate: (route: string) => void;
  onNewJourney: () => void;
}) {
  const t = useT();
  const { locale, switchLocale } = useLocale();
  return (
    <section className="v8-page">
      <div className="v8-page-intro">
        <div>
          <p className="v8-kicker">{greetingFor(new Date().getHours(), t)}</p>
          <h1>{t("hub.title")}</h1>
          <p className="v8-lede">
            {t("hub.lede")}
          </p>
        </div>
        <div className="v8-hub-actions">
          <button className="v9-language v8-home-language" data-testid="home-language" aria-label="Switch language" onClick={switchLocale}>
            {t("nav.language")}
          </button>
          <button className="v8-outline-button" onClick={onNewJourney}>
            {t("trial.newJourney")}
          </button>
          <button className="v8-primary" onClick={() => onNavigate("studio")}>
            <Icon name="spark" />
            {t("hub.openStudio")}
          </button>
        </div>
      </div>
      <div className="v8-hero-grid">
        <article className="v8-trip-hero">
          <div className="v8-trip-hero-head">
            <div>
              <span className="v8-status-pill">
                <span className="status-dot" />
                {t("hub.planningReady")}
              </span>
              <h2>{data.journey.title}</h2>
              <p>
                <Icon name="calendar" />
                {date(data.journey.start_at, locale)} — {date(data.journey.end_at, locale)}{" "}
                <span>·</span> {t("shell.travelers", { n: data.trip.party_size })}
              </p>
            </div>
            <button
              className="v8-quiet-button"
              onClick={() => onNavigate("studio")}
            >
              {t("hub.viewPlan")}
            </button>
          </div>
          <div className="v8-trip-metrics">
            <div>
              <span>{t("hub.stayBudget")}</span>
              <strong>{money(data.trip.stay_budget.amount_minor, data.trip.stay_budget.currency, locale)}</strong>
              <small>{t("hub.verifiedTarget")}</small>
            </div>
            <div>
              <span>{t("hub.protectedMargin")}</span>
              <strong>{selected?.protected_margin_min ?? 0} min</strong>
              <small>{t("hub.detGate")}</small>
            </div>
            <div>
              <span>{t("hub.planHealth")}</span>
              <strong className="green">
                {selected?.hard_constraints_passed ? t("hub.feasible") : t("hub.review")}
              </strong>
              <small>{t("hub.weatherAware")}</small>
            </div>
          </div>
          <div className="v8-anchor-row">
            <div>
              <span>{t("hub.arrival")}</span>
              <b>{date(data.trip.arrival_anchor.at, locale)}</b>
              <small>{data.trip.arrival_anchor.location}</small>
            </div>
            <div className="anchor-line" />
            <div>
              <span>{t("hub.departure")}</span>
              <b>{date(data.trip.departure_anchor.at, locale)}</b>
              <small>{data.trip.departure_anchor.location}</small>
            </div>
          </div>
        </article>
        <MapPanel data={data} option={selected} />
      </div>
      <div className="v8-section-heading">
        <div>
          <p className="v8-kicker">{t("hub.planGlance")}</p>
          <h2>{t("hub.everyDay")}</h2>
        </div>
        <button className="v8-text-button" onClick={() => onNavigate("stay")}>
          {t("hub.compareStays")}
        </button>
      </div>
      <div className="v8-day-row">
        {selected?.days.map((day) => (
          <button
            key={day.day}
            className="v8-day-card"
            onClick={() => onNavigate("studio")}
          >
            <span>{t("hub.day", { n: day.day })}</span>
            <strong>{day.label.split(" · ")[0]}</strong>
            <p>{day.activities.join(" · ")}</p>
            <small>
              <span className="mode-mark">{day.mode}</span>{" "}
              {t("hub.anchor", { type: day.anchor })}
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
  const t = useT();
  const { locale } = useLocale();
  const [draftImpact, setDraftImpact] = useState<{ day: number; count: number } | null>(null);
  return (
    <section className="v8-page" data-testid="v8-trip-studio">
      <div className="v8-page-intro compact">
        <div>
          <p className="v8-kicker">{t("studio.kicker")}</p>
          <h1>{t("studio.title")}</h1>
          <p className="v8-lede">
            {t("studio.lede")}
          </p>
        </div>
        <button className="v8-outline-button" onClick={() => void onRain()}>
          {t("studio.reportRain")}
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
            <b>{t("studio.draftPreview")}</b>
            <span>{t("studio.dayActivities", { day: draftImpact.day, count: draftImpact.count })}</span>
            <small>{t("studio.draftCheck")}</small>
          </div>
        )}
        <aside className="v8-studio-aside">
          <div className="v8-aside-heading">
            <span>{t("studio.selectedStay")}</span>
            <button onClick={() => onNavigate("stay")}>{t("studio.change")}</button>
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
                  {money(selected.stay.total_amount_minor, selected.stay.currency, locale)} <small>{t("studio.total")}</small>
                </strong>
              </div>
            </div>
          )}
          <div className="v8-cost-lines">
            <div>
              <span>{t("studio.stayTotal")}</span>
              <b>{money(selected?.stay_total_minor, selected?.stay.currency ?? data.trip.stay_budget.currency, locale)}</b>
            </div>
            <div>
              <span>{t("studio.dailyMovement")}</span>
              <b>{money(selected?.daily_travel_minor, selected?.stay.currency ?? data.journey.budget.currency, locale)}</b>
            </div>
            <div>
              <span>{t("studio.walkingExposure")}</span>
              <b>{selected?.walking_min} min</b>
            </div>
            <div className="total">
              <span>{t("studio.planHealth")}</span>
              <b className="green">
                {t("studio.protected", { n: selected?.protected_margin_min ?? 0 })}
              </b>
            </div>
          </div>
          <div className="v8-feasibility">
            <span className="status-dot" />
            <div>
              <b>{t("studio.feasibilityPassed")}</b>
              <small>
                {t("studio.feasibilitySub")}
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
  policy,
  loading,
  onRefresh,
}: {
  journeyId: string;
  plan: PlanVersion | null;
  twin: JourneyTwin | null;
  policy: Policy | null;
  loading: boolean;
  onRefresh: () => void;
}) {
  const t = useT();
  const execution = (twin?.context as { execution?: { next_activity_id?: string | null } } | undefined)?.execution;
  return (
    <section className="v8-page" data-testid="v12-authoritative-page">
      <div className="v8-page-intro compact">
        <div>
          <p className="v8-kicker">{t("auth.kicker")}</p>
          <h1>{t("auth.title")}</h1>
          <p className="v8-lede">
            {t("auth.lede")}
          </p>
        </div>
        <button className="v8-outline-button" type="button" onClick={onRefresh}>
          {t("auth.refresh")}
        </button>
      </div>
      {loading && <p className="v8-muted">{t("auth.loading")}</p>}
      {!loading && !plan && (
        <div className="v8-feasibility">
          <span className="status-dot" />
          <div>
            <b>{t("auth.noPlan")}</b>
            <small>{t("auth.noPlanSub")}</small>
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
          <V14RecoveryTruthPanel journeyId={journeyId} policy={policy} currency={data.journey.budget.currency} onAccepted={onRefresh} />
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
  const t = useT();
  const { locale } = useLocale();
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
            {t("live.kicker")}{" "}
            {offline ? t("live.saved", { date: date(offline.updated_at, locale) }) : t("live.syncing")}
          </p>
          <h1>{t("live.title")}</h1>
          <p className="v8-lede">
            {t("live.lede")}
          </p>
        </div>
        <div className="v9-live-actions">
          <button
            className="v8-outline-button"
            onClick={() => void onLocation()}
          >
            {t("live.updateLocation")}
          </button>
          <button
            className="v8-rain-button"
            aria-label="Rain detected"
            onClick={() => void onRain()}
          >
            {t("live.reportRain")}
          </button>
        </div>
      </div>
      <div className="v8-live-grid">
        <div className="v8-live-main">
          <MapPanel data={data} option={selected} />
          <div className="v8-live-now">
            <span className="v8-live-label">
              <span className="status-dot pulse" />
              {t("live.now")}
            </span>
            <div>
              <h2 data-testid="live-journey-current">
                {now
                  ? now.title
                  : `${t("live.awaitingPlan")}${selected?.stay.property_name ? ` · ${selected.stay.property_name}` : ""}`}
              </h2>
              <p>
                {next
                  ? t("live.nextLeg", { title: next.title, mode: nextLeg?.mode?.toLowerCase() ?? mode.toLowerCase(), duration: nextLeg?.duration_min ?? t("live.durationPending"), unit: nextLeg ? " min" : "" })
                  : t("live.nextSelect")}
              </p>
            </div>
            <strong>
              {now ? date(now.start_at, locale).split(", ").at(-1) : t("live.awaitingPlanUpper")}
            </strong>
          </div>
          <div className="v8-mode-chooser">
            <div>
              <span>{t("live.modeForLeg")}</span>
              <b>{t("live.chooseRoute")}</b>
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
              {t("live.compareAll")}
            </button>
          </div>
        </div>
        <aside className="v8-live-side">
          <div className="v8-next-card">
            <span>{t("live.leaveBy")}</span>
            <h3>{next?.title ?? t("live.awaitingPlan")}</h3>
            <p>
              {next
                ? t("live.arriveBy", { date: date(next.start_at, locale) })
                : t("live.selectPlan")}{" "}
              · {selected?.protected_margin_min ?? 0} min slack
            </p>
            <div className="v8-eta">
              <strong>
                {next ? date(next.start_at, locale).split(", ").at(-1) : "—"}
              </strong>
              <span>{t("live.eta", { mode: nextLeg?.mode ?? mode })}</span>
            </div>
            {destination && (
              <a
                className="v9-navigate"
                href={destination}
                target="_blank"
                rel="noreferrer"
              >
                {t("live.navigate")}
              </a>
            )}
            <div className="v9-risk">
              <b>{t("live.risk")}</b>
              <span>
                {data.active_plan?.disruptions.length
                  ? t("live.guardianMonitoring", { severity: data.active_plan.disruptions[0].severity })
                  : t("live.routeCurrent")}
              </span>
            </div>
          </div>
          <details className="v8-comparison v9-evidence-drawer">
            <summary className="v9-evidence-summary">
              <span>{t("live.evidence")}</span>
              <small>{t("live.evidenceSub")}</small>
            </summary>
            <div className="v8-aside-heading">
              <span>{t("live.routeEvidence")}</span>
              <button onClick={onSheet}>{t("live.compare")}</button>
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
                    : money(fact.cost_amount_minor, fact.currency ?? "CNY", locale)}
                </strong>
              </div>
            ))}
            <small>{t("live.providerFacts")}</small>
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
  const t = useT();
  const { locale } = useLocale();
  return (
    <section className="v8-page">
      <div className="v8-page-intro compact">
        <div>
          <p className="v8-kicker">{t("map.kicker")}</p>
          <h1>{t("map.title")}</h1>
          <p className="v8-lede">{t("map.lede")}</p>
        </div>
        <button className="v8-primary" onClick={onSheet}>
          {t("map.compareModes")}
        </button>
      </div>
      <div className="v8-map-page-grid">
        <MapPanel data={data} option={selected} />
        <div className="v8-map-facts">
          <span className="v8-kicker">{t("map.nextLeg")}</span>
          <h2>{nextActivityOf(data.active_plan)?.title ?? t("map.awaitingPlan")}</h2>
          {comparison.slice(0, 3).map((fact) => (
            <div className="v8-route-row" key={fact.mode}>
              <b>{fact.mode}</b>
              <span>
                {fact.duration_min} min · {fact.walking_min} walk
              </span>
              <strong>
                {fact.cost_amount_minor == null
                  ? "—"
                  : money(fact.cost_amount_minor, fact.currency ?? "CNY", locale)}
              </strong>
            </div>
          ))}
          <small>{t("map.unknownCosts")}</small>
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
  const t = useT();
  const { locale } = useLocale();
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
          <p className="v8-kicker">{t("bookings.kicker")}</p>
          <h1>{t("bookings.title")}</h1>
          <p className="v8-lede">{t("bookings.lede")}</p>
        </div>
      </div>
      <div className="v9-wallet-layout">
        <div className="v8-booking-grid">
          <article className="v8-booking-card selected">
            <div className="v8-booking-icon">
              <Icon name="bed" />
            </div>
            <div>
              <span className="v8-selected-label">{t("bookings.stayEvidence")}</span>
              <h2>{selected?.stay.property_name ?? t("bookings.noStay")}</h2>
              <p>
                {selected?.stay.room_type} ·{" "}
                {selected?.stay.refundable
                  ? t("bookings.freeCancel")
                  : t("bookings.nonRefundable")}
              </p>
              <strong>{money(selected?.stay.total_amount_minor, selected?.stay.currency ?? data.journey.budget.currency, locale)} {t("bookings.total")}</strong>
            </div>
            <span className="v8-booking-state">{t("bookings.notBooked")}</span>
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
                  {date(item.scheduled_departure_at, locale)} →{" "}
                  {date(item.scheduled_arrival_at, locale)}
                </p>
                <strong>
                  {item.price.amount_minor == null
                    ? t("bookings.priceUnknown")
                    : money(
                        item.price.amount_minor,
                        item.price.currency ?? "CNY",
                        locale,
                      )}
                </strong>
              </div>
              <span className="v8-booking-state safe">{t("bookings.protectedC4")}</span>
            </article>
          ))}
        </div>
        <aside className="v9-inbox">
          <span className="v8-kicker">{t("bookings.importKicker")}</span>
          <label htmlFor="reservation-json">{t("bookings.reservationJson")}</label>
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
            {t("bookings.reviewProtect")}
          </button>
          <small>{t("bookings.neverInvented")}</small>
        </aside>
      </div>
      <div className="v8-no-payment">
        <b>{t("bookings.authorityExplicit")}</b>
        <span>{t("bookings.authoritySub")}</span>
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
  const t = useT();
  const { locale } = useLocale();
  const stateKey = (s: string) =>
    ({ EN_ROUTE: "exec.state.enRoute", ARRIVED: "exec.state.arrived", IN_PROGRESS: "exec.state.inProgress", ACTIVE: "exec.state.active", COMPLETED: "exec.state.completed", SKIPPED: "exec.state.skipped" } as Record<string, string>)[s] ?? null;
  return (
    <main className="v9-offline">
      <div className="v8-brand-mark">CN</div>
      <span className="v8-status-pill">{t("offline.readOnly")}</span>
      <h1>{t("offline.saved24h")}</h1>
      <p>{message}</p>
      {value.snapshot.execution && (
        <div className="v12-offline-now-next">
          <article>
            <span>{t("exec.now")} · {stateKey(value.snapshot.execution.now_state) ? t(stateKey(value.snapshot.execution.now_state)!) : value.snapshot.execution.now_state.replaceAll("_", " ")}</span>
            <b>{value.snapshot.execution.now?.title ?? t("offline.journeyComplete")}</b>
          </article>
          <article>
            <span>{t("exec.next")} · {value.snapshot.execution.next_state ? (stateKey(value.snapshot.execution.next_state) ? t(stateKey(value.snapshot.execution.next_state)!) : value.snapshot.execution.next_state.replaceAll("_", " ")) : "—"}</span>
            <b>{value.snapshot.execution.next?.title ?? t("offline.noNextStep")}</b>
          </article>
        </div>
      )}
      <div>
        {value.snapshot.next_24h.map((item) => (
          <article key={item.id}>
            <b>{item.title}</b>
            <span>
              {date(item.start_at, locale)} → {date(item.end_at, locale)}
            </span>
          </article>
        ))}
      </div>
      <small>
        {t("offline.providerRefresh", { date: value.provider_freshness.latest_provider_capture_at ? date(value.provider_freshness.latest_provider_capture_at, locale) : t("offline.beforeSnapshot") })}
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
  const t = useT();
  const { locale } = useLocale();
  return (
    <section className="v8-page">
      <div className="v8-page-intro compact">
        <div>
          <p className="v8-kicker">{t("me.kicker")}</p>
          <h1>{t("me.title")}</h1>
          <p className="v8-lede">{t("me.lede")}</p>
        </div>
      </div>
      <div className="v8-me-grid">
        <article className="v8-me-card">
          <span className="v8-kicker">{t("me.currentMode")}</span>
          <strong>{policy?.mode ?? "ADVISORY"}</strong>
          <p>
            {t("me.version", { v: policy?.version ?? "—" })}{" "}
            {policy?.mode === "AUTONOMOUS"
              ? t("me.reversibleAllowed")
              : t("me.pauseConfirm")}
          </p>
          <button className="v8-primary" onClick={() => void onActivate()}>
            {policy?.mode === "AUTONOMOUS"
              ? t("me.envelopeEnabled")
              : t("me.enableTransport")}
          </button>
        </article>
        <article className="v8-me-card">
          <span className="v8-kicker">{t("me.preAuthorized")}</span>
          <ul>
            <li>
              {t("me.maxCost")}{" "}
              {money(policy?.max_auto_replan_cost_delta_minor ?? 5000, data.journey.budget.currency, locale)}
            </li>
            <li>{t("me.maxLoss")} {money(policy?.max_auto_loss_minor ?? 0, data.journey.budget.currency, locale)}</li>
            <li>
              {t("me.scheduleDrift")} {policy?.max_auto_schedule_drift_min ?? 20}{" "}
              {t("me.minutes")}
            </li>
            <li>{t("me.protectedMoments")}</li>
          </ul>
        </article>
        <article className="v8-me-card">
          <span className="v8-kicker">{t("me.tripContext")}</span>
          <strong>
            {t("me.travelersAdults", { travelers: data.trip.party_size, adults: data.trip.occupancy.adults ?? data.trip.party_size })}
          </strong>
          <p>
            {t("hub.stayBudget")} {money(data.trip.stay_budget.amount_minor, data.trip.stay_budget.currency, locale)} ·{" "}
            {data.journey.city_code}
          </p>
        </article>
        <PushCapabilityCard travelerId={data.journey.traveler_id} />
      </div>
    </section>
  );
}
