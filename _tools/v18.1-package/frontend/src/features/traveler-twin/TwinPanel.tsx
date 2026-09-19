import { Icon } from "../../components/v8/Icon";
import type { V8Data } from "../../app/v8Types";
import { useT } from "../../i18n/LocaleContext";

export function TwinPanel({ data }: { data: V8Data }) {
  const t = useT();
  const explicit = data.traveler_twin?.explicit_dimensions ?? ["low_walking"];
  const learned = data.traveler_twin?.learned_soft_dimensions ?? ["indoor_stops"];
  return <section className="v8-page"><div className="v8-page-intro compact"><div><p className="v8-kicker">{t("twin.kicker")}</p><h1>{t("twin.title")}</h1><p className="v8-lede">{t("twin.lede")}</p></div></div><div className="v8-twin-grid"><article className="v8-twin-card"><span className="v8-twin-label explicit">{t("twin.explicit")}</span><h2>{explicit.join(" · ")}</h2><p>{t("twin.explicitFrom")}</p><div className="v8-strength"><span style={{ width: "88%" }} /><b>0.88</b></div><small>{t("twin.explicitSub")}</small></article><article className="v8-twin-card"><span className="v8-twin-label learned">{t("twin.learned")}</span><h2>{learned.join(" · ")}</h2><p>{t("twin.learnedFrom")}</p><div className="v8-strength learned"><span style={{ width: "42%" }} /><b>0.42</b></div><small>{t("twin.learnedSub")}</small></article><aside className="v8-boundary-card"><Icon name="spark" /><b>{t("twin.authorityBoundary")}</b><p>{t("twin.boundarySub")}</p><span>{t("twin.provenance")}</span></aside></div></section>;
}
