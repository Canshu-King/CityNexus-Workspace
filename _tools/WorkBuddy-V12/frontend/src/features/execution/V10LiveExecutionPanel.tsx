import {
  Activity,
  Clock3,
  ExternalLink,
  ShieldCheck,
  WifiOff,
} from "lucide-react";
import {
  useExecutionClock,
  useWebObservations,
} from "../../api/v10Execution";

type Props = { journeyId: string };

export function V10LiveExecutionPanel({ journeyId }: Props) {
  const clock = useExecutionClock(journeyId);
  const web = useWebObservations(journeyId);
  const now = clock.data ? new Date(clock.data.now) : null;
  return (
    <section
      className="v10-execution-panel"
      data-testid="v10-live-execution-panel"
    >
      <div className="v10-execution-heading">
        <div>
          <span className="v8-kicker">LIVE STATUS</span>
          <h3>What is happening now</h3>
        </div>
        <span className="v10-truth-pill">
          <ShieldCheck size={14} /> updated just now
        </span>
      </div>
      <div className="v10-execution-grid">
        <div className="v10-metric">
          <Clock3 size={17} aria-hidden="true" />
          <span>CLOCK</span>
          <strong>
            {now
              ? now.toLocaleTimeString([], {
                  hour: "2-digit",
                  minute: "2-digit",
                })
              : "—"}
          </strong>
          <small>{clock.data?.timezone ?? "execution clock"}</small>
        </div>
        <div className="v10-metric">
          <Activity size={17} aria-hidden="true" />
          <span>CURRENT STEP</span>
          <strong>
            {clock.data?.current_activity_id ? "in progress" : "awaiting plan"}
          </strong>
          <small>{clock.data ? "journey status" : "loading"}</small>
        </div>
        <div className="v10-metric">
          <WifiOff size={17} aria-hidden="true" />
          <span>OFFLINE</span>
          <strong>read-only ready</strong>
          <small>next 24 hours saved</small>
        </div>
      </div>
      <details className="v10-evidence-drawer">
        <summary>
          Evidence trail{" "}
          <span>
            {web.data?.observations.length
              ? `${web.data.observations.length} sources`
              : "none recorded yet"}
          </span>
        </summary>
        {web.data?.observations.length ? (
          web.data.observations.slice(0, 3).map((item) => (
            <a
              className="v10-evidence-row"
              key={item.id}
              href={item.url}
              target="_blank"
              rel="noreferrer"
            >
              <span>
                <b>{item.title}</b>
                <small>
                  {item.domain} · {item.source_class}
                </small>
              </span>
              <ExternalLink size={14} aria-hidden="true" />
            </a>
          ))
        ) : (
          <p className="v10-muted">
            No web observation is authoritative. Search evidence appears here
            only after server capture.
          </p>
        )}
      </details>
    </section>
  );
}
