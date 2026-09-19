import { Icon } from "../../components/v8/Icon";
import type { V8Data } from "../../app/v8Types";
import type { TravelerCapability } from "../../api/citynexus";
import { useT } from "../../i18n/LocaleContext";

function capabilityLabel(item: TravelerCapability): string {
  const params = item.params ?? {};
  const suffix = typeof params.max_m === "number" ? ` · ${params.max_m} m` : typeof params.max_min === "number" ? ` · ${params.max_min} min` : "";
  return `${item.code}${suffix}`;
}

function CapabilityList({ items }: { items: TravelerCapability[] }) {
  if (!items.length) return <p className="v8-empty-note">No explicit capability facts recorded.</p>;
  return <ul className="v8-capability-list">{items.map((item) => <li key={`${item.scope}:${item.code}`}><strong>{capabilityLabel(item)}</strong><span>{item.severity}</span><small>{item.confirmed ? "Confirmed by traveler" : "Stated; confirmation needed"}</small></li>)}</ul>;
}

export function TwinPanel({ data }: { data: V8Data }) {
  const t = useT();
  const explicit = data.traveler_twin?.explicit_dimensions ?? [];
  const learned = data.traveler_twin?.learned_soft_dimensions ?? [];
  const capabilities = data.traveler_twin?.explicit_capabilities ?? [];
  const hard = capabilities.filter((item) => item.severity === "HARD");
  const softer = capabilities.filter((item) => item.severity !== "HARD");
  return <section className="v8-page"><div className="v8-page-intro compact"><div><p className="v8-kicker">{t("twin.kicker")}</p><h1>{t("twin.title")}</h1><p className="v8-lede">{t("twin.lede")}</p></div></div><div className="v8-twin-grid"><article className="v8-twin-card"><span className="v8-twin-label explicit">{t("twin.explicit")}</span><h2>{explicit.length ? explicit.join(" · ") : "No explicit preferences"}</h2><p>{t("twin.explicitFrom")}</p><small>{t("twin.explicitSub")}</small><h3 className="v8-capability-heading">Capability needs</h3><CapabilityList items={capabilities} /></article><article className="v8-twin-card"><span className="v8-twin-label learned">{t("twin.learned")}</span><h2>{learned.length ? learned.join(" · ") : "No learned signals"}</h2><p>{t("twin.learnedFrom")}</p><small>{t("twin.learnedSub")}</small><h3 className="v8-capability-heading">Learned capability state</h3><p>{hard.length ? `${hard.length} hard need(s) remain explicit and are never learned.` : "Hard accessibility needs are never inferred from behavior."}</p>{softer.length ? <CapabilityList items={softer} /> : null}</article><aside className="v8-boundary-card"><Icon name="spark" /><b>{t("twin.authorityBoundary")}</b><p>{t("twin.boundarySub")}</p><span>{t("twin.provenance")}</span><small className="v8-capability-disclosure">Unknown accessibility evidence is not accessible.</small></aside></div></section>;
}
