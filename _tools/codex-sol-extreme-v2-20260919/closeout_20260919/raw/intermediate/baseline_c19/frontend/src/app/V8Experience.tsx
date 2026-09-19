import { useCallback, useEffect, useMemo, useState } from "react";
import { Icon } from "../components/v8/Icon";
import { MapPanel } from "../components/v8/MapPanel";
import { AgentComposer } from "../features/agent/AgentComposer";
import { CopilotDock } from "../features/agent/CopilotDock";
import { PlanWithAiSheet } from "../features/planning/PlanWithAiSheet";
import { TripItinerary } from "../features/trip/TripItinerary";
import { ActivityDetail } from "../features/trip/ActivityDetail";
import { HotelsPanel } from "../features/stay/HotelsPanel";
import { PlanComparison } from "../features/planning/PlanComparison";
import { LiveRecovery } from "../features/execution/LiveRecovery";
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
import { RecoveryRequiredPanel } from "../features/recovery/RecoveryRequiredPanel";
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
import { isDisruptionOpen } from "../lib/disruptionState";
import {
  budgetEvidenceCoverage,
  budgetVerdictAllowed as budgetVerdictAllowedFor,
} from "../lib/budgetEvidence";
import { v8Modes, type RecoveryState, type V8Data, type V8Mode } from "./v8Types";

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

/**
 * Wall-clock helpers that read an ISO instant in the *journey's* time zone.
 *
 * Slicing the raw ISO string (``start_at.slice(11, 16)``) shows UTC wall time
 * for a UTC-offset instant.  A 10:00 Xiamen arrival is stored as
 * ``...T02:00:00+00:00``, so the raw slice rendered "02:00" on Today while the
 * itinerary (which uses Intl with the journey zone) rendered "10:00" — two
 * contradictory readings of the same stop.  Always format instants through the
 * journey time zone.
 */
function clockInZone(value: string, timeZone: string): string {
  try {
    return new Intl.DateTimeFormat("en-GB", {
      timeZone,
      hour: "2-digit",
      minute: "2-digit",
      hourCycle: "h23",
    }).format(new Date(value));
  } catch {
    return value.slice(11, 16);
  }
}

function dateKeyInZone(value: string, timeZone: string): string {
  try {
    return new Intl.DateTimeFormat("en-CA", {
      timeZone,
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
    }).format(new Date(value));
  } catch {
    return value.slice(0, 10);
  }
}

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

/** Same as `date`, but rendered in the journey's time zone, not the device's. */
function dateInZone(value: string | undefined, locale: string, timeZone: string) {
  if (!value) return "—";
  try {
    return new Intl.DateTimeFormat(locale === "zh-CN" ? "zh-CN" : "en-GB", {
      timeZone,
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    }).format(new Date(value));
  } catch {
    return date(value, locale);
  }
}

// Alternate paths people share or type.  A deep link that lands on an unknown
// key used to render an empty content area, so refresh/share produced a blank
// page.  Map the known aliases onto real routes; anything else falls back to
// Today rather than nothing.
//
// An alias must never shadow a route the product itself navigates to.  "stay"
// and "bookings" are real desktop routes, so aliasing them to "trips" made a
// hard refresh silently swap the surface: the traveller opened 住宿选择, then
// reloading showed the Trips workspace instead.
const ROUTE_ALIASES: Record<string, string> = {
  today: "hub",
  copilot: "agent",
  wallet: "trips",
  itinerary: "trips",
  stays: "trips",
  home: "hub",
};

const KNOWN_ROUTES = new Set<string>([
  ...desktopRoutes.map((r) => r.key),
  ...mobileRoutes.map((r) => r.key),
]);

function routeFromPath() {
  const raw = window.location.pathname.replace(/^\/v8\/?/, "").replace(/\/$/, "");
  if (!raw) return "hub";
  const key = raw.split("/")[0].toLowerCase();
  // A real route wins over an alias, otherwise refresh changes the screen.
  if (KNOWN_ROUTES.has(key)) return key;
  const alias = ROUTE_ALIASES[key];
  if (alias) return alias;
  // Never render an empty shell: an unknown path is Today.
  return "hub";
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
  if (plan.current_activity_id == null) return plan.activities[1] ?? null;
  const index = plan.activities.findIndex(
    (item) => item.id === plan.current_activity_id,
  );
  return index >= 0 ? (plan.activities[index + 1] ?? null) : null;
}

function liveActivityWindow(plan: V8Data["active_plan"]) {
  if (!plan) return { now: null, next: null, nextLeg: null };
  const cursor =
    plan.current_activity_id == null
      ? 0
      : plan.activities.findIndex((item) => item.id === plan.current_activity_id);
  if (cursor < 0) {
    // Present-but-unknown is stale/corrupt state.  Fail closed instead of
    // fabricating the first activity as Now.  A null cursor is handled above
    // as the explicitly permitted pre-execution fallback.
    return { now: null, next: null, nextLeg: null };
  }
  return {
    now: plan.activities[cursor] ?? null,
    next: plan.activities[cursor + 1] ?? null,
    nextLeg: plan.legs[cursor] ?? null,
  };
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
  // Event ids whose disruption the traveller has already resolved by accepting
  // a replan.  Read from /replans (which is authoritative for proposal status)
  // as well as from the event status, so the two can never disagree.
  const [handledEventIds, setHandledEventIds] = useState<string[]>([]);
  const [decodedArtifactText, setDecodedArtifactText] = useState<string | undefined>();
  const [setupOpen, setSetupOpen] = useState(false);
  const [planAiOpen, setPlanAiOpen] = useState(false);
  // Reference screen 08: the dedicated activity detail surface.
  const [detailActivityId, setDetailActivityId] = useState<string | null>(null);
  // Backend unreachable is a distinct state from "you have no trip": silently
  // dropping the traveller to the create-trip screen would imply their journey
  // vanished (master mission Phase 10).
  const [unreachable, setUnreachable] = useState(false);
  const [setupBusy, setSetupBusy] = useState(false);
  const { locale, switchLocale } = useLocale();
  const t = useT();
  // "Needs attention" means an event the traveller has NOT already handled.
  // Acknowledgement is deliberately NOT resolution in this product: an
  // ACKNOWLEDGED trigger means the traveller has *seen* the change, not that a
  // recovery was chosen.  Only RESOLVED, IGNORED, or an accepted replan linked
  // to this event closes it (T3 / docs/ACK_RESOLUTION_CONTRACT.md).  Counting a
  // merely-acknowledged event as handled let Today and the notification badge
  // go quiet while the disruption was still unresolved.
  const allDisruptions = useMemo(
    () => data?.active_plan?.disruptions ?? [],
    [data],
  );
  const isHandledDisruption = useCallback(
    (item: V8Data["active_plan"] extends null
      ? never
      : NonNullable<V8Data["active_plan"]>["disruptions"][number]) => {
      const acceptedTriggerIds: Set<string> = new Set(handledEventIds);
      return !isDisruptionOpen(item, acceptedTriggerIds);
    },
    [handledEventIds],
  );
  const disruptions = useMemo(
    () => allDisruptions.filter((item) => !isHandledDisruption(item)),
    [allDisruptions, isHandledDisruption],
  );
  /** Disruptions the traveller has already acted on; explained, not escalated. */
  const handledDisruptions = useMemo(
    () => allDisruptions.filter((item) => isHandledDisruption(item)),
    [allDisruptions, isHandledDisruption],
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
  // Distinct from ``authoritativePlan``: that one falls back to the first plan
  // for display, so it cannot answer "has the traveller actually chosen one?".
  const hasChosenPlan = Boolean(
    authoritativePlans.data?.some(
      (item) => item.status === "ACTIVE" || item.status === "SELECTED",
    ),
  );

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
    // Which disruptions already have an accepted proposal behind them?
    try {
      const replans = await v8Request<Array<{ trigger_event_id?: string | null; status?: string }>>(
        `/api/v1/journeys/${journeyId}/replans`,
      );
      setHandledEventIds(
        (Array.isArray(replans) ? replans : [])
          .filter((item) => String(item?.status ?? "").toUpperCase() === "ACCEPTED")
          .map((item) => String(item?.trigger_event_id ?? ""))
          .filter(Boolean),
      );
    } catch {
      setHandledEventIds([]);
    }
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
            // A network/backend failure is NOT proof the journey is gone.
            // Keep the id and tell the traveller the truth.
            const network = error instanceof TypeError;
            if (network) {
              if (!cancelled) {
                setUnreachable(true);
                setBusy(false);
              }
              return;
            }
            localStorage.removeItem("citynexus.v8.journey_id");
            journeyId = null;
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

  // `selected` is what to preview: the traveller's own choice, or the best
  // candidate so the screens are never empty.  `chosenOption` is what the
  // traveller actually committed to, and is the only thing that may be called
  // "your stay" or counted as spend.
  const selected =
    data?.options.find((item) => item.id === data.selected_option_id) ??
    data?.options[0] ??
    null;
  const chosenOption =
    data?.options.find((item) => item.id === data.selected_option_id) ??
    data?.options.find((item) => item.status === "SELECTED") ??
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
      // The real-city discovery provider materialises places under a latin
      // city code (CN-XIAMEN).  Using the raw Chinese name produced CN-厦门,
      // which matched no places and silently yielded zero candidate plans.
      const cityCode = `${draft.countryCode.trim() || "CN"}-${cityCodeSlug(cityName)}`;
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
      // Land on Today and open the planning entry: the next thing a traveller
      // wants after creating a trip is a plan, not a discovery console.
      navigate("hub");
      setPlanAiOpen(true);
      setMessage(
        locale.startsWith("zh")
          ? "行程已创建。告诉 AI 你想怎么玩，它会生成可选方案。"
          : "Trip created. Tell the AI how you like to travel and it will build candidate plans.",
      );
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

  // Derived for the activity-detail surface (reference 08).
  const allActivities = (data?.active_plan?.activities ?? []) as unknown as Array<{
    id: string;
    title: string;
    place_id?: string | null;
  }>;
  const detailActivity = detailActivityId
    ? allActivities.find((item) => item.id === detailActivityId) ?? null
    : null;
  // Nearby suggestions are other real stops on the same plan that the backend
  // actually returned; nothing is invented.
  const nearbyActivities = detailActivity
    ? allActivities.filter((item) => item.id !== detailActivity.id)
    : [];

  if (unreachable && !data)
    return (
      <section
        className="v8-page"
        data-testid="backend-unreachable"
        role="alert"
        aria-live="assertive"
      >
        <div className="v8-page-intro compact">
          <div>
            <p className="v8-kicker">{locale.startsWith("zh") ? "连接" : "Connection"}</p>
            <h1>{locale.startsWith("zh") ? "连不上服务器" : "Can't reach the server"}</h1>
            <p className="v8-lede">
              {locale.startsWith("zh")
                ? "你的行程数据没有丢失。请检查网络后重试。"
                : "Your trip data has not been lost. Check your connection and try again."}
            </p>
          </div>
        </div>
        <button
          type="button"
          className="v8-primary-button"
          data-testid="backend-unreachable-retry"
          onClick={() => {
            setUnreachable(false);
            setBusy(true);
            window.location.reload();
          }}
        >
          {locale.startsWith("zh") ? "重试" : "Try again"}
        </button>
      </section>
    );

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
                data-contrast-role={route === item.key ? "state" : undefined}
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
              {t("nav." + (route in { hub: 1, trips: 1, studio: 1, stay: 1, discover: 1, live: 1, bookings: 1, intelligence: 1, twin: 1, agent: 1, authoritative: 1, map: 1, me: 1 } ? route : "hub"))}
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
              data-testid="topbar-language"
              data-contrast-role="control"
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
            <>
              {/* Only offer the chooser while no plan is chosen; once chosen,
                  switching lives in Trips so Today stays task-focused. */}
              {!hasChosenPlan && (
                <PlanComparison
                  journeyId={data.journey.id}
                  plans={authoritativePlans.data ?? []}
                  budgetMinor={data.journey.budget.amount_minor}
                  currency={data.journey.budget.currency}
                  onSelected={() => {
                    void load(data.journey.id);
                    void authoritativePlans.refetch();
                    void authoritativeTwin.refetch();
                  }}
                />
              )}
              <Hub
                data={data}
                selected={selected}
                hasChosenPlan={hasChosenPlan}
                isHandledDisruption={isHandledDisruption}
                onNavigate={navigate}
                onNewJourney={() => setSetupOpen(true)}
                onPlanWithAi={() => setPlanAiOpen(true)}
              />
            </>
          )}
          {route === "studio" && (
            <Studio
              data={data}
              selected={selected}
              chosen={chosenOption}
              plan={authoritativePlan}
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
            <div
              className="live-shell"
              data-decision-active={disruptions.length > 0 ? "true" : "false"}
            >
              <Live
                data={data}
                selected={selected}
                mode={mode}
                onRain={triggerRain}
                onLocation={shareForegroundLocation}
                offline={offline}
              />
              <LiveRecovery
                journeyId={data.journey.id}
                handledEventIds={handledEventIds}
                onAccepted={() => void load(data.journey.id)}
              />
              <LiveSecondary
                data={data}
                selected={selected}
                mode={mode}
                comparison={comparison}
                isHandledDisruption={isHandledDisruption}
                onMode={changeMode}
                onSheet={() => setSheetOpen(true)}
                onRain={triggerRain}
                onLocation={shareForegroundLocation}
              />
              <V10LiveExecutionPanel journeyId={data.journey.id} />
            </div>
          )}
          {route === "map" && (
            <MapPage
              data={data}
              selected={selected}
              comparison={comparison}
              onSheet={() => setSheetOpen(true)}
            />
          )}
          {route === "trips" && detailActivity && (
            <ActivityDetail
              activity={detailActivity as never}
              timeZone={data.journey.timezone || "UTC"}
              onBack={() => setDetailActivityId(null)}
              onShowOnMap={() => {
                setDetailActivityId(null);
                navigate("map");
              }}
              onAskCopilot={() => {
                setDetailActivityId(null);
                navigate("agent");
              }}
              nearby={nearbyActivities as never}
              onOpenNearby={(id) => setDetailActivityId(id)}
            />
          )}
          {route === "trips" && !detailActivity && (
            <TripsWorkspace
              data={data}
              selected={selected}
              chosen={chosenOption}
              plan={authoritativePlan}
              wallet={wallet}
              onNavigate={navigate}
              onRain={triggerRain}
              onImport={importReservation}
              busy={busy}
              onOpenCopilot={() => setPlanAiOpen(true)}
              onOpenActivity={setDetailActivityId}
              onRefresh={() => void load(data.journey.id)}
            />
          )}
          {route === "bookings" && (
            <>
              <Bookings
                data={data}
                selected={selected}
                chosen={chosenOption}
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
              recovery={data.recovery}
              flags={data.experience_flags}
              currency={data.journey.budget.currency}
              onRefresh={() => void refreshAuthoritativeTruth(data.journey.id)}
            />
          )}
          {route === "agent" && (
            <AgentComposer data={data} busy={busy} onNavigate={navigate} />
          )}
          {route === "me" && (
            <Me data={data} policy={policy} onActivate={activateAutonomy} wallet={wallet} />
          )}
        </div>
      </main>
      <CopilotDock data={data} onNavigate={navigate} />
      {planAiOpen && (
        <PlanWithAiSheet
          journeyId={data.journey.id}
          cityCode={data.journey.city_code}
          onClose={() => setPlanAiOpen(false)}
          onPlanned={() => void load(data.journey.id)}
        />
      )}
      <nav className="v8-mobile-nav" aria-label="Mobile navigation">
        {mobileRoutes.map((item) => (
          <button
            key={item.key}
            data-testid={`nav-${item.key}`}
            data-contrast-role={
              route === item.key || (item.key === "map" && route === "live")
                ? "state"
                : undefined
            }
            className={
              route === item.key || (item.key === "map" && route === "live")
                ? "active"
                : ""
            }
            onClick={() => navigate(item.key)}
          >
            <Icon name={item.icon} />
            <span>{t(({ hub: "mobile.today", trips: "mobile.trips", agent: "mobile.copilot", bookings: "mobile.wallet" } as Record<string, string>)[item.key] ?? "nav." + item.key)}</span>
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
                {("group" in item && (index === 0 || !("group" in drawerRoutes[index - 1]) || (drawerRoutes[index - 1] as { group?: string }).group !== item.group)) && (
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


/**
 * Trips workspace.
 *
 * The previous version stacked itinerary + studio + booking JSON + authority
 * text into one long page.  Travellers answer different questions here, so the
 * screen is split into sub-tabs and the default tab is useful within one
 * phone screen.
 */
function TripsWorkspace({
  data,
  selected,
  chosen,
  plan,
  wallet,
  onNavigate,
  onRain,
  onImport,
  busy,
  onOpenCopilot,
  onOpenActivity,
  onRefresh,
}: {
  data: V8Data;
  selected: V8Data["options"][number] | null;
  chosen: V8Data["options"][number] | null;
  plan: PlanVersion | null;
  wallet: Wallet | null;
  onNavigate: (route: string) => void;
  onRain: () => Promise<void>;
  onImport: (reservation: Record<string, unknown>) => Promise<void>;
  busy: boolean;
  onOpenCopilot: () => void;
  onOpenActivity: (activityId: string) => void;
  onRefresh: () => void;
}) {
  const { locale } = useLocale();
  const zh = locale.startsWith("zh");
  const [tab, setTab] = useState<"itinerary" | "stay" | "bookings" | "spend">("itinerary");
  const tabs = [
    { key: "itinerary" as const, zh: "行程", en: "Itinerary" },
    { key: "stay" as const, zh: "住宿", en: "Stay" },
    { key: "bookings" as const, zh: "预订", en: "Bookings" },
    { key: "spend" as const, zh: "花费", en: "Spend" },
  ];
  const activityCount = data.active_plan?.activities.length ?? 0;
  // Only a *chosen* stay is a committed cost.  Summing every candidate option
  // would invent a spend the traveller never agreed to.
  const chosenStayOption = chosen;
  const chosenStayPriceKnown = Boolean(
    chosenStayOption &&
      ((chosenStayOption.stay?.nightly_amount_minor ?? 0) > 0 ||
        (chosenStayOption.stay_total_minor ?? 0) > 0),
  );
  const chosenStayTotalMinor = chosenStayPriceKnown
    ? chosenStayOption!.stay_total_minor
    : null;
  return (
    <>
      <nav className="trips-tabs" data-testid="trips-tabs" aria-label={zh ? "行程分区" : "Trip sections"}>
        {tabs.map((item) => (
          <button
            key={item.key}
            type="button"
            className={tab === item.key ? "active" : ""}
            data-testid={`trips-tab-${item.key}`}
            onClick={() => setTab(item.key)}
          >
            {zh ? item.zh : item.en}
          </button>
        ))}
      </nav>

      {tab === "itinerary" && (
        <TripItinerary
          data={data}
          onOpenCopilot={onOpenCopilot}
          onOpenActivity={onOpenActivity}
        />
      )}
      {tab === "stay" && (
        <HotelsPanel journeyId={data.journey.id} onSelected={onRefresh} />
      )}
      {tab === "bookings" && (
        <>
          {/* Consumer flow first: paste a confirmation or enter it manually,
              review the parsed fields, then confirm.  The raw-JSON workbench is
              kept for developers behind an Advanced disclosure. */}
          <JourneyInboxWorkbench
            journeyId={data.journey.id}
            onConfirmed={async () => { onRefresh(); }}
          />
          <details className="trips-advanced">
            <summary>{zh ? "高级 / 开发者" : "Advanced / developer"}</summary>
            <Bookings
              data={data}
              selected={selected}
              chosen={chosen}
              wallet={wallet}
              onImport={onImport}
              busy={busy}
            />
          </details>
        </>
      )}
      {tab === "spend" && (
        <section className="v8-page" data-testid="trips-spend">
          <div className="v8-page-intro compact">
            <div>
              <p className="v8-kicker">{zh ? "花费" : "Spend"}</p>
              <h1>{zh ? "这趟旅行花多少" : "What this trip costs"}</h1>
              <p className="v8-lede">
                {zh
                  ? `预算 ${data.journey.budget.currency} ${Math.round(data.journey.budget.amount_minor / 100)}；当前方案 ${activityCount} 个活动。`
                  : `Budget ${data.journey.budget.currency} ${Math.round(data.journey.budget.amount_minor / 100)}; the active plan has ${activityCount} stops.`}
              </p>
            </div>
          </div>
          <dl className="trial-review">
            <div>
              <dt>{zh ? "总预算" : "Total budget"}</dt>
              <dd>{data.journey.budget.currency} {Math.round(data.journey.budget.amount_minor / 100)}</dd>
            </div>
            <div>
              <dt>{zh ? "住宿合计（已选）" : "Stay total (selected)"}</dt>
              <dd data-testid="spend-stay-total">
                {!chosenStayOption
                  ? zh
                    ? "还没有选定住宿"
                    : "No stay chosen yet"
                  : chosenStayTotalMinor == null
                    ? zh
                      ? "价格未知（供应商未提供房价）"
                      : "Price unknown (no provider rate)"
                    : `${chosenStayOption.stay.currency} ${Math.round(chosenStayTotalMinor / 100)}`}
              </dd>
            </div>
            <div>
              <dt>{zh ? "活动数量" : "Stops"}</dt>
              <dd>{activityCount}</dd>
            </div>
          </dl>
          <Studio
            data={data}
            selected={selected}
            chosen={chosen}
            plan={plan}
            onNavigate={onNavigate}
            onRain={onRain}
          />
        </section>
      )}
    </>
  );
}

/**
 * A truthful, deliberately approximate budget sanity signal.
 *
 * It never claims an exact trip cost.  It only divides the traveller's own
 * declared budget by the trip length and party size and says whether that
 * leaves a workable daily allowance once lodging, transport and food are
 * considered.
 */
const BUDGET_DAILY_FLOOR_MINOR = 15_000; // CNY 150 per person per day

function budgetAdvisory(
  budgetMinor: number,
  days: number,
  people: number,
  zh: boolean,
): { tight: boolean; perDay: number; perPersonPerDay: number; text: string; hint: string } | null {
  if (!Number.isFinite(budgetMinor) || budgetMinor <= 0) return null;
  const safeDays = Math.max(1, days);
  const safePeople = Math.max(1, people);
  const perDay = Math.round(budgetMinor / safeDays);
  const perPersonPerDay = Math.round(perDay / safePeople);
  const tight = perPersonPerDay < BUDGET_DAILY_FLOOR_MINOR;
  const fmt = (minor: number) => `${Math.round(minor / 100).toLocaleString("zh-CN")}`;
  return {
    tight,
    perDay,
    perPersonPerDay,
    text: zh
      ? `${safeDays} 天 · ${safePeople} 人 · 每人每天约 ¥${fmt(perPersonPerDay)}`
      : `${safeDays} days · ${safePeople} people · about ¥${fmt(perPersonPerDay)} per person per day`,
    hint: tight
      ? zh
        ? "按这个预算，住宿、交通和吃饭很可能超出计划。可以先调整预算，或你确认继续也可以。"
        : "At this budget, lodging, transport and food are likely to exceed the plan. Adjust the budget, or continue intentionally."
      : zh
        ? "这是按你的预算平均下来的参考值，不是最终花费；真实价格以供应商为准。"
        : "This is your own budget averaged out, not a final cost. Real prices come from providers.",
  };
}

function Hub({
  data,
  selected,
  hasChosenPlan,
  isHandledDisruption,
  onNavigate,
  onNewJourney,
  onPlanWithAi,
}: {
  data: V8Data;
  selected: V8Data["options"][number] | null;
  /** True only when the traveller actually adopted a plan. */
  hasChosenPlan: boolean;
  /** Whether a disruption has already been dealt with (accepted replan). */
  isHandledDisruption: (item: NonNullable<V8Data["active_plan"]>["disruptions"][number]) => boolean;
  onNavigate: (route: string) => void;
  onNewJourney: () => void;
  onPlanWithAi: () => void;
}) {
  const t = useT();
  const { locale, switchLocale } = useLocale();
  const zh = locale.startsWith("zh");
  // The traveller may intentionally proceed after seeing a tight-budget warning.
  const [advisoryDismissed, setAdvisoryDismissed] = useState(false);

  // The journey carries a city code (CN-XIAMEN); derive a traveller-facing name
  // from it rather than showing the raw code.
  const cityLabel = (() => {
    const code = String(data.journey.city_code || "");
    const tail = code.includes("-") ? code.split("-").slice(1).join("-") : code;
    if (!tail) return "";
    const cleaned = tail.replaceAll("_", " ");
    // The product creates latin slugs (CN-XIAMEN).  A Chinese traveller must
    // read the city name in Chinese, not a romanised code, so map the known
    // slugs back to their local name.
    const localName = CITY_NAME_BY_SLUG[cleaned.toUpperCase()];
    if (localName) return locale.startsWith("zh") ? localName.zh : localName.en;
    if (/[一-鿿]/.test(cleaned)) return cleaned;
    return cleaned
      .toLowerCase()
      .split(/\s+/)
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(" ");
  })();

  const startMs = Date.parse(data.journey.start_at);
  const endMs = Date.parse(data.journey.end_at);
  const tripDayCount =
    Number.isFinite(startMs) && Number.isFinite(endMs)
      ? Math.max(1, Math.round((endMs - startMs) / 86_400_000) + 1)
      : 1;
  const activities = (data.active_plan?.activities ?? []) as unknown as Array<{
    id: string;
    title: string;
    start_at: string;
    end_at: string;
    type?: string | null;
  }>;
  const advisory = budgetAdvisory(
    Number(data.journey.budget?.amount_minor ?? 0),
    tripDayCount,
    Math.max(1, Number(data.trip.party_size ?? 1)),
    zh,
  );
  const nowMs = Date.now();
  const nextStop =
    activities.find((item) => Date.parse(item.end_at) >= nowMs) ?? activities[0] ?? null;
  // "Today" is a calendar day in the city the traveller is in, not on the
  // device that happens to be open — and the clock must be the city's clock.
  const journeyTz = data.journey.timezone || "UTC";
  const todayKey = dateKeyInZone(new Date().toISOString(), journeyTz);
  const todayStops = activities.filter(
    (item) => dateKeyInZone(item.start_at, journeyTz) === todayKey,
  );
  const chosenStay = data.options.find((option) => option.status === "SELECTED") ?? null;
  const planDisruptions = data.active_plan?.disruptions ?? [];
  // A handled event is history, not an open problem.  An ACKNOWLEDGED trigger
  // stays in the plan payload (acknowledgement is not resolution), so it must
  // not keep Today in a permanent "needs attention" state.
  const disruptions = planDisruptions.filter((item) => !isHandledDisruption(item));
  const handledDisruptions = planDisruptions.filter((item) => isHandledDisruption(item));
  // Single-focus hero: "Now" only when something is genuinely in progress, and
  // "Next" as the one upcoming action. No empty current slot is ever fabricated.
  const currentStop =
    activities.find(
      (item) => Date.parse(item.start_at) <= nowMs && Date.parse(item.end_at) >= nowMs,
    ) ?? null;
  const nextUp = currentStop
    ? activities.find((item) => Date.parse(item.start_at) > Date.parse(currentStop.end_at)) ?? null
    : nextStop;
  const heroClock = nextUp ? clockInZone(nextUp.start_at, journeyTz) : null;

  return (
    <section className="v8-page">
      <div className="v8-page-intro">
        <div>
          <p className="v8-kicker">{greetingFor(new Date().getHours(), t)}</p>
          {/* Today answers the traveller's four questions within one viewport:
              where am I going, when, what is next, and what needs attention. */}
          <h1 data-testid="today-heading">
            {cityLabel
              ? zh
                ? `${cityLabel}之旅`
                : `Trip to ${cityLabel}`
              : data.journey.title}
          </h1>
          {advisory && !advisoryDismissed && (
            <div
              className={`today-advisory${advisory.tight ? " tight" : ""}`}
              data-testid="budget-advisory"
              data-tight={advisory.tight ? "true" : "false"}
            >
              <strong>{advisory.text}</strong>
              <span>{advisory.hint}</span>
              {advisory.tight && (
                <div className="today-advisory-actions">
                  <button
                    type="button"
                    className="v8-outline-button"
                    data-testid="budget-advisory-edit"
                    onClick={onNewJourney}
                  >
                    {zh ? "调整预算" : "Adjust budget"}
                  </button>
                  <button
                    type="button"
                    className="v8-quiet-button"
                    data-testid="budget-advisory-continue"
                    onClick={() => setAdvisoryDismissed(true)}
                  >
                    {zh ? "我知道了，继续" : "Got it, continue"}
                  </button>
                </div>
              )}
            </div>
          )}
          <p className="v8-lede" data-testid="today-when">
            {dateInZone(data.journey.start_at, locale, journeyTz)} — {dateInZone(data.journey.end_at, locale, journeyTz)}
            {" · "}
            {t("shell.travelers", { n: data.trip.party_size })}
            {" · "}
            {zh ? `${tripDayCount} 天` : `${tripDayCount} days`}
          </p>
        </div>
        {/* Pass-8 ruling #1/#2: with an active journey the hero's
            "查看实时行程" is the ONLY primary action on this screen. These are
            path-switching and authoring utilities, so they read as one line of
            quiet text links below the summary instead of four stacked
            full-width buttons competing with the hero. The duplicated language
            toggle is gone — the topbar already owns that control. */}
        <div className="v8-hub-actions" data-testid="hub-secondary-actions">
          <button type="button" className="v8-quiet-button" data-testid="hub-plan-with-ai" onClick={onPlanWithAi}>
            {locale.startsWith("zh") ? "AI 帮我规划" : "Plan my trip with AI"}
          </button>
          <button type="button" className="v8-quiet-button" onClick={onNewJourney}>
            {t("trial.newJourney")}
          </button>
          <button type="button" className="v8-quiet-button" onClick={() => onNavigate("studio")}>
            {t("hub.openStudio")}
          </button>
        </div>
      </div>
      <div className="v8-hero-grid">
        <article
          className="v8-trip-hero cn-now-next-hero"
          data-testid="today-hero"
          data-now={currentStop ? "true" : "false"}
        >
          {currentStop ? (
            <div className="cn-hero-now" data-testid="today-now">
              <span className="cn-hero-label">{zh ? "现在" : "Now"}</span>
              <strong className="cn-hero-now-place">{currentStop.title}</strong>
            </div>
          ) : null}
          <div className="cn-hero-next" data-testid="today-next">
            <span className="cn-hero-label">
              {nextUp ? (zh ? "接下来" : "Next") : zh ? "今天" : "Today"}
            </span>
            <strong className="cn-hero-next-row">
              {nextUp
                ? `${heroClock ?? ""} ${nextUp.title}`.trim()
                : zh
                  ? "还没有安排"
                  : "Nothing scheduled"}
            </strong>
            {nextUp ? (
              <small className="cn-hero-meta">
                {todayStops.length
                  ? zh
                    ? `今天还有 ${todayStops.length} 项安排`
                    : `${todayStops.length} stops today`
                  : zh
                    ? "下一站之后暂无安排"
                    : "Nothing scheduled after this"}
              </small>
            ) : null}
          </div>
          {nextUp ? (
            <button
              type="button"
              className="v8-primary cn-hero-cta"
              data-testid="today-hero-cta"
              data-contrast-role="control"
              onClick={() => onNavigate("live")}
            >
              {zh ? "查看实时行程" : "Open Live"}
            </button>
          ) : null}
        </article>
        <MapPanel data={data} option={selected} />
      </div>
      {/* Stay / booking steps OUT of the hero into a compact strip: the hero owns
          one action, lodging is secondary context (GPT Hero rules). */}
      <div className="cn-hero-strip" data-testid="today-strip">
        <div className="cn-strip-item">
          <span>{zh ? "住宿" : "Stay"}</span>
          <strong data-testid="today-stay">
            {chosenStay
              ? chosenStay.stay.property_name
              : zh
                ? "还没有选定"
                : "Not chosen yet"}
          </strong>
        </div>
        <div className="cn-strip-item">
          <span>{t("hub.arrival")}</span>
          <b>{dateInZone(data.trip.arrival_anchor.at, locale, journeyTz)}</b>
        </div>
        <div className="cn-strip-item">
          <span>{t("hub.departure")}</span>
          <b>{dateInZone(data.trip.departure_anchor.at, locale, journeyTz)}</b>
        </div>
      </div>
      {/* Attention is its own band, not a tile squeezed beside "Next"/"Stay":
          Apple hierarchy says a change that needs the traveller is the loudest
          thing after Now/Next, and an all-clear is a quiet line, not a card.
          The `today-attention` element is always rendered (same logic and
          strings as before); only its presentation escalates via data-attention. */}
      <section
        className="cn-attention-band"
        data-testid="today-attention-band"
        data-attention={
          disruptions.length ? "open" : handledDisruptions.length ? "handled" : "clear"
        }
        aria-label={zh ? "需要关注" : "Needs attention"}
      >
        <div className="cn-attention-head">
          <span className="v8-kicker">{zh ? "需要关注" : "Attention"}</span>
          <strong
            className={disruptions.length ? "warn" : "green"}
            data-testid="today-attention"
          >
            {disruptions.length
              ? zh
                ? `${disruptions.length} 项变化`
                : `${disruptions.length} change(s)`
              : handledDisruptions.length
                ? zh
                  ? "已处理"
                  : "Handled"
                : zh
                  ? "一切正常"
                  : "All clear"}
          </strong>
        </div>
        {disruptions.length > 0 || handledDisruptions.length > 0 ? (
          <p className="cn-attention-hint">
            {disruptions.length
              ? zh
                ? "打开「实时行程」查看并处理这些变化。"
                : "Open Live to review these changes."
              : zh
                ? "刚才的变化已经处理好。"
                : "The earlier change has been handled."}
          </p>
        ) : null}
        {disruptions.length > 0 && (
          <button
            type="button"
            className="v8-primary cn-attention-cta"
            onClick={() => onNavigate("live")}
          >
            {zh ? "查看实时行程" : "Review in Live"}
          </button>
        )}
      </section>
      <div className="v8-section-heading">
        <div>
          <p className="v8-kicker">{t("hub.planGlance")}</p>
          <h2>{t("hub.everyDay")}</h2>
        </div>
        <button className="v8-text-button" onClick={() => onNavigate("stay")}>
          {t("hub.compareStays")}
        </button>
      </div>
      {/* The day cards belong to a stay *option*, not to a chosen plan.  Until
          the traveller has actually chosen a plan they are a preview of one
          candidate stay, so they must say so — otherwise an option's day plan
          reads as the trip the traveller is on. */}
      {!hasChosenPlan && selected && (
        <p className="v8-muted" data-testid="hub-glance-caveat">
          {zh
            ? `以下只是其中一个候选方案的预览，你还没有采用它。`
            : `Preview of one candidate option — you have not chosen a plan yet.`}
        </p>
      )}
      {!selected && (
        <div className="v8-empty-state" data-testid="hub-glance-empty">
          <b>{zh ? "还没有可以预览的行程" : "Nothing to preview yet"}</b>
          <p>
            {zh
              ? "选定方案后，这里会显示每天的安排。"
              : "Choose a plan and the day-by-day plan appears here."}
          </p>
        </div>
      )}
      <div className="v8-day-row">
        {selected?.days.map((day) => (
          <button
            key={day.day}
            className="v8-day-card"
            onClick={() => onNavigate(hasChosenPlan ? "studio" : "hub")}
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

/** A chosen stay with no provider rate must not print as 0.00. */
function stayTotalLabel(
  option: NonNullable<V8Data["options"][number]>,
  t: (key: string, params?: Record<string, string | number>) => string,
  locale: string,
): string {
  const known =
    (option.stay.nightly_amount_minor ?? 0) > 0 || (option.stay_total_minor ?? 0) > 0;
  if (!known) return t("studio.priceUnknown");
  return money(option.stay.total_amount_minor, option.stay.currency, locale);
}

function Studio({
  data,
  selected,
  chosen,
  plan,
  onNavigate,
  onRain,
}: {
  data: V8Data;
  /**
   * The option being previewed.  `selected` falls back to the first candidate
   * when the traveller has not chosen anything yet, so it is a *preview* and
   * must never be presented as the trip the traveller is on.
   */
  selected: V8Data["options"][number] | null;
  /** The option the traveller actually committed to, or null. */
  chosen: V8Data["options"][number] | null;
  /** The authoritative plan, whose activities carry the cost evidence. */
  plan: PlanVersion | null;
  onNavigate: (route: string) => void;
  onRain: () => Promise<void>;
}) {
  const t = useT();
  const { locale } = useLocale();
  const [draftImpact, setDraftImpact] = useState<{ day: number; count: number } | null>(null);
  // How much of the budget is actually evidenced?  A single priced stop does
  // not verify a total, and a stop with no provider price is not a free stop.
  // The evidence lives on the authoritative plan's activities (`cost_status`),
  // not on the /experience projection, so it is read from `plan`
  // (T4 / docs/BUDGET_EVIDENCE_CONTRACT.md).
  const planActivities = plan?.activities ?? [];
  const costEvidence = budgetEvidenceCoverage(planActivities);
  const pricedStops = costEvidence.knownCount;
  const budgetVerdictAllowed = budgetVerdictAllowedFor(costEvidence);
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
          {!chosen && selected && (
            <p className="v8-muted" data-testid="studio-preview-caveat">
              {locale.startsWith("zh")
                ? "以下只是候选方案的预览，你还没有采用它。"
                : "This is a preview of a candidate option - you have not chosen a plan yet."}
            </p>
          )}
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
            <span>{chosen ? t("studio.selectedStay") : t("studio.noStaySelected")}</span>
            <button onClick={() => onNavigate("stay")}>
              {chosen ? t("studio.change") : t("studio.chooseStay")}
            </button>
          </div>
          {chosen && (
            <div className="v8-selected-stay">
              <div className="v8-hotel-thumb">
                <Icon name="bed" />
              </div>
              <div>
                <b>{chosen.stay.property_name}</b>
                <span>{chosen.stay.room_type}</span>
                <strong>
                  {stayTotalLabel(chosen, t, locale)}{" "}
                  <small>{t("studio.total")}</small>
                </strong>
              </div>
            </div>
          )}
          <div className="v8-cost-lines">
            <div>
              <span>{t("studio.stayTotal")}</span>
              {/* A total is only known once a stay is chosen, and OSM carries
                  no price: unknown must read as unknown, never as ¥0.00. */}
              <b data-testid="studio-stay-total">
                {!chosen
                  ? t("studio.notChosen")
                  : (chosen.stay.nightly_amount_minor ?? 0) > 0 ||
                      (chosen.stay_total_minor ?? 0) > 0
                    ? money(chosen.stay_total_minor, chosen.stay.currency ?? data.trip.stay_budget.currency, locale)
                    : t("studio.priceUnknown")}
              </b>
            </div>
            <div>
              <span>{t("studio.dailyMovement")}</span>
              <b>
                {chosen
                  ? money(chosen.daily_travel_minor, chosen.stay.currency ?? data.journey.budget.currency, locale)
                  : t("studio.notChosen")}
              </b>
            </div>
            <div>
              <span>{t("studio.walkingExposure")}</span>
              <b>{chosen ? `${chosen.walking_min} min` : t("studio.notChosen")}</b>
            </div>
            <div className="total">
              <span>{t("studio.planHealth")}</span>
              <b className={data.active_plan ? "green" : ""}>
                {data.active_plan
                  ? t("studio.protected", { n: chosen?.protected_margin_min ?? 0 })
                  : t("studio.notChosen")}
              </b>
            </div>
          </div>
          {/* The plan gate has nothing to validate before a plan exists, and
              it cannot verify a budget it has no prices for: a stop with no
              provider price is not a free stop.  Claiming "budget verified"
              over an all-unknown itinerary is a fabricated fact, and one known
              price beside many unknown ones is only partial evidence — never a
              total (T4 / docs/BUDGET_EVIDENCE_CONTRACT.md). */}
          {data.active_plan ? (
            <div className="v8-feasibility" data-testid="studio-feasibility">
              <span className="status-dot" />
              <div>
                <b>
                  {budgetVerdictAllowed
                    ? t("studio.feasibilityPassed")
                    : t("studio.feasibilityPassedPartial")}
                </b>
                <small>
                  {budgetVerdictAllowed
                    ? t("studio.feasibilitySub")
                    : costEvidence.state === "PARTIAL"
                      ? t("studio.feasibilityPartialSub", {
                          n: costEvidence.unverifiedCount,
                        })
                      : t("studio.feasibilityNoPrice")}
                </small>
              </div>
            </div>
          ) : (
            <div className="v8-feasibility pending" data-testid="studio-no-plan">
              <span className="status-dot" />
              <div>
                <b>{t("studio.noPlanChecked")}</b>
                <small>{t("studio.noPlanCheckedSub")}</small>
              </div>
            </div>
          )}
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
  recovery,
  flags,
  currency,
  onRefresh,
}: {
  journeyId: string;
  plan: PlanVersion | null;
  twin: JourneyTwin | null;
  policy: Policy | null;
  loading: boolean;
  recovery?: RecoveryState | null;
  flags?: V8Data["experience_flags"];
  currency: string;
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
      {/* Durable mid-trip HARD recovery / stale-evidence condition.  Rendered
          before the plan so an invalidated plan can never look healthy. */}
      <RecoveryRequiredPanel
        journeyId={journeyId}
        recovery={recovery}
        flags={flags}
        onRefresh={onRefresh}
      />
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
          <V14RecoveryTruthPanel journeyId={journeyId} policy={policy} currency={currency} onAccepted={onRefresh} />
        </>
      )}
    </section>
  );
}

function Live({
  data,
  selected,
  mode,
  onRain,
  onLocation,
  offline,
}: {
  data: V8Data;
  selected: V8Data["options"][number] | null;
  mode: V8Mode;
  onRain: () => Promise<void>;
  onLocation: () => Promise<void>;
  offline: OfflineJourney | null;
}) {
  const t = useT();
  const { locale } = useLocale();
  const { now, next, nextLeg } = liveActivityWindow(data.active_plan);
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
      </div>
      <div className="v8-live-main">
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
            {now ? clockInZone(now.start_at, data.journey.timezone || "UTC") : t("live.awaitingPlanUpper")}
          </strong>
        </div>
        <MapPanel data={data} option={selected} />
      </div>
    </section>
  );
}

function LiveSecondary({
  data,
  selected,
  mode,
  comparison,
  isHandledDisruption,
  onMode,
  onSheet,
  onRain,
  onLocation,
}: {
  data: V8Data;
  selected: V8Data["options"][number] | null;
  mode: V8Mode;
  comparison: V8Data["mobility_facts"];
  isHandledDisruption: (item: NonNullable<V8Data["active_plan"]>["disruptions"][number]) => boolean;
  onMode: (mode: V8Mode) => Promise<void>;
  onSheet: () => void;
  onRain: () => Promise<void>;
  onLocation: () => Promise<void>;
}) {
  const t = useT();
  const { locale } = useLocale();
  const zh = locale.startsWith("zh");
  const { next, nextLeg } = liveActivityWindow(data.active_plan);
  const planDisruptions = data.active_plan?.disruptions ?? [];
  const disruptions = planDisruptions.filter((item) => !isHandledDisruption(item));
  const destination =
    next?.metadata.longitude != null && next?.metadata.latitude != null
      ? data.journey.city_code.startsWith("CN-")
        ? `https://uri.amap.com/navigation?to=${next.metadata.longitude},${next.metadata.latitude},${encodeURIComponent(next.title)}&mode=walk&coordinate=wgs84&callnative=1`
        : `https://www.google.com/maps/dir/?api=1&destination=${next.metadata.latitude},${next.metadata.longitude}`
      : null;
  return (
    <section className="v8-page" data-testid="v8-live-secondary">
      {/* Pass-8 ruling #3: Live reads Current -> Map -> Disruption/Replan ->
          these utilities -> mode/evidence. They are location and weather
          reporting, not decisions, so they no longer sit above "Current" as two
          full-width buttons of equal visual weight. */}
      <div className="cn-live-toolbar" data-testid="live-toolbar-actions">
        <button
          type="button"
          className="v8-quiet-button"
          data-testid="live-update-location"
          onClick={() => void onLocation()}
        >
          {t("live.updateLocation")}
        </button>
        <button
          type="button"
          className="v8-quiet-button"
          data-testid="live-report-rain"
          aria-label="Rain detected"
          onClick={() => void onRain()}
        >
          {t("live.reportRain")}
        </button>
      </div>
      <div className="cn-live-secondary">
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
                data-contrast-role={mode === item ? "state" : "control"}
                onClick={() => void onMode(item)}
              >
                {modeLabel(item, zh)}
              </button>
            ))}
          </div>
          <button className="v8-compare-button" onClick={onSheet}>
            {t("live.compareAll")}
          </button>
        </div>
        <div className="v8-live-side">
          <div className="v8-next-card">
            <span>{t("live.leaveBy")}</span>
            <h3>{next?.title ?? t("live.awaitingPlan")}</h3>
            <p>
              {next
                ? t("live.arriveBy", { date: dateInZone(next.start_at, locale, data.journey.timezone || "UTC") })
                : t("live.selectPlan")}{" "}
              · {selected?.protected_margin_min ?? 0} min slack
            </p>
            <div className="v8-eta">
              <strong>
                {next ? clockInZone(next.start_at, data.journey.timezone || "UTC") : "—"}
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
                {disruptions.length
                  ? t("live.guardianMonitoring", { severity: disruptions[0].severity })
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
        </div>
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

// Booking vocabulary in traveller language.  Internal codes such as
// UNKNOWN_REALTIME, STRUCTURED_JSON and C4 must never be the primary reading.
const BOOKING_TYPES: Record<string, { zh: string; en: string }> = {
  FLIGHT: { zh: "航班", en: "Flight" },
  RAIL: { zh: "火车", en: "Rail" },
  COACH: { zh: "大巴", en: "Coach" },
  FERRY: { zh: "轮渡", en: "Ferry" },
  HOTEL: { zh: "住宿", en: "Hotel" },
  TICKET: { zh: "门票", en: "Ticket" },
  RESERVATION: { zh: "预订", en: "Reservation" },
};

function bookingTypeLabel(value: string | null | undefined): string {
  const key = String(value ?? "").toUpperCase();
  return BOOKING_TYPES[key]?.zh ?? key.replaceAll("_", " ").toLowerCase();
}

function realtimeLabel(value: string | null | undefined, zh: boolean): string {
  const key = String(value ?? "").toUpperCase();
  if (key === "ON_TIME" || key === "NORMAL") return zh ? "准点" : "On time";
  if (key === "DELAYED") return zh ? "延误" : "Delayed";
  if (key === "CANCELLED") return zh ? "已取消" : "Cancelled";
  if (key === "UNKNOWN_REALTIME" || key === "UNKNOWN" || !key) {
    return zh ? "暂无实时状态" : "No live status";
  }
  return zh ? "状态未知" : "Status unknown";
}

function Bookings({
  data,
  selected,
  chosen,
  wallet,
  onImport,
  busy,
}: {
  data: V8Data;
  selected: V8Data["options"][number] | null;
  chosen: V8Data["options"][number] | null;
  wallet: Wallet | null;
  onImport: (reservation: Record<string, unknown>) => Promise<void>;
  busy: boolean;
}) {
  const t = useT();
  const { locale } = useLocale();
  const zh = locale.startsWith("zh");
  const [input, setInput] = useState("");
  const [parseError, setParseError] = useState<string | null>(null);
  const submit = async () => {
    // A traveller pastes a ticket, not JSON.  Failing to parse must produce a
    // visible, localised message instead of an unhandled exception.
    let value: Record<string, unknown>;
    try {
      const parsed = JSON.parse(input);
      if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
        throw new Error("not an object");
      }
      value = parsed as Record<string, unknown>;
    } catch {
      setParseError(
        input.trim().startsWith("{")
          ? zh
            ? "这段内容不是有效的预订数据。请检查格式，或改用上面的粘贴/手动方式。"
            : "That is not valid booking data. Check the format, or use the paste/manual flow above."
          : zh
            ? "这里只接受结构化数据。普通文字请用「粘贴确认单」或「手动录入」。"
            : "Only structured data is accepted here. For normal text use Paste or Manual entry above.",
      );
      return;
    }
    setParseError(null);
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
          {selected ? (
            <article className="v8-booking-card selected">
              <div className="v8-booking-icon">
                <Icon name="bed" />
              </div>
              <div>
                <span className="v8-selected-label">
                  {chosen ? t("bookings.stayEvidence") : t("bookings.stayPreview")}
                </span>
                <h2>{selected.stay.property_name}</h2>
                <p>
                  {selected.stay.room_type} ·{" "}
                  {selected.stay.refundable
                    ? t("bookings.freeCancel")
                    : t("bookings.nonRefundable")}
                </p>
                <strong data-testid="bookings-stay-total">
                  {stayTotalLabel(selected, t, locale)} {t("bookings.total")}
                </strong>
              </div>
              <span className="v8-booking-state">
                {chosen ? t("bookings.notBooked") : t("bookings.notChosen")}
              </span>
            </article>
          ) : (
            <article className="v8-booking-card" data-testid="bookings-no-stay">
              <div className="v8-booking-icon">
                <Icon name="bed" />
              </div>
              <div>
                <span className="v8-selected-label">{t("bookings.stayEvidence")}</span>
                <h2>{t("bookings.noStay")}</h2>
                <p>{t("bookings.noStaySub")}</p>
              </div>
            </article>
          )}
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
                  {zh ? bookingTypeLabel(item.type) : item.type} ·{" "}
                  {realtimeLabel(item.realtime_status, zh)}
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
              <span className="v8-booking-state safe">
                {zh ? "已确认 · 受保护" : "Confirmed · protected"}
              </span>
            </article>
          ))}
        </div>
        <aside className="v9-inbox">
          <span className="v8-kicker">{zh ? "导入预订" : "Import a booking"}</span>
          <p className="v8-lede">
            {zh
              ? "在「行程 · 预订」里粘贴确认单、手动录入或上传截图。这个页面只用于结构化数据。"
              : "Use Trips · Bookings to paste a confirmation, type one in, or upload a screenshot. This panel is for structured data only."}
          </p>
          <details className="v8-advanced" data-testid="bookings-advanced">
            <summary>{zh ? "高级：结构化数据" : "Advanced: structured data"}</summary>
            <label htmlFor="reservation-json">{t("bookings.reservationJson")}</label>
            <textarea
              id="reservation-json"
              data-testid="bookings-json-input"
              value={input}
              onChange={(event) => {
                setInput(event.target.value);
                if (parseError) setParseError(null);
              }}
              placeholder={'{"reservation_type":"RAIL", "confirmation_ref":"…"}'}
            />
            <button
              className="v8-primary"
              disabled={busy || input.trim().length < 2}
              onClick={() => void submit()}
            >
              {t("bookings.reviewProtect")}
            </button>
            {parseError && (
              <p className="role-alert" role="alert" data-testid="bookings-parse-error">
                {parseError}
              </p>
            )}
            <small>{t("bookings.neverInvented")}</small>
          </details>
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
  wallet,
}: {
  data: V8Data;
  policy: Policy | null;
  onActivate: () => Promise<void>;
  wallet?: Wallet | null;
}) {
  const t = useT();
  const { locale } = useLocale();
  const zh = locale.startsWith("zh");

  // The traveller reads a human sentence, not the internal delegation enum.
  const freedomLabel = (mode: string | null | undefined): string => {
    switch (String(mode ?? "").toUpperCase()) {
      case "AUTONOMOUS":
        return zh ? "自动执行已开启" : "Automatic changes are on";
      case "ASSISTED":
        return zh ? "重要改动先问你" : "I ask before important changes";
      default:
        return zh ? "仅提供建议" : "Suggestions only";
    }
  };
  const cityLabel =
    CITY_NAME_BY_SLUG[String(data.journey.city_code || "").split("-").pop()?.toUpperCase() ?? ""]?.[
      zh ? "zh" : "en"
    ] ?? String(data.journey.city_code || "").split("-").pop() ?? "";

  const bookings = wallet?.reservations ?? [];
  const stay = (data.options ?? []).find((o) => o.id === data.selected_option_id) ?? null;
  const [showAdvanced, setShowAdvanced] = useState(false);

  return (
    <section className="v8-page" data-testid="v8-me">
      <div className="v8-page-intro compact">
        <div>
          <p className="v8-kicker">{zh ? "我的" : "Me"}</p>
          <h1>{zh ? "我的行程与偏好" : "My trip and preferences"}</h1>
          <p className="v8-lede">
            {zh
              ? "这里是你这趟行程的事实：同行人数、预算、住宿和已确认的预订。"
              : "The facts of this trip: party, budget, stay and confirmed bookings."}
          </p>
        </div>
      </div>

      <div className="v8-me-grid">
        <article className="v8-me-card">
          <span className="v8-kicker">{zh ? "这趟行程" : "This trip"}</span>
          <strong>{cityLabel}</strong>
          <p>
            {t("shell.travelers", { n: data.trip.party_size })} ·{" "}
            {money(data.journey.budget.amount_minor, data.journey.budget.currency, locale)}
          </p>
        </article>

        <article className="v8-me-card">
          <span className="v8-kicker">{zh ? "住宿" : "Stay"}</span>
          <strong>{stay ? stay.stay.property_name : zh ? "还没有选定" : "Not chosen yet"}</strong>
          <p>
            {stay
              ? zh
                ? "已确认的住宿"
                : "Confirmed stay"
              : zh
                ? "在「行程 · 住宿」里挑选"
                : "Choose it in Trips · Stay"}
          </p>
        </article>

        <article className="v8-me-card">
          <span className="v8-kicker">{zh ? "已确认的预订" : "Confirmed bookings"}</span>
          <strong>
            {bookings.length
              ? zh
                ? `${bookings.length} 项`
                : `${bookings.length}`
              : zh
                ? "还没有"
                : "None yet"}
          </strong>
          <p>
            {bookings.length
              ? zh
                ? "受保护的预订，不会被自动改动。"
                : "Protected bookings; they are never changed automatically."
              : zh
                ? "在「行程 · 预订」里导入你的票或确认单。"
                : "Import a ticket or confirmation in Trips · Bookings."}
          </p>
        </article>

        <article className="v8-me-card">
          <span className="v8-kicker">{zh ? "改动偏好" : "Change preferences"}</span>
          <strong>{freedomLabel(policy?.mode)}</strong>
          <p>
            {zh
              ? "任何会影响已确认预订或受保护安排的改动，都会先征得你同意。"
              : "Anything affecting a confirmed booking or protected plan asks you first."}
          </p>
          <label className="me-mode-row">
            <span>{zh ? "开启自动执行" : "Allow automatic changes"}</span>
            <input
              type="checkbox"
              data-testid="me-mode-toggle"
              checked={String(policy?.mode ?? "").toUpperCase() === "AUTONOMOUS"}
              onChange={() => void onActivate()}
            />
          </label>
        </article>

        <PushCapabilityCard travelerId={data.journey.traveler_id} />
      </div>

      <details className="v8-advanced" data-testid="me-advanced">
        <summary>{zh ? "高级详情" : "Advanced detail"}</summary>
        <div className="v8-me-grid">
          <article className="v8-me-card">
            <span className="v8-kicker">{zh ? "委派范围" : "Delegation scope"}</span>
            <ul>
              <li>
                {t("me.maxCost")}{" "}
                {money(policy?.max_auto_replan_cost_delta_minor ?? 5000, data.journey.budget.currency, locale)}
              </li>
              <li>
                {t("me.maxLoss")} {money(policy?.max_auto_loss_minor ?? 0, data.journey.budget.currency, locale)}
              </li>
              <li>
                {t("me.scheduleDrift")} {policy?.max_auto_schedule_drift_min ?? 20} {t("me.minutes")}
              </li>
              <li>{t("me.protectedMoments")}</li>
            </ul>
          </article>
          <article className="v8-me-card">
            <span className="v8-kicker">{zh ? "技术标识" : "Technical identifiers"}</span>
            <ul className="me-identifiers">
              <li>
                <b>mode</b> <code>{policy?.mode ?? "ADVISORY"}</code>
              </li>
              <li>
                <b>version</b> <code>{policy?.version ?? "—"}</code>
              </li>
              <li>
                <b>city_code</b> <code>{data.journey.city_code}</code>
              </li>
            </ul>
            <button type="button" className="v8-outline-button" onClick={() => setShowAdvanced(!showAdvanced)}>
              {showAdvanced ? (zh ? "收起" : "Hide") : zh ? "查看策略详情" : "View policy detail"}
            </button>
            {showAdvanced && (
              <pre className="me-policy-json" data-testid="me-policy-json">
                {JSON.stringify(policy ?? {}, null, 2)}
              </pre>
            )}
          </article>
        </div>
      </details>
    </section>
  );
}

/** Latin city-code slug for a city name, matching the discovery provider.
 *
 * Chinese city names are mapped to their standard pinyin code so the journey's
 * city_code agrees with the places the provider materialises.  Unknown names
 * fall back to a normalised latin slug.
 */
// Reverse of CITY_CODE_SLUGS: a created Journey stores the latin slug, but the
// traveller reads the city in their own language.
// Travel modes are internal enum values (WALK, RIDE_HAIL).  The traveller
// reads a normal word for how they will move.
function modeLabel(mode: string, zh: boolean): string {
  const key = String(mode).toUpperCase();
  const labels: Record<string, { zh: string; en: string }> = {
    WALK: { zh: "步行", en: "Walk" },
    BICYCLE: { zh: "骑行", en: "Cycle" },
    TRANSIT: { zh: "公交地铁", en: "Transit" },
    AUTO: { zh: "驾车", en: "Drive" },
    RIDE_HAIL: { zh: "网约车", en: "Ride-hail" },
  };
  const entry = labels[key];
  return entry ? (zh ? entry.zh : entry.en) : key.replace("_", " ").toLowerCase();
}

const CITY_NAME_BY_SLUG: Record<string, { zh: string; en: string }> = {
  XIAMEN: { zh: "厦门", en: "Xiamen" },
  BEIJING: { zh: "北京", en: "Beijing" },
  SHANGHAI: { zh: "上海", en: "Shanghai" },
  TIANJIN: { zh: "天津", en: "Tianjin" },
  FUZHOU: { zh: "福州", en: "Fuzhou" },
  GUANGZHOU: { zh: "广州", en: "Guangzhou" },
  SHENZHEN: { zh: "深圳", en: "Shenzhen" },
  CHENGDU: { zh: "成都", en: "Chengdu" },
  HANGZHOU: { zh: "杭州", en: "Hangzhou" },
  TOKYO: { zh: "东京", en: "Tokyo" },
  SINGAPORE: { zh: "新加坡", en: "Singapore" },
};

const CITY_CODE_SLUGS: Record<string, string> = {
  "厦门": "XIAMEN", "北京": "BEIJING", "上海": "SHANGHAI", "天津": "TIANJIN",
  "福州": "FUZHOU", "广州": "GUANGZHOU", "深圳": "SHENZHEN",
  "成都": "CHENGDU", "杭州": "HANGZHOU", "东京": "TOKYO", "新加坡": "SINGAPORE",
};

function cityCodeSlug(name: string): string {
  const trimmed = name.trim();
  if (CITY_CODE_SLUGS[trimmed]) return CITY_CODE_SLUGS[trimmed];
  const lower = trimmed.toLowerCase();
  if (CITY_CODE_SLUGS[lower]) return CITY_CODE_SLUGS[lower];
  return trimmed.toUpperCase().replace(/\s+/g, "-");
}
