import { Icon } from "../../components/v8/Icon";
import { MapPanel } from "../../components/v8/MapPanel";
import type { V8Data } from "../../app/v8Types";
import { useT, useLocale } from "../../i18n/LocaleContext";
import { formatMinorMoney } from "../../lib/money";

export function StayExplorer({ data, selected, onSelect }: { data: V8Data; selected: V8Data["options"][number] | null; onSelect: (id: string) => void }) {
  const t = useT();
  const { locale } = useLocale();
  return <section className="v8-page" data-testid="v8-stay-explorer">
    <div className="v8-page-intro compact"><div><p className="v8-kicker">{t("stay.kicker")}</p><h1>{t("stay.title")}</h1><p className="v8-lede">{t("stay.lede")}</p></div><span className="v8-evidence-label"><span className="status-dot" />{t("stay.capturedReplay")}</span></div>
    <div className="v8-stay-layout">
      <div className="v8-stay-list">{data.options.slice(0, 4).map((item) => <article data-testid="stay-offer-card" className={item.id === data.selected_option_id ? "v8-stay-card selected" : "v8-stay-card"} key={item.id} onClick={() => onSelect(item.id)} onKeyDown={(event) => { if (event.key === "Enter") onSelect(item.id); }} role="button" tabIndex={0}>
        <div className="v8-hotel-thumb large"><Icon name="bed" /><span>TIANJIN</span></div>
        <div className="v8-stay-card-body"><div className="v8-stay-card-title"><div><span className="v8-rank">0{item.rank}</span><h3>{item.stay.property_name}</h3></div>{item.id === data.selected_option_id && <span className="v8-selected-label">{t("stay.selected")}</span>}</div><p>{item.stay.room_type} · {data.trip.party_size} travelers · {item.stay.refundable ? t("stay.freeCancel") : t("stay.nonRefundable")}</p><div className="v8-stay-price"><strong>{money(item.stay_total_minor, item.stay.currency, locale)}</strong><span>total · {money(item.stay.nightly_amount_minor, item.stay.currency, locale)}/{t("stay.nightly")}</span></div><div className="v8-stay-impact"><span>{t("stay.journeyImpact")}</span><b>{item.walking_min} min walk</b><b>{item.protected_margin_min} min slack</b><em>{item.leg_modes[0]}</em></div></div>
      </article>)}</div>
      <div className="v8-stay-detail"><MapPanel data={data} option={selected} /><div className="v8-detail-panel"><div><span>{t("stay.rateEvidence")}</span><b>{selected?.stay.property_name}</b></div><dl><div><dt>{t("stay.totalCurrency")}</dt><dd>{money(selected?.stay.total_amount_minor, selected?.stay.currency, locale)} · {selected?.stay.currency} explicit</dd></div><div><dt>{t("stay.checkInOut")}</dt><dd>{date(selected?.stay.check_in_at, locale)} → {date(selected?.stay.check_out_at, locale)}</dd></div><div><dt>{t("stay.cancellation")}</dt><dd>{selected?.stay.cancellation_policy.summary}</dd></div><div><dt>{t("stay.provider")}</dt><dd>captured hotel · {Math.round((selected?.stay.evidence.confidence ?? 0) * 100)}% confidence</dd></div></dl></div></div>
    </div>
  </section>;
}

function money(minor: number | null | undefined, currency = "CNY", locale = "en") { return formatMinorMoney(minor, currency, locale === "zh-CN" ? "zh-CN" : "en-US"); }
function date(value?: string, locale = "en") { return value ? new Intl.DateTimeFormat(locale === "zh-CN" ? "zh-CN" : "en-GB", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit", hour12: false }).format(new Date(value)) : "—"; }
