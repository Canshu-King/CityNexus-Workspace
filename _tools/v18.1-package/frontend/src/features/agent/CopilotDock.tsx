import { useEffect, useMemo, useState } from "react";
import type { V8Data } from "../../app/v8Types";
import { cityNexusApi, type CopilotResponse } from "../../api/citynexus";
import { useLocale, useT } from "../../i18n/LocaleContext";
import { AgentRunRail, type AgentRailStep } from "./AgentRunRail";

type Message = { role: "user" | "assistant"; text: string; response?: CopilotResponse };

export function CopilotDock({
  data,
  onNavigate,
}: {
  data: V8Data;
  onNavigate: (route: string) => void;
}) {
  const t = useT();
  const { locale } = useLocale();
  const [open, setOpen] = useState(false);
  const [draft, setDraft] = useState("");
  const [sending, setSending] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [lastRuntime, setLastRuntime] = useState("DIRECT");
  const activeRun = useMemo(
    () => [...messages].reverse().find((item) => item.response?.agent_run)?.response?.agent_run ?? null,
    [messages],
  );
  const [runState, setRunState] = useState<string | null>(null);
  const [runEvents, setRunEvents] = useState<Array<Record<string, unknown>>>([]);

  useEffect(() => {
    setRunState(activeRun?.status ?? null);
    setRunEvents([]);
    if (!activeRun?.events_url) return undefined;

    const source = new EventSource(activeRun.events_url);
    const handleEvent = (event: MessageEvent<string>) => {
      try {
        const payload = JSON.parse(event.data) as Record<string, unknown>;
        setRunEvents((current) => [...current.slice(-19), payload]);
        const nextState = String(payload.status ?? payload.state ?? payload.type ?? "");
        if (nextState) {
          setRunState(nextState);
          if (/^(completed|succeeded|failed|cancelled|stopped|error)$/i.test(nextState)) source.close();
        }
      } catch {
        source.close();
      }
    };
    source.addEventListener("message", handleEvent);
    source.onerror = () => source.close();
    return () => source.close();
  }, [activeRun?.events_url, activeRun?.run_id, activeRun?.status]);

  const localeCode = locale === "zh-CN" ? "zh" : "en";
  const steps = useMemo<AgentRailStep[]>(() => {
    if (!activeRun) return [];
    const terminal = /completed|succeeded|failed|cancelled|stopped|error/i.test(runState ?? activeRun.status);
    const label = (name: string) => ({ inspect_journey: "检查当前行程", inspect_twin: "检查 Journey Twin", search_city_services: "搜索候选地点", request_replan: "请求重规划方案" }[name] ?? name);
    return runEvents.map((event, index) => {
      const name = String(event.tool_name ?? event.tool ?? event.name ?? event.event_type ?? event.type ?? "Hermes event");
      const raw = String(event.event_type ?? event.type ?? "");
      const failed = /failed|error/i.test(raw) || event.status === "failed";
      const done = /completed|succeeded|finished/i.test(raw) || event.status === "completed";
      return { id: `${index}-${name}`, label: label(name), status: failed ? "failed" : done || terminal ? "done" : "active", detail: <small><code>{name}</code></small> };
    });
  }, [activeRun, locale, runEvents, runState]);

  const stopRun = async () => {
    if (!activeRun?.run_id) return;
    await cityNexusApi.stopNativeHermesRun(data.journey.id, activeRun.run_id);
    setRunState("stopped");
  };

  const send = async () => {
    const value = draft.trim();
    if (value.length < 2 || sending) return;
    setSending(true);
    setError(null);
    setDraft("");
    setMessages((current) => [...current, { role: "user", text: value }]);
    try {
      const response = await cityNexusApi.sendCopilotMessage(data.journey.id, value, localeCode);
      setLastRuntime(response.agent_run?.runtime_identity ?? "DIRECT");
      setMessages((current) => [...current, { role: "assistant", text: response.message, response }]);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : t("agent.sendError"));
    } finally {
      setSending(false);
    }
  };

  const continueAction = (action?: string) => {
    if (action === "REQUEST_PLACE_SEARCH") onNavigate("discover");
    if (action === "REQUEST_REPLAN") onNavigate("authoritative");
    if (action === "REQUEST_PREFERENCE_UPDATE") onNavigate("me");
  };

  return (
    <aside className={`cn-copilot-dock ${open ? "open" : "collapsed"}`} data-testid="v18-copilot-dock">
      {!open ? (
        <button className="cn-copilot-edge" type="button" onClick={() => setOpen(true)} aria-label={t("agent.citynexus")}>
          <span className="cn-copilot-edge-mark">✦</span>
          <span>{t("agent.citynexus")}</span>
          <i className="cn-copilot-status" />
        </button>
      ) : (
        <div className="cn-copilot-panel">
          <header className="cn-copilot-head">
            <div>
              <b>{t("agent.citynexus")}</b>
              <small>{locale === "zh-CN" ? "DeepSeek 理解 · 真实运行时" : "DeepSeek meaning · runtime truth"}</small>
            </div>
            <button type="button" className="cn-copilot-close" onClick={() => setOpen(false)} aria-label={t("shell.close")}>×</button>
          </header>
          <div className="cn-copilot-runtime">
            <span>{locale === "zh-CN" ? "Semantic" : "Semantic"}: DeepSeek</span>
            <span>{locale === "zh-CN" ? "Execution" : "Execution"}: {lastRuntime}</span>
            <span>Truth: CityNexus</span>
          </div>
          <div className="cn-copilot-history" aria-live="polite">
            {messages.length === 0 && <p className="cn-copilot-empty">{locale === "zh-CN" ? "问我为什么这样安排、试算变化，或报告已经确认的中断。" : "Ask why, preview a change, or report a confirmed disruption."}</p>}
            {messages.map((item, index) => (
              <article key={`${item.role}-${index}`} className={`cn-copilot-bubble ${item.role}`}>
                <small>{item.role === "user" ? (locale === "zh-CN" ? "你" : "You") : "CityNexus"}</small>
                <p>{item.text}</p>
                {item.response?.intent && <span className="cn-copilot-chip">{item.response.intent.name}</span>}
                {item.response?.verification && <span className="cn-copilot-chip">{item.response.verification.status}</span>}
                {item.response?.action?.type && <button type="button" className="cn-copilot-link" onClick={() => continueAction(item.response?.action?.type)}>{item.response.action.type}</button>}
              </article>
            ))}
          </div>
          {activeRun?.runtime_identity === "HERMES_NATIVE_MCP" && steps.length > 0 && <AgentRunRail steps={steps} />}
          {activeRun?.runtime_identity === "HERMES_NATIVE_MCP" && !/completed|succeeded|failed|cancelled|stopped|error/i.test(runState ?? activeRun.status) && <button type="button" className="cn-copilot-stop" onClick={() => void stopRun()}>Stop</button>}
          {error && <p className="cn-copilot-error" role="alert">{error}</p>}
          <form className="cn-copilot-form" onSubmit={(event) => { event.preventDefault(); void send(); }}>
            <textarea value={draft} onChange={(event) => setDraft(event.target.value)} placeholder={t("agent.inputPlaceholder")} aria-label={t("agent.message")} rows={2} />
            <button className="v8-primary" type="submit" disabled={sending || draft.trim().length < 2}>{sending ? t("agent.working") : t("agent.send")}</button>
          </form>
        </div>
      )}
    </aside>
  );
}
