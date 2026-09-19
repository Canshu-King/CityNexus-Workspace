import { useState } from "react";

type Draft = {
  id: string;
  artifact_type: string;
  extracted: Record<string, unknown>;
  unresolved_fields: string[];
  extraction_mode: string;
  status: string;
  confirmed_at?: string | null;
};

type Props = {
  journeyId: string;
  onConfirmed?: () => Promise<void>;
};

type ExtractionResponse = {
  status: string;
  provider?: string;
  reason?: string;
  draft?: Draft | null;
};

async function postJson<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const payload = (await response.json()) as T & { detail?: string };
  if (!response.ok) throw new Error(payload.detail ?? `Request failed (${response.status})`);
  return payload;
}

function readImage(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result));
    reader.onerror = () => reject(new Error("The image could not be read."));
    reader.readAsDataURL(file);
  });
}

export function JourneyInboxWorkbench({ journeyId, onConfirmed }: Props) {
  const [text, setText] = useState("");
  const [image, setImage] = useState<File | null>(null);
  const [draft, setDraft] = useState<Draft | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const showResult = (result: ExtractionResponse) => {
    if (result.draft) setDraft(result.draft);
    setMessage(
      result.status === "READY"
        ? "Draft extracted. Review every critical field before confirming."
        : result.status === "NOT_CONFIGURED"
          ? "DeepSeek extraction is not configured; deterministic import remains available."
          : result.reason ?? `Extraction status: ${result.status}`,
    );
  };

  const extractText = async () => {
    if (text.trim().length < 3) return;
    setBusy(true);
    try {
      showResult(
        await postJson<ExtractionResponse>(
          `/api/v1/journeys/${journeyId}/inbox/text-extract`,
          { text },
        ),
      );
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Text extraction failed.");
    } finally {
      setBusy(false);
    }
  };

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
      setMessage(error instanceof Error ? error.message : "Image extraction failed.");
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
      setMessage("Confirmed facts are now protected in the Travel Wallet.");
      await onConfirmed?.();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Confirmation failed.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="v10-inbox-workbench" aria-label="Journey Inbox extraction">
      <div className="v10-inbox-heading">
        <div>
          <span className="v8-kicker">MULTIMODAL INBOX</span>
          <h2>Bring a confirmation into the Journey</h2>
        </div>
        <span className="v10-truth-pill">draft first · confirm critical facts</span>
      </div>
      <div className="v10-inbox-inputs">
        <label>
          Pasted confirmation
          <textarea
            value={text}
            onChange={(event) => setText(event.target.value)}
            placeholder="Paste rail, flight, hotel, or venue confirmation text"
          />
          <button type="button" onClick={() => void extractText()} disabled={busy || text.trim().length < 3}>
            Extract text draft
          </button>
        </label>
        <label>
          Confirmation screenshot
          <input type="file" accept="image/*" onChange={(event) => setImage(event.target.files?.[0] ?? null)} />
          <small>{image ? image.name : "Image bytes are sent only for this extraction request."}</small>
          <button type="button" onClick={() => void extractImage()} disabled={busy || !image}>
            Extract image draft
          </button>
        </label>
      </div>
      {message && <p className="v10-inbox-message" role="status">{message}</p>}
      {draft && (
        <div className="v10-inbox-draft" data-testid="v10-inbox-draft">
          <div>
            <b>{draft.artifact_type} · {draft.status}</b>
            <small>{draft.extraction_mode}</small>
          </div>
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
              ? `Needs review: ${draft.unresolved_fields.join(", ")}`
              : "Critical fields resolved; confirm to protect this reservation."}
          </p>
          <button type="button" onClick={() => void confirm()} disabled={busy || Boolean(draft.unresolved_fields.length) || draft.status === "CONFIRMED"}>
            {draft.status === "CONFIRMED" ? "Confirmed" : "Confirm and protect"}
          </button>
        </div>
      )}
    </section>
  );
}
