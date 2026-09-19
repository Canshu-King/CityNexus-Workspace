import { useEffect, useState } from "react";
import { formatMinorMoney } from "../../lib/money";

type Proposal = {
  id: string;
  status: string;
  proposed_plan_version_id: string;
  locked_commitments_preserved: boolean;
  diff: {
    removed?: string[];
    added?: string[];
    cost_delta_minor?: number;
    travel_delta_min?: number;
    verified_evidence?: {
      baseline_plan_evidence?: { snapshot_id?: string | null };
      incident_recovery_evidence?: {
        route_provenance?: string;
        source_provider?: string;
        mobility_snapshot?: MobilityEvidence;
      };
      impact_resolution?: {
        semantic_reason?: string;
        semantic_explanation?: string;
      };
      mobility?: { snapshot?: MobilityEvidence };
    };
  };
  explanation?: { impact_model?: string; impact_provider?: string };
};

type MobilityEvidence = {
  snapshot_id?: string;
  source_provider?: string;
  degraded?: boolean;
};

type Props = {
  journeyId: string;
  policy?: { mode: "ADVISORY" | "ASSISTED" | "AUTONOMOUS"; auto_accept_replan: boolean } | null;
  currency?: string;
  onAccepted?: () => void;
};

function moneyDelta(value: number | undefined, currency = "CNY"): string {
  if (value == null || value === 0) return "No cost change";
  return `${value > 0 ? "+" : "−"}${formatMinorMoney(Math.abs(value), currency, "en-US")}`;
}

export function V14RecoveryTruthPanel({ journeyId, policy, currency = "CNY", onAccepted }: Props) {
  const [proposal, setProposal] = useState<Proposal | null>(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const refresh = async () => {
    const response = await fetch(`/api/v1/journeys/${journeyId}/replans`);
    if (!response.ok) return;
    const items = (await response.json()) as Proposal[];
    setProposal(items.find((item) => item.status === "PRESENTED") ?? items[0] ?? null);
  };

  useEffect(() => {
    void refresh();
  }, [journeyId]);

  const accept = async () => {
    if (!proposal) return;
    setBusy(true);
    try {
      const response = await fetch(`/api/v1/replans/${proposal.id}/accept`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Idempotency-Key": `v14-ui-${proposal.id}`,
        },
      });
      const body = await response.json();
      if (!response.ok) throw new Error(body?.detail ?? "Recovery acceptance failed");
      setMessage("Recovery accepted · the child PlanVersion is now authoritative.");
      await refresh();
      onAccepted?.();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Recovery acceptance failed");
    } finally {
      setBusy(false);
    }
  };

  const verified = proposal?.diff.verified_evidence;
  const incident = verified?.incident_recovery_evidence;
  const snapshot = incident?.mobility_snapshot ?? verified?.mobility?.snapshot;
  const authorization = policy
    ? `${policy.mode} · ${policy.auto_accept_replan ? "envelope auto-accept enabled" : "confirmation required"}`
    : "policy unavailable · confirmation required";
  return (
    <section className="v12-authoritative-panel" data-testid="v14-recovery-truth">
      <header className="v12-panel-header">
        <div>
          <span className="v8-kicker">V14 · REALITY CHANGED</span>
          <h2>Grounded adaptive recovery</h2>
        </div>
        <button className="v8-outline-button" type="button" onClick={() => void refresh()}>
          Refresh recovery
        </button>
      </header>
      {!proposal && <p className="v8-muted">No recovery proposal is waiting on this Journey.</p>}
      {proposal && (
        <>
          <div className="v12-now-next">
            <article className="v12-state-card now">
              <span className="v12-state-kicker">CHANGED</span>
              <strong data-testid="v14-recovery-changed">
                {proposal.diff.removed?.[0] ?? "Current activity"}
              </strong>
              <small>→ {proposal.diff.added?.[0] ?? "recovered activity"}</small>
            </article>
            <article className="v12-state-card next">
              <span className="v12-state-kicker">PROTECTED</span>
              <strong data-testid="v14-recovery-protected">
                {proposal.locked_commitments_preserved ? "C4 commitments preserved" : "Review commitment impact"}
              </strong>
              <small>{moneyDelta(proposal.diff.cost_delta_minor, currency)} · {proposal.diff.travel_delta_min ?? 0} min route delta</small>
            </article>
          </div>
          <div className="v8-cost-lines">
            <div>
              <span>Baseline evidence</span>
              <b>{verified?.baseline_plan_evidence?.snapshot_id ?? "—"}</b>
            </div>
            <div>
              <span>Incident evidence</span>
              <b data-testid="v14-recovery-provider">
                {incident?.source_provider ?? snapshot?.source_provider ?? "—"} · {incident?.route_provenance ?? "—"}
              </b>
            </div>
            <div>
              <span>Deterministic gate</span>
              <b>{snapshot?.degraded ? "DEGRADED · confirmation" : "PASSED · provider facts frozen"}</b>
            </div>
            <div>
              <span>Delegation policy</span>
              <b data-testid="v14-recovery-authorization">{authorization}</b>
            </div>
          </div>
          <p className="v8-muted">
            {verified?.impact_resolution?.semantic_explanation ??
              verified?.impact_resolution?.semantic_reason ??
              `Impact interpreted by ${proposal.explanation?.impact_provider ?? "CityNexus"} · ${proposal.explanation?.impact_model ?? "deterministic gate"}.`}
          </p>
          {message && <p role="status">{message}</p>}
          {proposal.status === "PRESENTED" && (
            <button
              className="v8-primary"
              type="button"
              data-testid="v14-recovery-accept"
              disabled={busy}
              onClick={() => void accept()}
            >
              {busy ? "Applying…" : "Accept grounded recovery"}
            </button>
          )}
          {proposal.status === "ACCEPTED" && (
            <span className="v8-status-pill" data-testid="v14-recovery-accepted">
              Accepted child PlanVersion · {proposal.proposed_plan_version_id}
            </span>
          )}
        </>
      )}
    </section>
  );
}
