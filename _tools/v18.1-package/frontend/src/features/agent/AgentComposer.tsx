import { useMemo, useState } from "react";
import type { V8Data } from "../../app/v8Types";
import { cityNexusApi, type CopilotResponse } from "../../api/citynexus";
import { useLocale, useT } from "../../i18n/LocaleContext";
import { formatMinorMoney } from "../../lib/money";

type CopilotMessage = {
  role: "user" | "assistant";
  text: string;
  response?: CopilotResponse;
};

const intentLabel: Record<string, string> = {
  EXPLAIN_PLAN: "agent.intentExplain",
  WHAT_IF: "agent.intentWhatIf",
  DISCOVER: "agent.intentDiscover",
  PREFERENCE_CHANGE: "agent.intentPreference",
  DISRUPTION_REPORT: "agent.intentDisruption",
  REPLAN_REQUEST: "agent.intentReplan",
  VERIFY_FACT: "agent.intentVerifyFact",
  PERSONAL_ASSISTANCE: "agent.intentPersonalAssistance",
  UNKNOWN: "agent.intentUnknown",
};

export function AgentComposer({
  data,
  busy,
  onNavigate,
}: {
  data: V8Data;
  busy: boolean;
  onNavigate: (route: string) => void;
}) {
  const t = useT();
  const { locale } = useLocale();
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState<CopilotMessage[]>([]);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const localeCode = locale === "zh-CN" ? "zh" : "en";
  const suggestions = useMemo(
    () => [t("agent.suggestionExplain"), t("agent.suggestionWhatIf"), t("agent.suggestionDiscover")],
    [t],
  );

  const send = async () => {
    const value = message.trim();
    if (value.length < 2 || sending) return;
    setSending(true);
    setError(null);
    setMessages((current) => [...current, { role: "user", text: value }]);
    setMessage("");
    try {
      const response = await cityNexusApi.sendCopilotMessage(
        data.journey.id,
        value,
        localeCode,
      );
      setMessages((current) => [
        ...current,
        { role: "assistant", text: response.message, response },
      ]);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : t("agent.sendError"));
    } finally {
      setSending(false);
    }
  };

  const actionLabel = (action: string | null | undefined) => {
    if (action === "REQUEST_REPLAN") return t("agent.requestReplan");
    if (action === "REQUEST_PLACE_SEARCH") return t("agent.openDiscovery");
    if (action === "REQUEST_PREFERENCE_UPDATE") return t("agent.openPreferences");
    if (action === "REQUEST_PLAN_EXPLANATION") return t("agent.explainAgain");
    return null;
  };

  const continueAction = (action: string | null | undefined) => {
    if (action === "REQUEST_PLACE_SEARCH") onNavigate("discover");
    if (action === "REQUEST_REPLAN") onNavigate("authoritative");
    if (action === "REQUEST_PREFERENCE_UPDATE") onNavigate("me");
  };

  return (
    <section className="v8-page" data-testid="v15-copilot">
      <div className="v8-page-intro compact">
        <div>
          <p className="v8-kicker">{t("agent.kicker")}</p>
          <h1>{t("agent.title")}</h1>
          <p className="v8-lede">{t("agent.lede")}</p>
        </div>
        <span className="v8-status-pill violet">
          {data.traveler_twin?.learned_soft_dimensions?.length
            ? t("agent.twinActive")
            : t("agent.twinReady")}
        </span>
      </div>

      <div className="v8-agent-composer-card">
        <div className="v8-agent-copy">
          <span className="v8-agent-mark">{t("agent.brand")}</span>
          <h2>{t("agent.whatChange")}</h2>
          <p>{t("agent.whatChangeSub")}</p>
          <div className="v8-agent-boundary">
            <b>{t("agent.authorityBoundary")}</b>
            <span>{t("agent.boundarySub")}</span>
          </div>
        </div>
        <div className="v8-agent-input">
          <label htmlFor="v15-copilot-input">{t("agent.message")}</label>
          <textarea
            id="v15-copilot-input"
            value={message}
            onChange={(event) => setMessage(event.target.value)}
            placeholder={t("agent.inputPlaceholder")}
            data-testid="v15-copilot-input"
          />
          <div className="v8-agent-toolbar">
            <span>
              {t("agent.journeyPrefix")} {data.journey.title}
            </span>
            <button
              className="v8-primary"
              data-testid="v15-copilot-submit"
              disabled={busy || sending || message.trim().length < 2}
              onClick={() => void send()}
            >
              {sending ? t("agent.working") : t("agent.send")}
            </button>
          </div>
          <div className="v15-copilot-suggestions" aria-label={t("agent.suggestions") }>
            {suggestions.map((suggestion) => (
              <button
                key={suggestion}
                className="v8-outline-button"
                type="button"
                onClick={() => setMessage(suggestion)}
              >
                {suggestion}
              </button>
            ))}
          </div>
        </div>
      </div>

      {error && <p className="v8-message error">{error}</p>}

      <div className="v15-copilot-history" aria-live="polite">
        {messages.map((item, index) => (
          <article
            key={`${item.role}-${index}`}
            className={item.role === "user" ? "v15-copilot-message user" : "v15-copilot-message"}
          >
            <span className="v8-kicker">
              {item.role === "user" ? t("agent.you") : t("agent.citynexus")}
            </span>
            <p>{item.text}</p>
            {item.response && (
              <div className="v15-copilot-evidence">
                <div className="v15-copilot-badges">
                  <span className="v8-status-pill violet" data-testid="v15-intent">
                    {t(intentLabel[item.response.intent.name] ?? "agent.intentUnknown")}
                  </span>
                  <span className="v8-evidence-label" data-testid="v15-mode">
                    {item.response.mode === "AI" ? t("agent.aiBadge") : t("agent.fallbackBadge")}
                  </span>
                </div>
                {item.response.what_if && (
                  <div className="v15-what-if" data-testid="v15-what-if">
                    <div className="v15-what-if-head">
                      <b>{t("agent.whatIfPreview")}</b>
                      <span data-testid="v15-simulation-only">{t("agent.simulationOnly")}</span>
                    </div>
                    <div className="v15-what-if-grid">
                      <div>
                        <span>{t("agent.before")}</span>
                        <b>{formatMetric(item.response.what_if.before, item.response.what_if.before.cost_minor, locale)}</b>
                      </div>
                      <div>
                        <span>{t("agent.after")}</span>
                        <b>{formatMetric(item.response.what_if.after, item.response.what_if.after.cost_minor, locale)}</b>
                      </div>
                      <div>
                        <span>{t("agent.feasibility")}</span>
                        <b>{item.response.what_if.feasibility}</b>
                      </div>
                    </div>
                    <small>
                      {t("agent.protectedCount", {
                        n: item.response.what_if.protected_commitments.count,
                      })}{" "}
                      · {item.response.what_if.protected_commitments.preserved ? t("agent.preserved") : t("agent.notPreserved")}
                    </small>
                  </div>
                )}
                <div className="v15-copilot-action">
                  <span>{item.response.intent.provider === "deepseek" ? t("agent.aiInterpreted") : t("agent.fallbackInterpreted")}</span>
                  {actionLabel(item.response.action?.type) && item.response.action?.type !== "REQUEST_PLAN_EXPLANATION" && (
                    <button
                      className="v8-secondary"
                      type="button"
                      onClick={() => continueAction(item.response?.action?.type)}
                    >
                      {actionLabel(item.response.action?.type)}
                    </button>
                  )}
                </div>
                {item.response.intent.semantic_envelope && (
                  <div className="v15-copilot-semantic" data-testid="v17-semantic-envelope">
                    <span>{t("agent.semanticBoundary")}</span>
                    <b>
                      {item.response.intent.semantic_envelope.assertion_status}
                      {" · "}
                      {item.response.intent.semantic_envelope.effective_time}
                      {" · "}
                      {item.response.intent.semantic_envelope.event_type}
                    </b>
                    <small>{item.response.intent.semantic_envelope.requested_action}</small>
                  </div>
                )}
              </div>
            )}
          </article>
        ))}
      </div>

      <div className="v8-agent-progress">
        <span className="v8-kicker">{t("agent.recentUnderstanding")}</span>
        <div>
          <b>{t("agent.whatIfStudio")}</b>
          <span>{t("agent.whatIfStudioSub")}</span>
        </div>
        <div>
          <b>{t("agent.protected")}</b>
          <span>{t("agent.protectedSummary")}</span>
        </div>
      </div>
    </section>
  );
}

function formatMetric(
  record: Record<string, unknown>,
  cost: unknown,
  locale: "zh-CN" | "en-GB",
) {
  const currency = typeof record.currency === "string" ? record.currency : "CNY";
  const value = typeof cost === "number" ? formatMinorMoney(cost, currency, locale) : "—";
  const walking =
    typeof record.walking_min === "number" ? ` · ${record.walking_min} min walk` : "";
  return value + walking;
}
