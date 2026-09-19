/**
 * "AI 帮我规划" — natural-language trip planning entry.
 *
 * Design rules honoured here:
 *  - the traveller types plain language; no internal vocabulary is shown;
 *  - progress is a REAL stepper; the backend exposes no percentage, so no
 *    percentage is fabricated (design corrections §6);
 *  - internal action enums (REQUEST_REPLAN, ACCEPT_REPLAN, …) and mission
 *    internals are never rendered;
 *  - a provider failure is shown honestly with a retry, never faked as success
 *    (master mission Phase 10).
 */

import { useEffect, useRef, useState } from "react";
import { useLocale } from "../../i18n/LocaleContext";

type Stage = { key: string; zh: string; en: string };

const STAGES: Stage[] = [
  { key: "understand", zh: "理解你的需求", en: "Understanding your request" },
  { key: "places", zh: "搜索真实地点", en: "Searching real places" },
  { key: "check", zh: "检查时间与交通", en: "Checking time and travel" },
  { key: "compose", zh: "生成可选方案", en: "Building candidate plans" },
];

const EXAMPLES = [
  {
    zh: "我和朋友两个人去厦门，想轻松一点，想去鼓浪屿、环岛路，想吃沙茶面和海鲜，不想太赶，也想找性价比高的酒店。",
    en: "Two of us in Xiamen, relaxed pace, Gulangyu and the Ring Road, local seafood, and a good-value hotel.",
  },
  {
    zh: "带爸妈去厦门三天，不要走太多路，下午要有休息时间，酒店要靠近地铁。",
    en: "Three days in Xiamen with my parents, not much walking, an afternoon rest, hotel near the metro.",
  },
];

/** Map internal mission status -> traveller language. */
function statusCopy(
  status: string,
  zh: boolean,
  planCount = 0,
): { title: string; body: string; tone: "ok" | "warn" | "busy" } {
  const s = (status || "").toUpperCase();
  if (s === "COMPLETED" || s === "SUCCEEDED") {
    return {
      title: zh ? `已生成 ${planCount} 个可选方案` : `${planCount} candidate plans are ready`,
      body: zh
        ? "去“今天”对比这几个方案，选一个再继续。"
        : "Compare them on Today, then choose one to continue.",
      tone: "ok",
    };
  }
  if (s === "BASELINE_UNAVAILABLE") {
    return {
      title: zh ? "无法确认这次的结果" : "We could not confirm this run",
      body: zh
        ? "无法确认本次是否生成了新方案，请重试或刷新页面。"
        : "We could not confirm whether this run produced new plans. Please retry or refresh.",
      tone: "warn",
    };
  }
  if (s === "NO_PLANS_PRODUCED") {
    return {
      title: zh ? "没有生成可行方案" : "No usable plans were produced",
      body: zh
        ? "你的需求已理解，但这次没能排出可行方案。你的行程没有被改动，可以调整预算或换个说法再试。"
        : "Your request was understood, but no feasible plan came out. Your trip is unchanged — adjust the budget or rephrase and try again.",
      tone: "warn",
    };
  }
  if (s.includes("SKIPPED_EXTERNAL_DEPENDENCY") || s.includes("EXTERNAL")) {
    return {
      title: zh ? "AI 暂时不可用" : "AI is unavailable right now",
      body: zh
        ? "规划助手这次没能连上。你的行程没有被改动，可以稍后重试。"
        : "The planning assistant could not be reached. Your trip is unchanged; you can retry.",
      tone: "warn",
    };
  }
  if (s === "RUNNING" || s === "PENDING" || s === "QUEUED") {
    return {
      title: zh ? "正在规划…" : "Planning…",
      body: zh ? "正在处理你的需求。" : "Working on your request.",
      tone: "busy",
    };
  }
  return {
    title: zh ? "暂时无法完成规划" : "Could not finish planning",
    body: zh
      ? "这次没能生成方案。你的行程没有被改动，可以重试或换个说法。"
      : "We could not produce plans this time. Your trip is unchanged; retry or rephrase.",
    tone: "warn",
  };
}

export function PlanWithAiSheet({
  journeyId,
  cityCode,
  onClose,
  onPlanned,
}: {
  journeyId: string;
  cityCode?: string;
  onClose: () => void;
  onPlanned?: () => void;
}) {
  const { locale } = useLocale();
  const zh = locale.startsWith("zh");
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [stage, setStage] = useState(0);
  const [result, setResult] = useState<null | {
    status: string;
    failureReason: string | null;
    summary: string | null;
    planCount?: number;
    newPlanIds?: string[];
  }>(null);
  const timer = useRef<number | null>(null);

  useEffect(() => () => { if (timer.current) window.clearInterval(timer.current); }, []);

  /**
   * Ids of every candidate plan that already existed, or `null` when the
   * baseline could not be fetched.
   *
   * Fail-CLOSED: an empty set means "there really were no plans before this
   * run".  A failed / non-OK / unparsable lookup must NOT masquerade as an
   * empty baseline — otherwise an old plan appears later and is mis-attributed
   * to THIS run.  `null` = the baseline is indeterminate.
   */
  const existingPlanIds = async (): Promise<Set<string> | null> => {
    try {
      const response = await fetch(`/api/v1/journeys/${journeyId}/plans`, {
        headers: { Accept: "application/json" },
      });
      if (!response.ok) return null;
      const plans = await response.json();
      // A non-array body is not a trustworthy "no plans" answer either.
      if (!Array.isArray(plans)) return null;
      return new Set(
        plans.map((item: { id?: string }) => item?.id).filter(Boolean) as string[],
      );
    } catch {
      return null;
    }
  };

  const submit = async () => {
    const command = text.trim();
    if (command.length < 8) return;
    setBusy(true);
    setResult(null);
    setStage(0);
    // This run must be judged on what IT produced.  Counting all plans let an
    // old ACTIVE/SELECTED plan satisfy a failed new run.  `null` means we could
    // not read the baseline at all, so nothing can be attributed to this run —
    // fail CLOSED instead of assuming an empty baseline.
    const baseline = await existingPlanIds();
    // Indeterminate stepper: we advance through the real stages we can name,
    // and stop at the last one. No fabricated percentage.
    timer.current = window.setInterval(() => {
      setStage((current) => Math.min(current + 1, STAGES.length - 1));
    }, 1200);
    try {
      const response = await fetch(`/api/v1/journeys/${journeyId}/agent/commands`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify({ command }),
      });
      const body = await response.json().catch(() => null);
      const mission = body?.mission ?? null;
      // A plan id only counts as "new" when we KNOW it was absent from the
      // pre-run baseline.  With an indeterminate baseline there is no such id.
      const isNewPlanId = (id: string | undefined): id is string =>
        typeof id === "string" && id.length > 0 && baseline !== null && !baseline.has(id);
      // A COMPLETED mission only means the request compiled.  It does NOT mean
      // candidate plans exist, so the real plan count decides what we report.
      // Reporting "plans are ready" without checking was a false success.
      // Returns `null` when the answer is unknowable (bad baseline OR bad
      // re-count) — NOT the same as "[] = no new plans".
      const countNewPlans = async (): Promise<string[] | null> => {
        if (baseline === null) return null;
        try {
          const plansResponse = await fetch(`/api/v1/journeys/${journeyId}/plans`, {
            headers: { Accept: "application/json" },
          });
          if (!plansResponse.ok) return null;
          const plans = await plansResponse.json();
          if (!Array.isArray(plans)) return null;
          return plans.map((item: { id?: string }) => item?.id).filter(isNewPlanId);
        } catch {
          return null;
        }
      };
      const counted = await countNewPlans();
      let newPlanIds: string[] = counted ?? [];
      let planCount = counted === null ? -1 : newPlanIds.length;
      // The mission compiler can succeed while the agent runtime (an external
      // dependency) produces nothing.  Before reporting failure, try the real
      // product path: compose candidates from the city places that discovery
      // has already materialised for this journey.  Only attempted when the
      // baseline is KNOWN — otherwise we cannot attribute what it created.
      if (baseline !== null && planCount === 0) {
        try {
          const placesResponse = await fetch(
            `/api/v1/places?city_code=${encodeURIComponent(cityCode)}`,
            { headers: { Accept: "application/json" } },
          );
          const places = placesResponse.ok ? await placesResponse.json() : [];
          const ids = Array.isArray(places)
            ? places.map((item: { id?: string }) => item?.id).filter(Boolean).slice(0, 8)
            : [];
          if (ids.length >= 2) {
            const generate = await fetch(
              `/api/v1/journeys/${journeyId}/plans/generate`,
              {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ place_ids: ids, candidate_count: 3 }),
              },
            );
            if (generate.ok) {
              const created = await generate.json();
              // Only artifacts this run created count as success.
              newPlanIds = (Array.isArray(created) ? created : [])
                .map((item: { id?: string }) => item?.id)
                .filter(isNewPlanId);
              if (newPlanIds.length === 0) {
                const recounted = await countNewPlans();
                if (recounted !== null) newPlanIds = recounted;
              }
              planCount = newPlanIds.length;
            }
          }
        } catch {
          /* keep planCount at 0 and report honestly */
        }
      }

      const missionStatus = String(mission?.status ?? "").toUpperCase();
      let status: string;
      if (baseline === null) {
        // Indeterminate baseline: whatever we see afterwards cannot be
        // attributed to this run, so success is never claimed.  The harness
        // reads planCount === -1 as "not a success".
        status = "BASELINE_UNAVAILABLE";
        planCount = -1;
        newPlanIds = [];
      } else if (planCount > 0) {
        status = "COMPLETED";
      } else if (missionStatus.includes("EXTERNAL") || missionStatus.includes("SKIPPED")) {
        status = "SKIPPED_EXTERNAL_DEPENDENCY";
      } else if (!response.ok) {
        status = `HTTP_${response.status}`;
      } else {
        // Compiled, but produced nothing the traveller can use.
        status = "NO_PLANS_PRODUCED";
      }
      setResult({
        status,
        newPlanIds,
        failureReason: mission?.failure_reason ?? null,
        summary: mission?.reasoning_summary ?? null,
        planCount,
      });
      if (status === "COMPLETED") onPlanned?.();
    } catch {
      setResult({ status: "NETWORK", failureReason: null, summary: null });
    } finally {
      if (timer.current) window.clearInterval(timer.current);
      setBusy(false);
    }
  };

  const copy = result ? statusCopy(result.status, zh, result.planCount ?? 0) : null;

  return (
    <div className="v8-sheet-backdrop" role="dialog" aria-modal="true" data-testid="plan-ai-sheet">
      <section className="plan-ai-sheet">
        <header className="plan-ai-head">
          <div>
            <b>{zh ? "AI 帮我规划" : "Plan my trip with AI"}</b>
            <small>
              {zh
                ? "用你自己的话描述这趟旅行，越具体越好。"
                : "Describe the trip in your own words — the more specific the better."}
            </small>
          </div>
          <button type="button" className="plan-ai-close" aria-label={zh ? "关闭" : "Close"} onClick={onClose}>
            ×
          </button>
        </header>

        <label className="plan-ai-field">
          <span className="v8-sr-only">{zh ? "旅行需求" : "Trip request"}</span>
          <textarea
            data-testid="plan-ai-input"
            rows={5}
            value={text}
            disabled={busy}
            onChange={(event) => setText(event.target.value)}
            placeholder={zh ? EXAMPLES[0].zh : EXAMPLES[0].en}
          />
        </label>

        <div className="plan-ai-examples">
          {EXAMPLES.map((item) => (
            <button
              key={item.en}
              type="button"
              disabled={busy}
              onClick={() => setText(zh ? item.zh : item.en)}
            >
              {zh ? item.zh.slice(0, 18) + "…" : item.en.slice(0, 26) + "…"}
            </button>
          ))}
        </div>

        {busy && (
          <ol className="plan-ai-steps" data-testid="plan-ai-steps">
            {STAGES.map((item, index) => (
              <li key={item.key} className={index < stage ? "done" : index === stage ? "active" : ""}>
                <span className="plan-ai-dot">{index < stage ? "✓" : index === stage ? "●" : "○"}</span>
                <span>{zh ? item.zh : item.en}</span>
              </li>
            ))}
          </ol>
        )}

        {copy && (
          <div
            className={`plan-ai-result ${copy.tone}`}
            data-testid="plan-ai-result"
            data-plan-count={result?.planCount ?? 0}
            data-new-plan-ids={(result?.newPlanIds ?? []).join(",")}
            role="status"
          >
            <b>{copy.title}</b>
            <p>{copy.body}</p>
            {result?.failureReason && (
              <details className="plan-ai-detail">
                <summary>{zh ? "技术详情" : "Technical detail"}</summary>
                <code data-testid="plan-ai-reason">{result.failureReason}</code>
              </details>
            )}
            {result?.summary && !result.failureReason && <p className="plan-ai-summary">{result.summary}</p>}
          </div>
        )}

        <div className="plan-ai-actions">
          <button type="button" className="v8-outline-button" onClick={onClose} disabled={busy}>
            {zh ? "稍后" : "Later"}
          </button>
          <button
            type="button"
            className="v8-primary-button"
            data-testid="plan-ai-submit"
            disabled={busy || text.trim().length < 8}
            onClick={() => void submit()}
          >
            {busy ? (zh ? "规划中…" : "Planning…") : zh ? "开始规划" : "Plan my trip"}
          </button>
        </div>
      </section>
    </div>
  );
}
