import type { ReactNode } from "react";

export type AgentRailStep = {
  id: string;
  label: string;
  status: "pending" | "active" | "done" | "approval" | "failed";
  detail?: ReactNode;
};

export function AgentRunRail({ steps }: { steps: AgentRailStep[] }) {
  return (
    <ol className="cn-agent-rail" aria-label="CityNexus agent progress" aria-live="polite">
      {steps.map((step) => (
        <li key={step.id} className={`cn-agent-step ${step.status}`}>
          <span className="cn-agent-step-mark" aria-hidden="true" />
          <div>
            <b>{step.label}</b>
            {step.detail && <small>{step.detail}</small>}
          </div>
        </li>
      ))}
    </ol>
  );
}
