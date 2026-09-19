import { useEffect, useState } from "react";
import { useT } from "../../i18n/LocaleContext";

type Draft = {
  id: string;
  artifact_type: string;
  extracted: Record<string, unknown>;
  interpretation?: {
    anchor_role?: string;
    anchor_role_confidence?: number | null;
    semantic_target?: Record<string, unknown> | null;
    payment_status?: string | null;
    reasoning_summary?: string | null;
  };
  smart_intake?: {
    decision?: string;
    reasons?: string[];
    conflicts?: string[];
    resolved_target?: {
      status?: string;
      label?: string;
      semantic_node_key?: string;
      confidence?: number | null;
    } | null;
    role_confidence?: number | null;
  };
  unresolved_fields: string[];
  extraction_mode: string;
  status: string;
  confirmed_at?: string | null;
};

type MemoryItem = {
  id: string;
  kind: string;
  role: string;
  title: string;
  label: string;
  at?: string | null;
  status: string;
  protected: boolean;
  confidence?: number | null;
  reasoning_summary?: string;
  semantic_node_key?: string | null;
};

type Memory = { title: string; items: MemoryItem[] };

type Props = {
  journeyId: string;
  decodedText?: string;
  onConfirmed?: () => Promise<void>;
};

type ExtractionResponse = {
  status: string;
  provider?: string;
  reason?: string;
  draft?: Draft | null;
};

type ApplyResponse = {
  status: string;
  decision?: string;
  draft?: Draft;
};

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, init);
  const payload = (await response.json()) as T & {
    detail?: string;
    error?: { message?: string };
  };
  if (!response.ok) {
    throw new Error(payload.error?.message ?? payload.detail ?? `Request failed (${response.status})`);
  }
  return payload;
}

async function postJson<T>(path: string, body: unknown): Promise<T> {
  return requestJson<T>(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

function readImage(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result));
    reader.onerror = () => reject(new Error("The image could not be read."));
    reader.readAsDataURL(file);
  });
}

function dateInput(value: unknown): string {
  return typeof value === "string" ? value.replace(/Z$/, "").slice(0, 16) : "";
}

function serverDate(value: string): string | undefined {
  if (!value) return undefined;
  return value.length === 16 ? `${value}:00+08:00` : value;
}

export function JourneyInboxWorkbench({ journeyId, decodedText, onConfirmed }: Props) {
  const t = useT();
  const [text, setText] = useState("");
  const [image, setImage] = useState<File | null>(null);
  const [draft, setDraft] = useState<Draft | null>(null);
  const [memory, setMemory] = useState<Memory | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [role, setRole] = useState("UNKNOWN");
  const [scheduledDeparture, setScheduledDeparture] = useState("");
  const [scheduledArrival, setScheduledArrival] = useState("");

  const confidence = (value: number | null | undefined): string =>
    typeof value === "number" ? t("inbox.confidence", { n: Math.round(value * 100) }) : t("inbox.confidencePending");

  const loadMemory = async () => {
    try {
      setMemory(await requestJson<Memory>(`/api/v1/journeys/${journeyId}/memory`));
    } catch (error) {
      setMessage(error instanceof Error ? error.message : t("inbox.memoryLoadError"));
    }
  };

  useEffect(() => {
    void loadMemory();
  }, [journeyId]);

  useEffect(() => {
    if (!draft) return;
    setRole(String(draft.extracted.anchor_role ?? "UNKNOWN"));
    setScheduledDeparture(dateInput(draft.extracted.scheduled_departure_at));
    setScheduledArrival(dateInput(draft.extracted.scheduled_arrival_at));
  }, [draft?.id]);

  const showResult = (result: ExtractionResponse) => {
    if (result.draft) setDraft(result.draft);
    setMessage(
      result.status === "READY"
        ? t("inbox.semanticReady")
        : result.status === "NOT_CONFIGURED"
          ? t("inbox.notConfigured")
          : result.reason ?? `${t("inbox.extractionStatus")} ${result.status}`,
    );
  };

  const extractText = async (value = text) => {
    if (value.trim().length < 3) return;
    setText(value);
    setBusy(true);
    try {
      showResult(
        await postJson<ExtractionResponse>(
          `/api/v1/journeys/${journeyId}/inbox/text-extract`,
          { text: value },
        ),
      );
    } catch (error) {
      setMessage(error instanceof Error ? error.message : t("inbox.textFailed"));
    } finally {
      setBusy(false);
    }
  };

  useEffect(() => {
    if (decodedText) void extractText(decodedText);
  }, [decodedText]);

  const extractImage = async () => {
    if (!image) return;
    setBusy(true);
    try {
      showResult(
        await postJson<ExtractionResponse>(
          `/api/v1/journeys/${journeyId}/inbox/vision`,
          { image_url: await readImage(image), hint: "rail, flight, hotel, or attraction confirmation" },
        ),
      );
    } catch (error) {
      setMessage(error instanceof Error ? error.message : t("inbox.imageFailed"));
    } finally {
      setBusy(false);
    }
  };

  const refreshAfterApply = async (result: ApplyResponse) => {
    if (result.draft) setDraft(result.draft);
    await loadMemory();
    await onConfirmed?.();
    setMessage(
      result.status === "APPLIED"
        ? t("inbox.semanticApplied")
        : t("inbox.stoppedAt", { step: result.status }) + t("inbox.correctHint"),
    );
  };

  const smartApply = async () => {
    if (!draft) return;
    setBusy(true);
    try {
      await refreshAfterApply(
        await postJson<ApplyResponse>(
          `/api/v1/journeys/${journeyId}/inbox/${draft.id}/smart-apply`,
          {},
        ),
      );
    } catch (error) {
      setMessage(error instanceof Error ? error.message : t("inbox.smartApplyFailed"));
    } finally {
      setBusy(false);
    }
  };

  const confirm = async () => {
    if (!draft || draft.unresolved_fields.length) return;
    setBusy(true);
    try {
      await postJson(`/api/v1/journeys/${journeyId}/inbox/${draft.id}/confirm`, {});
      setDraft({ ...draft, status: "CONFIRMED", confirmed_at: new Date().toISOString() });
      await loadMemory();
      await onConfirmed?.();
      setMessage(t("inbox.confirmedProtected"));
    } catch (error) {
      setMessage(error instanceof Error ? error.message : t("inbox.confirmFailed"));
    } finally {
      setBusy(false);
    }
  };

  const saveCorrections = async () => {
    if (!draft) return;
    setBusy(true);
    try {
      const patched = await requestJson<Draft>(
        `/api/v1/journeys/${journeyId}/inbox/${draft.id}`,
        {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            anchor_role: role,
            scheduled_departure_at: serverDate(scheduledDeparture),
            scheduled_arrival_at: serverDate(scheduledArrival),
          }),
        },
      );
      setDraft(patched);
      setMessage(t("inbox.correctionsSaved"));
    } catch (error) {
      setMessage(error instanceof Error ? error.message : t("inbox.correctionsFailed"));
    } finally {
      setBusy(false);
    }
  };

  const decision = draft?.smart_intake?.decision ?? "NEEDS_REVIEW";
  const target = draft?.interpretation?.semantic_target;
  const targetLabel = String(
    draft?.smart_intake?.resolved_target?.label ?? target?.resolved_label ?? target?.query ?? t("inbox.unboundTarget"),
  );
  const canSmartApply = Boolean(
    draft &&
      draft.status !== "CONFIRMED" &&
      !draft.unresolved_fields.length &&
      ["AUTO_APPLY", "APPLY_WITH_NOTICE"].includes(decision),
  );

  return (
    <section className="v10-inbox-workbench" aria-label={t("inbox.inboxExtraction")}>
      <div className="v10-inbox-heading">
        <div>
          <span className="v8-kicker">{t("inbox.multimodal")}</span>
          <h2>{t("inbox.bringConfirmation")}</h2>
        </div>
        <span className="v10-truth-pill">{t("inbox.semanticDraft")}</span>
      </div>
      <div className="v10-inbox-inputs">
        <label>
          {t("inbox.pastedConfirmation")}
          <textarea
            value={text}
            onChange={(event) => setText(event.target.value)}
            placeholder={t("inbox.pasteHint")}
          />
          <button type="button" onClick={() => void extractText()} disabled={busy || text.trim().length < 3}>
            {t("inbox.extractText")}
          </button>
        </label>
        <label>
          {t("inbox.screenshot")}
          <input type="file" accept="image/*" onChange={(event) => setImage(event.target.files?.[0] ?? null)} />
          <small>{image ? image.name : t("inbox.imageHint")}</small>
          <button type="button" onClick={() => void extractImage()} disabled={busy || !image}>
            {t("inbox.extractImage")}
          </button>
        </label>
      </div>
      {message && <p className="v10-inbox-message" role="status">{message}</p>}

      <section className="v13-2-memory-panel" data-testid="v13-2-memory" aria-label={t("inbox.journeyMemory")}>
        <div className="v10-inbox-heading">
          <div>
            <span className="v8-kicker">{t("inbox.authoritativeMemory")}</span>
            <h3>{memory?.title ?? t("inbox.journeyMemory")}</h3>
          </div>
          <small>{t("inbox.protectedFacts", { n: memory?.items.length ?? 0 })}</small>
        </div>
        {memory?.items.length ? (
          <ol>
            {memory.items.map((item) => (
              <li key={item.id}>
                <strong>{item.title} · {item.role}</strong>
                <span>{item.label} · {item.at ?? t("inbox.timePending")}</span>
                <small>{item.protected ? t("inbox.protected") : t("inbox.candidate")} · {confidence(item.confidence)}</small>
                {item.reasoning_summary && <p>{item.reasoning_summary}</p>}
              </li>
            ))}
          </ol>
        ) : (
          <p>{t("inbox.noArtifact")}</p>
        )}
      </section>

      {draft && (
        <div className="v10-inbox-draft" data-testid="v10-inbox-draft">
          <div>
            <b>{draft.artifact_type} · {draft.status}</b>
            <small>{draft.extraction_mode}</small>
          </div>
          <section className="v13-2-interpretation" data-testid="v13-2-interpretation">
            <b>{t("inbox.semanticInterpretation")}</b>
            <span>{draft.interpretation?.anchor_role ?? "UNKNOWN"} · {confidence(draft.interpretation?.anchor_role_confidence)}</span>
            <span>{t("inbox.target")} {targetLabel}</span>
            <span>{t("inbox.payment")} {String(draft.interpretation?.payment_status ?? "UNKNOWN")}</span>
            {draft.interpretation?.reasoning_summary && <p>{draft.interpretation.reasoning_summary}</p>}
          </section>
          <section className="v13-2-review" aria-label={t("inbox.reviewSemantic")}>
            <label>
              {t("inbox.anchorRole")}
              <select data-testid="v13-2-anchor-role" value={role} onChange={(event) => setRole(event.target.value)} disabled={draft.status === "CONFIRMED"}>
                <option value="UNKNOWN">{t("inbox.roleUnknown")}</option>
                <option value="ARRIVAL">{t("inbox.roleArrival")}</option>
                <option value="MID_TRIP">{t("inbox.roleMidTrip")}</option>
                <option value="DEPARTURE">{t("inbox.roleDeparture")}</option>
              </select>
            </label>
            <label>
              {t("inbox.scheduledDeparture")}
              <input type="datetime-local" value={scheduledDeparture} onChange={(event) => setScheduledDeparture(event.target.value)} disabled={draft.status === "CONFIRMED"} />
            </label>
            <label>
              {t("inbox.scheduledArrival")}
              <input type="datetime-local" value={scheduledArrival} onChange={(event) => setScheduledArrival(event.target.value)} disabled={draft.status === "CONFIRMED"} />
            </label>
            <button type="button" onClick={() => void saveCorrections()} disabled={busy || draft.status === "CONFIRMED"}>
              {t("inbox.saveCorrections")}
            </button>
          </section>
          <dl>
            {Object.entries(draft.extracted).slice(0, 8).map(([key, value]) => (
              <div key={key}>
                <dt>{key.replaceAll("_", " ")}</dt>
                <dd>{typeof value === "object" ? JSON.stringify(value) : String(value ?? "UNKNOWN")}</dd>
              </div>
            ))}
          </dl>
          <p className={draft.unresolved_fields.length ? "v10-inbox-warning" : "v10-inbox-clear"}>
            {draft.unresolved_fields.length
              ? `${t("inbox.needsReview")} ${draft.unresolved_fields.join(", ")}`
              : `${t("inbox.smartDecision")} ${decision} · ${targetLabel}`}
          </p>
          <button data-testid="v13-2-smart-apply" type="button" onClick={() => void smartApply()} disabled={busy || !canSmartApply}>
            {draft.status === "CONFIRMED" ? t("inbox.applied") : canSmartApply ? t("inbox.applySmart") : t("inbox.reviewRequired")}
          </button>
          <button type="button" onClick={() => void confirm()} disabled={busy || Boolean(draft.unresolved_fields.length) || draft.status === "CONFIRMED"}>
            {draft.status === "CONFIRMED" ? t("inbox.confirmed") : t("inbox.confirmProtect")}
          </button>
        </div>
      )}
    </section>
  );
}
