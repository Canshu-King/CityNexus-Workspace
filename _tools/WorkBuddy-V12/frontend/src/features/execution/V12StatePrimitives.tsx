import type { ReactNode } from "react";
import { AlertTriangle, Check, CloudOff, LockKeyhole, Radio, ShieldCheck } from "lucide-react";
import type { ExecutionState } from "./V12AuthoritativeJourneyPanel";

export function ActivityCard({ title, state, locked = false }: { title: string; state: ExecutionState; locked?: boolean }) {
  return <article className="v12-activity-row"><span className="v12-activity-index">{state === "COMPLETED" ? <Check size={14} /> : "•"}</span><span className="v12-activity-title">{title}</span><span className="v12-activity-status">{state.replaceAll("_", " ")}{locked && <LockKeyhole size={12} />}</span></article>;
}

export function JourneyLeg({ mode, durationMin }: { mode: string; durationMin: number }) {
  return <div className="v12-leg-chip"><b>{mode}</b><span>{durationMin} min</span></div>;
}

export function CommitmentCard({ title, level = "C4_Anchored" }: { title: string; level?: string }) {
  return <article className="v12-commitment-card"><ShieldCheck size={15} /><div><b>{title}</b><small>{level} · protected</small></div></article>;
}

export function ImpactPreview({ passed, summary }: { passed: boolean; summary: string }) {
  return <div className={`v12-impact-card ${passed ? "passed" : "blocked"}`}><span>{passed ? <Check size={15} /> : <AlertTriangle size={15} />}</span><div><b>{passed ? "Impact preview passed" : "Impact preview blocked"}</b><small>{summary}</small></div></div>;
}

export function RiskBanner({ risk, children }: { risk: "SAFE" | "AT_RISK" | "CRITICAL"; children: ReactNode }) {
  return <div className={`v12-risk-banner risk-${risk.toLowerCase()}`}><AlertTriangle size={16} /><div><b>{risk.replaceAll("_", " ")}</b><span>{children}</span></div></div>;
}

export function AgentAction({ label, decision }: { label: string; decision: string }) {
  return <div className="v12-agent-action"><Radio size={15} /><div><b>{label}</b><small>Policy decision · {decision}</small></div></div>;
}

export function OfflineBanner({ readOnly = true }: { readOnly?: boolean }) {
  return <div className="v12-offline-banner"><CloudOff size={16} /><span>{readOnly ? "Offline snapshot · read only" : "Offline queue ready"}</span></div>;
}

export function EdgeStatus({ status = "SYNCED" }: { status?: "SYNCED" | "STALE" | "DEGRADED" }) {
  return <div className="v12-edge-status"><Radio size={15} /><span>PIC Edge · {status}</span></div>;
}

export function LiveJourney({ now, next, state }: { now: string; next: string; state: ExecutionState }) {
  return <div className="v12-live-journey"><span className="v8-kicker">LIVE JOURNEY · {state.replaceAll("_", " ")}</span><strong>{now}</strong><small>NEXT · {next}</small></div>;
}
