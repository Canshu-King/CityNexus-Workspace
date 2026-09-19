import { useMemo, useState } from "react";
import { useLocale, useT } from "../../i18n/LocaleContext";

export type JourneyTrialDraft = {
  cityName: string;
  countryCode: string;
  timezone: string;
  startAt: string;
  endAt: string;
  arrivalLocation: string;
  departureLocation: string;
  budgetMajor: number;
  stayBudgetMajor: number;
  currency: string;
  partySize: number;
  rooms: number;
};

export function suggestedRoomCount(partySize: number): number {
  if (partySize <= 2) return 1;
  if (partySize <= 4) return 2;
  if (partySize <= 6) return 3;
  return Math.max(3, Math.ceil(partySize / 3));
}

function futureLocalAt(dayOffset: number, hour: number) {
  const value = new Date();
  value.setDate(value.getDate() + dayOffset);
  value.setHours(hour, 0, 0, 0);
  const local = new Date(value.getTime() - value.getTimezoneOffset() * 60_000);
  return local.toISOString().slice(0, 16);
}

function localDateTimeInZoneToIso(value: string, timeZone: string) {
  const [datePart, timePart] = value.split("T");
  const [year, month, day] = datePart.split("-").map(Number);
  const [hour, minute] = timePart.split(":").map(Number);
  const localMs = Date.UTC(year, month - 1, day, hour, minute);
  let instantMs = localMs;
  const formatter = new Intl.DateTimeFormat("en-US", {
    timeZone,
    calendar: "iso8601",
    numberingSystem: "latn",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hourCycle: "h23",
  });
  for (let attempt = 0; attempt < 2; attempt += 1) {
    const parts = Object.fromEntries(
      formatter.formatToParts(new Date(instantMs)).map(({ type, value: part }) => [type, part]),
    );
    const displayedMs = Date.UTC(
      Number(parts.year),
      Number(parts.month) - 1,
      Number(parts.day),
      Number(parts.hour),
      Number(parts.minute),
      Number(parts.second),
    );
    instantMs += localMs - displayedMs;
  }
  return new Date(instantMs).toISOString();
}

export function JourneyTrialSetup({
  onCreate,
  onUseTianjinDemo,
  onCancel,
  busy,
}: {
  onCreate: (draft: JourneyTrialDraft) => Promise<void>;
  onUseTianjinDemo: () => Promise<void>;
  onCancel?: () => void;
  busy: boolean;
}) {
  const t = useT();
  const { locale, switchLocale } = useLocale();
  const browserTimezone = useMemo(
    () => Intl.DateTimeFormat().resolvedOptions().timeZone || "Asia/Shanghai",
    [],
  );
  const [draft, setDraft] = useState<JourneyTrialDraft>({
    cityName: "",
    countryCode: "CN",
    timezone: browserTimezone,
    startAt: futureLocalAt(1, 10),
    endAt: futureLocalAt(3, 20),
    arrivalLocation: "",
    departureLocation: "",
    budgetMajor: 2000,
    stayBudgetMajor: 900,
    currency: "CNY",
    partySize: 1,
    rooms: 1,
  });
  const [roomsTouched, setRoomsTouched] = useState(false);
  const update = <K extends keyof JourneyTrialDraft>(key: K, value: JourneyTrialDraft[K]) =>
    setDraft((current) => ({ ...current, [key]: value }));
  const valid =
    draft.cityName.trim().length >= 2 &&
    draft.arrivalLocation.trim().length >= 2 &&
    draft.departureLocation.trim().length >= 2 &&
    draft.startAt &&
    draft.endAt &&
    new Date(draft.endAt).getTime() > new Date(draft.startAt).getTime();

  return (
    <main className="v8-trial-setup" data-testid="trial-setup">
      <header className="v8-trial-setup-head">
        <div className="v8-brand">
          <div className="v8-brand-mark">CN</div>
          <div><strong>CityNexus</strong><span>{t("shell.tagline")}</span></div>
        </div>
        <button
          className="v9-language v8-trial-language"
          data-testid="trial-language"
          aria-label="Switch language"
          onClick={switchLocale}
        >
          {t("nav.language")}
        </button>
      </header>
      <section className="v8-trial-card">
        <div className="v8-trial-copy">
          <p className="v8-kicker">{t("trial.kicker")}</p>
          <h1>{t("trial.title")}</h1>
          <p className="v8-lede">{t("trial.lede")}</p>
          <div className="v8-trial-notice">
            <b>{t("trial.liveTitle")}</b>
            <span>{t("trial.liveNote")}</span>
          </div>
          <button
            className="v8-outline-button"
            data-testid="trial-tianjin-demo"
            disabled={busy}
            onClick={() => void onUseTianjinDemo()}
          >
            {t("trial.tianjinDemo")}
          </button>
        </div>
        <form
          className="v8-trial-form"
          onSubmit={(event) => {
            event.preventDefault();
            if (valid && !busy) void onCreate(draft);
          }}
        >
          <label>{t("trial.city")}<input data-testid="trial-city" value={draft.cityName} onChange={(event) => update("cityName", event.target.value)} placeholder={locale === "zh-CN" ? "例如：福州、北京、上海" : "e.g. Fuzhou, Beijing, Shanghai"} /></label>
          <div className="v8-trial-row">
            <label>{t("trial.country")}<input data-testid="trial-country" value={draft.countryCode} onChange={(event) => update("countryCode", event.target.value.toUpperCase().slice(0, 3))} /></label>
            <label>{t("trial.timezone")}<input data-testid="trial-timezone" value={draft.timezone} onChange={(event) => update("timezone", event.target.value)} /></label>
          </div>
          <div className="v8-trial-row">
            <label>{t("trial.start")}<input data-testid="trial-start" type="datetime-local" value={draft.startAt} onChange={(event) => update("startAt", event.target.value)} /></label>
            <label>{t("trial.end")}<input data-testid="trial-end" type="datetime-local" value={draft.endAt} onChange={(event) => update("endAt", event.target.value)} /></label>
          </div>
          <label>{t("trial.arrival")}<input data-testid="trial-arrival" value={draft.arrivalLocation} onChange={(event) => update("arrivalLocation", event.target.value)} placeholder={locale === "zh-CN" ? "例如：福州站" : "e.g. Fuzhou Railway Station"} /></label>
          <label>{t("trial.departure")}<input data-testid="trial-departure" value={draft.departureLocation} onChange={(event) => update("departureLocation", event.target.value)} placeholder={locale === "zh-CN" ? "例如：福州站" : "e.g. Fuzhou Railway Station"} /></label>
          <div className="v8-trial-row three">
            <label>{t("trial.budget")}<input type="number" min="0" value={draft.budgetMajor} onChange={(event) => update("budgetMajor", Number(event.target.value))} /></label>
            <label>{t("trial.currency")}<input value={draft.currency} onChange={(event) => update("currency", event.target.value.toUpperCase().slice(0, 3))} /></label>
            <label>{t("trial.party")}<input type="number" min="1" max="20" value={draft.partySize} onChange={(event) => { const partySize = Number(event.target.value); setDraft((current) => ({ ...current, partySize, ...(roomsTouched ? {} : { rooms: suggestedRoomCount(partySize) }) })); }} /></label>
            <label>{t("trial.rooms")}<input type="number" min="1" max="20" value={draft.rooms} onChange={(event) => { setRoomsTouched(true); update("rooms", Number(event.target.value)); }} /></label>
          </div>
          <label>{t("trial.stayBudget")}<input type="number" min="0" value={draft.stayBudgetMajor} onChange={(event) => update("stayBudgetMajor", Number(event.target.value))} /></label>
          <div className="v8-trial-actions">
            {onCancel && <button type="button" className="v8-quiet-button" onClick={onCancel}>{t("trial.cancel")}</button>}
            <button className="v8-primary" data-testid="trial-create" disabled={!valid || busy} type="submit">
              {busy ? t("trial.creating") : t("trial.create")}
            </button>
          </div>
        </form>
      </section>
    </main>
  );
}

export { localDateTimeInZoneToIso };
