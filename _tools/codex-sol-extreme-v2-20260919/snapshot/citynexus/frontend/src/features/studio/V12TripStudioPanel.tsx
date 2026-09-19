import { useEffect, useMemo, useState } from "react";
import { AlertTriangle, CheckCircle2, LockKeyhole, WandSparkles } from "lucide-react";
import {
  useAcceptTripStudioEdit,
  useTripStudioPreview,
  type PlanVersion,
  type TripStudioPreview,
} from "../../api/v12Authoritative";
import { ImpactPreview } from "../execution/V12StatePrimitives";
import { SortableActivityList } from "./SortableActivityList";
import { useT } from "../../i18n/LocaleContext";

type Props = {
  journeyId: string;
  plan: PlanVersion;
  onAccepted?: () => void;
};

export function V12TripStudioPanel({ journeyId, plan, onAccepted }: Props) {
  const t = useT();
  const initialOrder = useMemo(() => plan.activities.map((item) => item.id), [plan.activities]);
  const [draftOrder, setDraftOrder] = useState(initialOrder);
  const [preview, setPreview] = useState<TripStudioPreview | null>(null);
  const previewMutation = useTripStudioPreview(journeyId);
  const acceptMutation = useAcceptTripStudioEdit(journeyId);
  const names = useMemo(
    () => new Map(plan.activities.map((item) => [item.id, item.title])),
    [plan.activities],
  );
  const labels = useMemo(
    () => Object.fromEntries(names.entries()),
    [names],
  );
  const changed = draftOrder.some((id, index) => id !== initialOrder[index]);
  const protectedCount = plan.activities.filter((item) => item.locked).length;

  useEffect(() => {
    setDraftOrder(initialOrder);
    setPreview(null);
  }, [initialOrder, plan.id]);

  const previewDraft = async () => {
    const next = await previewMutation.mutateAsync({ activity_ids: draftOrder, draft_order: draftOrder });
    setPreview(next);
  };

  const acceptDraft = async () => {
    if (!preview?.can_accept) return;
    await acceptMutation.mutateAsync({ activity_ids: draftOrder, preview_id: preview.preview_id });
    setPreview(null);
    onAccepted?.();
  };

  return (
    <section className="v12-trip-studio" data-testid="v12-trip-studio">
      <header className="v12-panel-header">
        <div>
          <span className="v8-kicker">{t("studio.v12Kicker")}</span>
          <h2>{t("studio.v12Title")}</h2>
          <p className="v8-muted">{t("studio.v12Sub")}</p>
        </div>
        <span className="v12-evidence-badge"><WandSparkles size={14} /> {plan.mobility_snapshot_id ? t("studio.sameEvidence") : t("studio.evidencePending")}</span>
      </header>
      <div className="v12-studio-meta">
        <span>{t("fmt.activities", { n: plan.activities.length })}</span>
        <span>{t("fmt.protectedAnchors", { n: protectedCount })}</span>
        <span>{changed ? t("studio.draftDiffers") : t("studio.noDraft")}</span>
      </div>
      <SortableActivityList
        activities={draftOrder}
        labels={labels}
        protectedFirst={Boolean(plan.activities[0]?.locked)}
        onDraft={(next) => {
          setDraftOrder(next);
          setPreview(null);
        }}
      />
      <div className="v12-studio-legend">
        <span><LockKeyhole size={13} /> {t("studio.lockedLegend")}</span>
        <span>{t("studio.previewLegend")}</span>
      </div>
      {preview && (
        <div data-testid="v12-impact-preview">
          <ImpactPreview
            passed={preview.can_accept}
            summary={preview.can_accept ? t("studio.impactPass") : t("studio.impactFail")}
          />
          {!preview.can_accept && <p className="v12-studio-error"><AlertTriangle size={14} /> {String((preview.deterministic_gate as { failures?: string[] }).failures?.join(", ") ?? t("studio.gateFailed"))}</p>}
          {preview.can_accept && <p className="v12-studio-success"><CheckCircle2 size={14} /> {t("studio.readyNext")}</p>}
          <small className="v8-muted" data-testid="v13-frozen-evidence-summary">
            {t("studio.frozenEvidence")} {preview.evidence_snapshot_id ?? "pending"} · cost Δ {String((preview.impact as { cost_delta_minor?: number }).cost_delta_minor ?? 0)} · time Δ {String((preview.impact as { time_delta_min?: number }).time_delta_min ?? 0)} min
          </small>
        </div>
      )}
      <footer className="v12-panel-footer">
        <span>PlanVersion {plan.version_no} · {plan.source}</span>
        <div className="v12-studio-actions">
          <button className="v8-outline-button" type="button" disabled={!changed || previewMutation.isPending} onClick={() => void previewDraft()}>
            {previewMutation.isPending ? t("studio.checking") : t("studio.previewImpact")}
          </button>
          <button className="v8-primary" type="button" disabled={!preview?.can_accept || acceptMutation.isPending} onClick={() => void acceptDraft()}>
            {acceptMutation.isPending ? t("studio.accepting") : t("studio.acceptEdit")}
          </button>
        </div>
      </footer>
      {(previewMutation.error || acceptMutation.error) && <p className="v12-studio-error"><AlertTriangle size={14} /> {(previewMutation.error ?? acceptMutation.error)?.message}</p>}
    </section>
  );
}
