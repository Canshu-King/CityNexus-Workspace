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
import { useT } from "../../i18n/LocaleContext";

type Props = { journeyId: string };

export function V10LiveExecutionPanel({ journeyId }: Props) {
  const t = useT();
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
          <span className="v8-kicker">{t("exec.liveStatus")}</span>
          <h3>{t("exec.whatHappening")}</h3>
        </div>
        <span className="v10-truth-pill">
          <ShieldCheck size={14} /> {t("exec.updatedNow")}
        </span>
      </div>
      <div className="v10-execution-grid">
        <div className="v10-metric">
          <Clock3 size={17} aria-hidden="true" />
          <span>{t("exec.clock")}</span>
          <strong>
            {now
              ? now.toLocaleTimeString([], {
                  hour: "2-digit",
                  minute: "2-digit",
                })
              : "—"}
          </strong>
          <small>{clock.data?.timezone ?? t("exec.execClock")}</small>
        </div>
        <div className="v10-metric">
          <Activity size={17} aria-hidden="true" />
          <span>{t("exec.currentStep")}</span>
          <strong>
            {clock.data?.current_activity_id ? t("exec.inProgress") : t("live.awaitingPlan")}
          </strong>
          <small>{clock.data ? t("exec.journeyStatus") : t("exec.loading")}</small>
        </div>
        <div className="v10-metric">
          <WifiOff size={17} aria-hidden="true" />
          <span>{t("exec.offline")}</span>
          <strong>{t("exec.readOnlyReady")}</strong>
          <small>{t("exec.next24hSaved")}</small>
        </div>
      </div>
      <details className="v10-evidence-drawer">
        <summary>
          {t("exec.evidenceTrail", { n: web.data?.observations.length ?? 0 })}{" "}
          <span>
            {web.data?.observations.length
              ? t("exec.evidenceTrail", { n: web.data.observations.length })
              : t("exec.noEvidence")}
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
            {t("exec.noWebObs")}
          </p>
        )}
      </details>
    </section>
  );
}
