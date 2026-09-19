import { useEffect, useState } from "react";
import { useT, useLocale } from "../../i18n/LocaleContext";
import { formatMinorMoney } from "../../lib/money";

type Candidate = {
  id: string;
  name: string;
  category: string;
  provider_key?: string;
  latitude: number;
  longitude: number;
  opening_hours?: { status?: string; open?: string; close?: string; source_urls?: string[] };
  cost_evidence?: { status?: string; amount_minor?: number | null; currency?: string };
};

type DiscoveryResponse = {
  intent: {
    provider: string;
    model?: string | null;
    anchor_key: string;
    explanation: string;
    queries: Array<{ query: string; radius_m: number; limit: number }>;
  };
  anchor?: { source?: string; location?: string; latitude: number; longitude: number } | null;
  discovery: {
    provenance: string;
    mode: string;
    provider_status: Record<string, unknown>;
    provider_evidence?: {
      mobility?: {
        provider?: string;
        captured_at?: string;
        supported_modes?: string[];
        route_provenance?: string;
        cost_provenance?: string;
      };
      weather?: { provider?: string; time_basis?: string };
    };
    candidates: Candidate[];
  };
  curation: {
    provider: string;
    semantic_fallback?: string;
    rejected_candidate_ids: string[];
    ranked: Array<{ candidate_id: string; semantic_fit: number; reason: string }>;
  };
  feasibility: {
    passed: boolean;
    authority: string;
    eligible: Candidate[];
    rejected: Array<{ candidate_id: string; reason: string }>;
  };
  replay: { sealed: boolean; provenance: string; provider_status: Record<string, unknown> };
  selected_plan?: { id: string; status: string; version_no: number };
  require_fully_grounded?: boolean;
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    ...init,
  });
  const body = await response.json();
  if (!response.ok) {
    throw new Error(body?.error?.message ?? body?.detail ?? `Request failed (${response.status})`);
  }
  return body as T;
}

export function RealCityDiscoveryPanel({
  journeyId,
  cityCode,
  onComplete,
  onOpenPlan,
}: {
  journeyId: string;
  cityCode: string;
  onComplete: () => Promise<void>;
  onOpenPlan: () => void;
}) {
  const t = useT();
  const { locale } = useLocale();
  const supportsTianjinReplay = ["CN-TIANJIN", "TIANJIN", "TSN", "CNX-DEMO"].includes(cityCode.toUpperCase().replaceAll("_", "-"));
  const [goal, setGoal] = useState("I prefer quiet indoor culture, low walking, and rain-friendly places near my protected Journey moments.");
  const [mode, setMode] = useState<"captured_replay" | "live" | "replay">(supportsTianjinReplay ? "captured_replay" : "live");
  const [result, setResult] = useState<DiscoveryResponse | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setMode(supportsTianjinReplay ? "captured_replay" : "live");
  }, [supportsTianjinReplay]);

  const money = (value: number | null | undefined, currency = "CNY") =>
    value == null
      ? t("mobility.costUnknown")
      : formatMinorMoney(value, currency, locale === "zh-CN" ? "zh-CN" : "en-US");

  const runDiscovery = async () => {
    setBusy(true);
    setError(null);
    try {
      const next = await request<DiscoveryResponse>(`/api/v1/journeys/${journeyId}/real-city/intelligence`, {
        method: "POST",
        body: JSON.stringify({ goal, mode, radius_m: 3200, limit: 8, candidate_count: 2, require_fully_grounded: mode === "captured_replay" }),
      });
      setResult(next);
      await onComplete();
    } catch (cause) {
      const message = cause instanceof Error ? cause.message : "";
      if (message === "V13_DISCOVERY_NO_FEASIBLE_PLACE_SET") {
        setError(t("discovery.noGroundedCandidates"));
      } else if (message.startsWith("DeepSeek discovery failed")) {
        setError(t("discovery.aiUnavailable"));
      } else {
        setError(message || t("discovery.composeError"));
      }
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="v8-page" data-testid="v13-discovery">
      <div className="v8-page-intro compact">
        <div>
            <p className="v8-kicker">{t("discovery.kicker")}</p>
          <h1>{t("discovery.title")}</h1>
          <p className="v8-lede">{t("discovery.lede")}</p>
        </div>
        <span className="v8-evidence-label"><span className="status-dot" />{mode === "captured_replay" ? t("discovery.sealedRealReplay") : mode === "live" ? t("discovery.liveProviderMode") : t("discovery.demoReplay")}</span>
      </div>
      <div className="v8-agent-composer-card">
        <div className="v8-agent-copy">
          <span className="v8-agent-mark">{t("discovery.brand")}</span>
          <h2>{t("discovery.shapeCity")}</h2>
          <p>{t("discovery.shapeSub")}</p>
          <div className="v8-agent-boundary"><b>{t("discovery.boundary")}</b><span>{t("discovery.boundarySub")}</span></div>
        </div>
        <div className="v8-agent-input">
          <label htmlFor="v13-discovery-goal">{t("discovery.intent")}</label>
          <textarea id="v13-discovery-goal" data-testid="v13-discovery-goal" value={goal} onChange={(event) => setGoal(event.target.value)} />
          <div className="v8-agent-toolbar">
            <label>{t("discovery.evidenceMode")} <select aria-label={t("discovery.evidenceMode")} value={mode} onChange={(event) => setMode(event.target.value as typeof mode)}>{supportsTianjinReplay && <option value="captured_replay">{t("discovery.sealedRealReplay")}</option>}<option value="live">{t("discovery.liveProviders")}</option>{supportsTianjinReplay && <option value="replay">{t("discovery.syntheticDemo")}</option>}</select></label>
            <button className="v8-primary" data-testid="v13-discover-submit" disabled={busy || goal.trim().length < 3} onClick={() => void runDiscovery()}>{busy ? t("discovery.composing") : t("discovery.discoverCompose")}</button>
          </div>
          {!supportsTianjinReplay && <p className="v8-sheet-note">{t("discovery.genericCityLiveNote")}</p>}
        </div>
      </div>
      {error && <div className="v8-message" role="alert">{error}</div>}
      {result && (
        <div className="v8-intelligence-grid" data-testid="v13-discovery-result">
          <article className="v8-intel-hero">
            <span className="v8-status-pill violet" data-testid="v13-discovery-provider">{result.intent.provider}</span>
            <h2>{result.intent.explanation || t("discovery.groundedStop")}</h2>
            <p>{t("discovery.anchor")} <b>{result.intent.anchor_key}</b>{result.anchor?.location ? ` · ${result.anchor.location}` : ""}</p>
            <p>{t("discovery.query")} {result.intent.queries[0]?.query} · {t("discovery.radius", { r: result.intent.queries[0]?.radius_m, max: result.intent.queries[0]?.limit })}</p>
            <div className="v8-chain"><span>{t("discovery.memory")}</span><b>→</b><span>{t("intel.deepseek")}</span><b>→</b><span>{t("discovery.providers")}</span><b>→</b><span>{t("discovery.detGate")}</span></div>
          </article>
          <div className="v8-intel-facts">
            <div><span>{t("discovery.provenance")}</span><b>{result.replay.provenance === "SEALED_REAL_REPLAY" ? t("discovery.sealedRealReplay") : result.replay.sealed ? t("discovery.sealed") : result.discovery.provenance}</b><small>{result.discovery.mode} · {String(result.discovery.provider_status.overpass ?? t("discovery.providerCaptured"))}</small></div>
            <div><span>{t("discovery.mobility")}</span><b>{result.discovery.provider_evidence?.mobility?.provider ?? t("discovery.explicitFallback")}</b><small>{result.discovery.provider_evidence?.mobility?.supported_modes?.join(" + ") ?? t("discovery.factFallback")} · {result.discovery.provider_evidence?.mobility?.route_provenance ?? t("discovery.syntheticFallback")}</small></div>
            <div><span>{t("discovery.grounding")}</span><b>{result.require_fully_grounded ? t("discovery.fullyGrounded") : t("discovery.mixedDegraded")}</b><small>{result.discovery.provider_evidence?.mobility?.cost_provenance ?? t("discovery.costSeparate")}</small></div>
            <div><span>{t("discovery.feasibility")}</span><b>{result.feasibility.passed ? t("discovery.passed") : t("discovery.blocked")}</b><small>{result.feasibility.authority}</small></div>
            <div data-testid="v13-discovery-selected-plan"><span>{t("discovery.planversion")}</span><b>{result.selected_plan?.status ?? t("discovery.notSelected")}</b><small>{result.selected_plan ? `v${result.selected_plan.version_no} · ${result.selected_plan.id}` : t("discovery.noPlan")}</small></div>
          </div>
        </div>
      )}
      {result && <div className="v8-stay-layout">
        <div className="v8-stay-list">
          {result.discovery.candidates.slice(0, 4).map((candidate) => {
            const rank = result.curation.ranked.find((item) => item.candidate_id === candidate.id);
            const eligible = result.feasibility.eligible.some((item) => item.id === candidate.id);
            return <article className={eligible ? "v8-stay-card selected" : "v8-stay-card"} key={candidate.id}>
              <div className="v8-stay-card-body"><div className="v8-stay-card-title"><div><span className="v8-rank">{eligible ? "✓" : "—"}</span><h3>{candidate.name}</h3></div><span className="v8-selected-label">{eligible ? t("discovery.eligible") : t("discovery.rejected")}</span></div>
                <p>{candidate.category} · {candidate.provider_key ?? t("discovery.providerGrounded")}</p>
                <div className="v8-stay-impact"><span>{candidate.opening_hours?.status ?? t("discovery.hoursUnknown")}</span><b>{money(candidate.cost_evidence?.amount_minor, candidate.cost_evidence?.currency)}</b><em>{rank ? t("discovery.semanticFit", { n: Math.round(rank.semantic_fit * 100) }) : t("discovery.notRanked")}</em></div>
                {candidate.opening_hours?.source_urls?.[0] && <small>{t("discovery.sourceCaptured", { url: new URL(candidate.opening_hours.source_urls[0]).hostname })}</small>}
                {rank?.reason && <small>{rank.reason}</small>}
              </div>
            </article>;
          })}
        </div>
        <aside className="v8-boundary-card"><b>{t("discovery.authoritativeNext")}</b><p>{t("discovery.authoritativeSub")}</p><button className="v8-primary" onClick={onOpenPlan}>{t("discovery.openAuthoritative")}</button>{result.curation.rejected_candidate_ids.length > 0 && <small>{t("discovery.rejectedIds")} {result.curation.rejected_candidate_ids.join(", ")}</small>}</aside>
      </div>}
    </section>
  );
}
