import { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import { createActor } from "xstate";
import {
  CityNexusApiError,
  cityNexusApi,
  type Activity,
  type PlanVersion,
} from "./api/citynexus";
import type { Commitment, JourneyTwin } from "./contracts/journeyTwin";
import type { ReplanProposal } from "./contracts/replan";
import { testIds } from "./contracts/testIds";
import {
  bootstrapGoldenScenario,
  injectClosureAndLoadCandidates,
  reconnectGoldenScenario,
  type GoldenScenarioSession,
} from "./demo/goldenScenario";
import { journeyModeMachine } from "./state/journeyModeMachine";
import "./styles.css";

const journeyStorageKey = "citynexus.demo.journey_id";
const closureOccurredAt = "2026-10-10T13:25:00+08:00";

function formatTime(value: string | null | undefined): string {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleTimeString("en-GB", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });
}

function formatMoney(amountMinor: number, currency: string): string {
  try {
    return new Intl.NumberFormat("zh-CN", {
      style: "currency",
      currency,
      maximumFractionDigits: 0,
    }).format(amountMinor);
  } catch {
    return amountMinor.toLocaleString("en-US") + " " + currency;
  }
}

function activityForId(plan: PlanVersion | null, activityId: string | null): Activity | null {
  if (!plan || !activityId) return null;
  return plan.activities.find((item) => item.id === activityId) ?? null;
}

function commitmentActivity(
  plan: PlanVersion | null,
  commitment: Commitment,
): Activity | null {
  return activityForId(plan, commitment.activity_id);
}

function semanticTitle(key: string, plan: PlanVersion | null): string {
  const activity = plan?.activities.find(
    (item) => item.place_id === key || item.city_service_id === key,
  );
  return activity?.title ?? key;
}

function proposalDiffText(proposal: ReplanProposal, plan: PlanVersion): string {
  const removed = proposal.diff.removed.map((key) => semanticTitle(key, plan));
  const added = proposal.diff.added.map((key) => semanticTitle(key, plan));
  const preserved = proposal.diff.preserved_protected.map((key) => semanticTitle(key, plan));
  return (
    "Removed " +
    (removed.join(", ") || "none") +
    " · added " +
    (added.join(", ") || "none") +
    " · protected preserved " +
    (preserved.join(", ") || "none")
  );
}

function proposalDeltaText(proposal: ReplanProposal, currency: string): string {
  const diff = proposal.diff;
  return (
    "Cost Δ " +
    formatMoney(diff.cost_delta_minor, currency) +
    " · travel Δ " +
    (diff.travel_delta_min >= 0 ? "+" : "") +
    diff.travel_delta_min +
    " min · end Δ " +
    (diff.end_time_delta_min >= 0 ? "+" : "") +
    diff.end_time_delta_min +
    " min"
  );
}

function errorMessage(error: unknown): string {
  if (error instanceof CityNexusApiError) {
    const body = error.body as { error?: { message?: string } } | null;
    return body?.error?.message ?? error.message;
  }
  return error instanceof Error ? error.message : "CityNexus request failed";
}

function App() {
  const actor = useMemo(() => createActor(journeyModeMachine), []);
  const [workflowState, setWorkflowState] = useState(() =>
    String(actor.getSnapshot().value),
  );
  const [session, setSession] = useState<GoldenScenarioSession | null>(null);
  const [proposals, setProposals] = useState<ReplanProposal[]>([]);
  const [selectedProposalId, setSelectedProposalId] = useState<string | null>(null);
  const [eventId, setEventId] = useState<string | null>(null);
  const [simulatorOpen, setSimulatorOpen] = useState(false);
  const [replanRejected, setReplanRejected] = useState(false);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastAction, setLastAction] = useState<string | null>(null);

  useEffect(() => {
    const subscription = actor.subscribe((snapshot) => {
      setWorkflowState(String(snapshot.value));
    });
    actor.start();
    actor.send({ type: "BOOTSTRAP" });

    let cancelled = false;
    async function loadJourney() {
      setLoading(true);
      setError(null);
      const storedJourneyId = localStorage.getItem(journeyStorageKey);
      try {
        let nextSession: GoldenScenarioSession;
        if (storedJourneyId) {
          try {
            nextSession = await reconnectGoldenScenario(storedJourneyId);
          } catch (reconnectError) {
            if (!(reconnectError instanceof CityNexusApiError) || reconnectError.status !== 404) {
              throw reconnectError;
            }
            localStorage.removeItem(journeyStorageKey);
            nextSession = await bootstrapGoldenScenario();
          }
        } else {
          nextSession = await bootstrapGoldenScenario();
        }
        if (cancelled) return;
        localStorage.setItem(journeyStorageKey, nextSession.journeyId);
        setSession(nextSession);
        actor.send({ type: "BOOTSTRAP_OK" });
      } catch (loadError) {
        if (cancelled) return;
        setError(errorMessage(loadError));
        actor.send({ type: "FAIL", message: errorMessage(loadError) });
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    void loadJourney();

    return () => {
      cancelled = true;
      subscription.unsubscribe();
      actor.stop();
    };
  }, [actor]);

  const plan = session?.plan ?? null;
  const twin: JourneyTwin | null = session?.twin ?? null;
  const current = activityForId(plan, twin?.current_activity_id ?? null);
  const currentIndex = current
    ? plan?.activities.findIndex((item) => item.id === current.id) ?? -1
    : -1;
  const next = currentIndex >= 0 ? plan?.activities[currentIndex + 1] ?? null : null;
  const envelope = twin?.context.feasibility_envelope;
  const opportunity = twin?.context.opportunity_window;
  const degradedProviders = twin?.context.degraded_providers ?? [];
  const c4Commitment = twin?.upcoming_commitments.find(
    (item) => item.level === "C4_Anchored",
  );
  const c4Activity = c4Commitment ? commitmentActivity(plan, c4Commitment) : null;
  const selectedProposal =
    proposals.find((item) => item.id === selectedProposalId) ?? proposals[0] ?? null;
  const families = Array.from(
    new Set(proposals.map((item) => String(item.diff.candidate_family))),
  );
  const planCurrency = plan?.total_cost.currency ?? "CNY";

  async function runClosure() {
    if (!session?.techArt) return;
    setBusy(true);
    setError(null);
    setLastAction(null);
    actor.send({ type: "EVENT_DETECTED" });
    try {
      const result = await injectClosureAndLoadCandidates(session, closureOccurredAt);
      const refreshedTwin = await cityNexusApi.getTwin(session.journeyId);
      setSession({ ...session, twin: refreshedTwin });
      setEventId(result.eventId);
      setProposals(result.proposals);
      setSelectedProposalId(result.proposals[0]?.id ?? null);
      setReplanRejected(false);
      setLastAction("Closure event and backend replan proposals loaded");
      actor.send({ type: "REPLANS_READY" });
    } catch (runError) {
      setError(errorMessage(runError));
      actor.send({ type: "FAIL", message: errorMessage(runError) });
    } finally {
      setBusy(false);
    }
  }

  async function acceptSelected() {
    if (!selectedProposal || !session) return;
    setBusy(true);
    setError(null);
    actor.send({ type: "ACCEPT" });
    try {
      const accepted = await cityNexusApi.acceptReplan(
        selectedProposal.id,
        "frontend-golden-accept-" + session.journeyId,
      );
      if (!accepted.twin.active_plan_version_id) {
        throw new Error("Accepted backend response has no active plan");
      }
      const acceptedPlan = await cityNexusApi.getPlan(accepted.twin.active_plan_version_id);
      const riverCruise = acceptedPlan.activities.find(
        (item) => item.place_id === "place-river-cruise",
      );
      if (!riverCruise) throw new Error("Accepted plan lost the protected River Cruise activity");
      setSession({
        journeyId: session.journeyId,
        plan: acceptedPlan,
        techArt:
          acceptedPlan.activities.find((item) => item.place_id === "place-tech-art") ?? null,
        riverCruise,
        twin: accepted.twin,
      });
      setProposals((existing) =>
        existing.map((item) => (item.id === accepted.proposal.id ? accepted.proposal : item)),
      );
      setLastAction("Accepted backend proposal " + accepted.proposal.id);
      actor.send({ type: "ACCEPTED" });
    } catch (acceptError) {
      setError(errorMessage(acceptError));
      actor.send({ type: "FAIL", message: errorMessage(acceptError) });
    } finally {
      setBusy(false);
    }
  }

  async function rejectSelected() {
    if (!selectedProposal) return;
    setBusy(true);
    setError(null);
    actor.send({ type: "REJECT" });
    try {
      const rejected = await cityNexusApi.rejectReplan(selectedProposal.id);
      setProposals((existing) =>
        existing.map((item) => (item.id === rejected.id ? rejected : item)),
      );
      setReplanRejected(true);
      setLastAction("Rejected backend proposal " + rejected.id);
      actor.send({ type: "REJECTED" });
    } catch (rejectError) {
      setError(errorMessage(rejectError));
      actor.send({ type: "FAIL", message: errorMessage(rejectError) });
    } finally {
      setBusy(false);
    }
  }

  if (loading) {
    return (
      <main className="shell loading-shell">
        <p className="eyebrow">CityNexus · deterministic journey mode</p>
        <h1>Connecting to the JourneyTwin</h1>
        <p data-testid={testIds.journeyStatus}>BOOTSTRAPPING · backend</p>
      </main>
    );
  }

  if (error && !twin) {
    return (
      <main className="shell loading-shell">
        <p className="eyebrow">CityNexus · deterministic journey mode</p>
        <h1>Journey connection unavailable</h1>
        <p data-testid={testIds.journeyStatus}>ERROR · {error}</p>
        <button onClick={() => window.location.reload()}>Retry backend connection</button>
      </main>
    );
  }

  return (
    <main className="shell">
      <header>
        <p className="eyebrow">CityNexus · deterministic journey mode</p>
        <h1>Commitment-aware recovery</h1>
        <span
          data-testid={testIds.journeyStatus}
          data-source="backend"
          data-journey-id={session?.journeyId}
          className="status"
        >
          {twin?.context.journey_status ?? "UNKNOWN"} · backend truth
        </span>
        {replanRejected && <span className="status muted-status"> · proposal rejected</span>}
        <p className="workflow-state">
          UI workflow · {workflowState}
          {lastAction ? " · " + lastAction : ""}
        </p>
        {error && <p className="error-note">{error}</p>}
      </header>
      <section className="grid">
        <div data-testid={testIds.journeyMap} className="map-card">
          <div className="map-title">Journey map · backend route evidence</div>
          <div className="map-canvas" aria-label="Journey map markers and route">
            <span data-testid={testIds.mapCurrentMarker} className="map-marker current-marker">
              {current ? current.title : "Current"}
            </span>
            {eventId && (
              <span data-testid={testIds.mapEventMarker} className="map-marker event-marker">
                Closure event
              </span>
            )}
            {c4Activity && (
              <span data-testid={testIds.mapProtectedMarker} className="map-marker protected-marker">
                C4
              </span>
            )}
            <div data-testid={testIds.mapOldRoute} className="route-line old-route" />
            {proposals.length > 0 && <div data-testid={testIds.mapNewRoute} className="route-line new-route" />}
          </div>
          <p data-testid={testIds.currentActivity}>
            Current: {current?.title ?? "not reported"}
          </p>
          <p>Next: {next?.title ?? "no upcoming activity"}</p>
        </div>
        <aside className="evidence-card">
          <h2 data-testid={testIds.protectedCommitment}>
            🔒 {c4Activity?.title ?? "No active C4"} ·{" "}
            {c4Commitment ? formatTime(c4Commitment.policy.scheduled_start_at) : "—"} C4
          </h2>
          <p data-testid={testIds.nextCommitment}>
            Next activity · {next?.title ?? c4Activity?.title ?? "—"}
          </p>
          <p data-testid={testIds.nextCommitmentBuffer}>
            Next commitment buffer ·{" "}
            {envelope?.next_commitment_buffer_min == null
              ? "not available"
              : envelope.next_commitment_buffer_min + " min"}
          </p>
          <p data-testid={testIds.budgetRemaining}>
            Budget remaining ·{" "}
            {envelope ? formatMoney(envelope.budget_remaining_minor, planCurrency) : "—"}
          </p>
          <p data-testid={testIds.opportunityWindow}>
            Opportunity window ·{" "}
            {opportunity
              ? formatTime(opportunity.opens_at) +
                "–" +
                formatTime(opportunity.must_depart_by) +
                " · " +
                opportunity.available_minutes +
                " min available"
              : "not available"}
          </p>
          <p data-testid={testIds.feasibilityEnvelope}>
            Feasibility envelope · {envelope?.robust ? "robust" : "review"} · persisted backend
            evidence
          </p>
          <p
            data-testid={testIds.providerDegradation}
            className={degradedProviders.length ? "" : "provider-ready"}
          >
            Provider status ·{" "}
            {degradedProviders.length ? "degraded: " + degradedProviders.join(", ") : "ready"}
          </p>
          <div data-testid={testIds.upcomingCommitments} className="upcoming-list">
            <strong>Upcoming commitments from JourneyTwin</strong>
            {twin?.upcoming_commitments.map((commitment) => {
              const linked = commitmentActivity(plan, commitment);
              return (
                <span key={commitment.id}>
                  {linked?.title ?? commitment.policy.semantic_key ?? commitment.id} ·{" "}
                  {formatTime(commitment.policy.scheduled_start_at)} · {commitment.level}
                </span>
              );
            })}
          </div>
          <button
            data-testid={testIds.eventSimulator}
            onClick={() => setSimulatorOpen((value) => !value)}
            disabled={busy || !session?.techArt}
          >
            Demo Event Simulator
          </button>
          {simulatorOpen && session?.techArt && (
            <button
              data-testid={testIds.eventClosureButton}
              onClick={() => void runClosure()}
              disabled={busy}
            >
              Inject Tech Art closure · {formatTime(closureOccurredAt)}
            </button>
          )}
        </aside>
      </section>
      <section data-testid={testIds.journeyTimeline} className="timeline-card">
        <strong>Journey timeline · active PlanVersion</strong>
        <div className="timeline-track">
          {plan?.activities.map((activity) => {
            const isCurrent = activity.id === twin?.current_activity_id;
            const isProtected = activity.id === c4Activity?.id;
            return (
              <span
                key={activity.id}
                className={
                  "timeline-item" +
                  (isCurrent ? " active" : "") +
                  (isProtected ? " protected" : "")
                }
              >
                {formatTime(activity.start_at)} · {activity.title}
                {isProtected ? " · C4" : ""}
              </span>
            );
          })}
        </div>
      </section>
      {selectedProposal && plan && (
        <section data-testid={testIds.replanPanel} className="replan-card">
          <h2>Replan comparison · persisted proposals</h2>
          <div data-testid={testIds.replanCandidate} className="candidate">
            {selectedProposal.diff.candidate_family} ·{" "}
            {selectedProposal.hard_constraints_passed ? "verified feasible" : "not feasible"}
          </div>
          <div data-testid={testIds.replanCandidateFamilies} className="candidate-families">
            {families.map((family) => (
              <button
                key={family}
                className={
                  family === selectedProposal.diff.candidate_family
                    ? "family-chip selected"
                    : "family-chip"
                }
                onClick={() => {
                  const candidate = proposals.find(
                    (item) => item.diff.candidate_family === family,
                  );
                  setSelectedProposalId(candidate?.id ?? null);
                }}
                disabled={busy}
              >
                {family}
              </button>
            ))}
          </div>
          <p data-testid={testIds.replanScore}>
            Utility score · {selectedProposal.utility_score.toFixed(3)} ·{" "}
            {Object.entries(selectedProposal.score_breakdown)
              .filter(([key]) => key !== "total")
              .slice(0, 3)
              .map(([key, value]) => key + " " + Number(value).toFixed(2))
              .join(" · ")}
          </p>
          <p data-testid={testIds.replanEvidence}>
            Evidence · hard constraints{" "}
            {selectedProposal.hard_constraints_passed ? "pass" : "fail"} · C4{" "}
            {selectedProposal.locked_commitments_preserved ? "preserved" : "not preserved"} ·{" "}
            {selectedProposal.diff.verified_evidence
              ? "verified evidence attached"
              : "evidence unavailable"}
          </p>
          <p data-testid={testIds.replanDiff}>{proposalDiffText(selectedProposal, plan)}</p>
          <p data-testid={testIds.replanDeltas}>
            {proposalDeltaText(selectedProposal, planCurrency)} · protected commitments unchanged
          </p>
          <div className="replan-actions">
            <button
              data-testid={testIds.acceptReplan}
              onClick={() => void acceptSelected()}
              disabled={busy}
            >
              Accept backend replan
            </button>
            <button
              data-testid={testIds.rejectReplan}
              className="secondary-button"
              onClick={() => void rejectSelected()}
              disabled={busy}
            >
              Reject
            </button>
          </div>
        </section>
      )}
      <p data-testid={testIds.aiExplanation} className="note">
        Explanations are limited to verified JourneyTwin and ReplanDiff evidence.
      </p>
    </main>
  );
}

createRoot(document.getElementById("root")!).render(<App />);
