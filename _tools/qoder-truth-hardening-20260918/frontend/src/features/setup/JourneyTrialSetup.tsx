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
  /** Optional planning brief captured in step 2. */
  pace?: string;
  interests?: string[];
  specialRequirements?: string;
};

/** City -> (country, timezone, currency) so a normal user never has to type them. */
const CITY_FACTS: Record<string, { country: string; timezone: string; currency: string; labelZh: string; labelEn: string }> = {
  "厦门": { country: "CN", timezone: "Asia/Shanghai", currency: "CNY", labelZh: "中国", labelEn: "China" },
  xiamen: { country: "CN", timezone: "Asia/Shanghai", currency: "CNY", labelZh: "中国", labelEn: "China" },
  "北京": { country: "CN", timezone: "Asia/Shanghai", currency: "CNY", labelZh: "中国", labelEn: "China" },
  beijing: { country: "CN", timezone: "Asia/Shanghai", currency: "CNY", labelZh: "中国", labelEn: "China" },
  "上海": { country: "CN", timezone: "Asia/Shanghai", currency: "CNY", labelZh: "中国", labelEn: "China" },
  shanghai: { country: "CN", timezone: "Asia/Shanghai", currency: "CNY", labelZh: "中国", labelEn: "China" },
  "天津": { country: "CN", timezone: "Asia/Shanghai", currency: "CNY", labelZh: "中国", labelEn: "China" },
  tianjin: { country: "CN", timezone: "Asia/Shanghai", currency: "CNY", labelZh: "中国", labelEn: "China" },
  "福州": { country: "CN", timezone: "Asia/Shanghai", currency: "CNY", labelZh: "中国", labelEn: "China" },
  fuzhou: { country: "CN", timezone: "Asia/Shanghai", currency: "CNY", labelZh: "中国", labelEn: "China" },
  "广州": { country: "CN", timezone: "Asia/Shanghai", currency: "CNY", labelZh: "中国", labelEn: "China" },
  guangzhou: { country: "CN", timezone: "Asia/Shanghai", currency: "CNY", labelZh: "中国", labelEn: "China" },
  "深圳": { country: "CN", timezone: "Asia/Shanghai", currency: "CNY", labelZh: "中国", labelEn: "China" },
  shenzhen: { country: "CN", timezone: "Asia/Shanghai", currency: "CNY", labelZh: "中国", labelEn: "China" },
  "成都": { country: "CN", timezone: "Asia/Shanghai", currency: "CNY", labelZh: "中国", labelEn: "China" },
  chengdu: { country: "CN", timezone: "Asia/Shanghai", currency: "CNY", labelZh: "中国", labelEn: "China" },
  "杭州": { country: "CN", timezone: "Asia/Shanghai", currency: "CNY", labelZh: "中国", labelEn: "China" },
  hangzhou: { country: "CN", timezone: "Asia/Shanghai", currency: "CNY", labelZh: "中国", labelEn: "China" },
  tokyo: { country: "JP", timezone: "Asia/Tokyo", currency: "JPY", labelZh: "日本", labelEn: "Japan" },
  "东京": { country: "JP", timezone: "Asia/Tokyo", currency: "JPY", labelZh: "日本", labelEn: "Japan" },
  singapore: { country: "SG", timezone: "Asia/Singapore", currency: "SGD", labelZh: "新加坡", labelEn: "Singapore" },
  "新加坡": { country: "SG", timezone: "Asia/Singapore", currency: "SGD", labelZh: "新加坡", labelEn: "Singapore" },
};

export function inferCityFacts(cityName: string) {
  const key = cityName.trim().toLowerCase();
  if (!key) return null;
  return CITY_FACTS[key] ?? CITY_FACTS[cityName.trim()] ?? null;
}

export function currencyLabel(currency: string, locale: string) {
  const zh = locale.startsWith("zh");
  const table: Record<string, [string, string]> = {
    CNY: ["人民币", "Chinese yuan"],
    JPY: ["日元", "Japanese yen"],
    SGD: ["新加坡元", "Singapore dollar"],
    USD: ["美元", "US dollar"],
    EUR: ["欧元", "Euro"],
  };
  const hit = table[currency];
  return hit ? (zh ? hit[0] : hit[1]) : currency;
}

export function timezoneLabel(timezone: string, locale: string) {
  const zh = locale.startsWith("zh");
  const table: Record<string, [string, string]> = {
    "Asia/Shanghai": ["中国标准时间", "China Standard Time"],
    "Asia/Tokyo": ["日本标准时间", "Japan Standard Time"],
    "Asia/Singapore": ["新加坡时间", "Singapore Time"],
  };
  const hit = table[timezone];
  return hit ? (zh ? hit[0] : hit[1]) : timezone;
}

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

export function localDateTimeInZoneToIso(value: string, timeZone: string) {
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

const PACE_OPTIONS = [
  { key: "relaxed", zh: "轻松", en: "Relaxed" },
  { key: "balanced", zh: "适中", en: "Balanced" },
  { key: "packed", zh: "紧凑", en: "Packed" },
] as const;

const INTEREST_OPTIONS = [
  { key: "food", zh: "美食", en: "Food" },
  { key: "nature", zh: "自然", en: "Nature" },
  { key: "culture", zh: "人文", en: "Culture" },
  { key: "seaside", zh: "海边", en: "Seaside" },
  { key: "shopping", zh: "购物", en: "Shopping" },
  { key: "family", zh: "亲子", en: "Family" },
] as const;

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
  const zh = locale.startsWith("zh");
  const browserTimezone = useMemo(
    () => Intl.DateTimeFormat().resolvedOptions().timeZone || "Asia/Shanghai",
    [],
  );
  const [step, setStep] = useState<1 | 2 | 3>(1);
  const [advanced, setAdvanced] = useState(false);
  const [draft, setDraft] = useState<JourneyTrialDraft>({
    cityName: "",
    countryCode: "CN",
    timezone: browserTimezone,
    startAt: futureLocalAt(1, 10),
    endAt: futureLocalAt(3, 20),
    arrivalLocation: "",
    departureLocation: "",
    budgetMajor: 3000,
    stayBudgetMajor: 1000,
    currency: "CNY",
    partySize: 2,
    rooms: 1,
    pace: "relaxed",
    interests: [],
    specialRequirements: "",
  });
  const [roomsTouched, setRoomsTouched] = useState(false);

  const update = <K extends keyof JourneyTrialDraft>(key: K, value: JourneyTrialDraft[K]) =>
    setDraft((current) => ({ ...current, [key]: value }));

  // Corrections §5: infer country / timezone / currency from the city and keep
  // the technical fields behind "Advanced settings".
  const applyCity = (cityName: string) => {
    const facts = inferCityFacts(cityName);
    setDraft((current) => ({
      ...current,
      cityName,
      ...(facts
        ? { countryCode: facts.country, timezone: facts.timezone, currency: facts.currency }
        : {}),
    }));
  };

  const facts = inferCityFacts(draft.cityName);
  const step1Ready = draft.cityName.trim().length > 0;
  const step2Ready = draft.partySize >= 1 && draft.budgetMajor > 0;

  const stepTitle = zh
    ? ["目的地与时间", "人数与偏好", "确认创建"]
    : ["Destination & dates", "Travellers & preferences", "Review & create"];

  const submit = async () => {
    await onCreate(draft);
  };

  return (
    <section className="v8-page" data-testid="trial-setup">
      <div className="v8-page-intro compact">
        <div>
          <p className="v8-kicker">{t("trial.kicker")}</p>
          <h1>{zh ? "新建行程" : "Create a trip"}</h1>
          <p className="v8-lede">
            {zh
              ? "三步完成。选择目的地、告诉我们怎么玩，剩下的交给 CityNexus。"
              : "Three steps. Pick a destination, tell us how you like to travel, and let CityNexus handle the rest."}
          </p>
        </div>
        <button
          type="button"
          className="v8-outline-button"
          aria-label="Switch language"
          onClick={switchLocale}
        >
          {zh ? "EN" : "中文"}
        </button>
      </div>

      <ol className="trial-steps" data-testid="trial-steps">
        {stepTitle.map((label, index) => {
          const n = (index + 1) as 1 | 2 | 3;
          return (
            <li
              key={label}
              className={n === step ? "active" : n < step ? "done" : ""}
              data-testid={`trial-step-${n}`}
            >
              <span className="trial-step-dot">{n < step ? "✓" : n}</span>
              <span>{label}</span>
            </li>
          );
        })}
      </ol>

      {step === 1 && (
        <div className="v8-card trial-card" data-testid="trial-step1-body">
          <label className="trial-field">
            <span>{zh ? "目的地" : "Destination"}</span>
            <input
              data-testid="trial-city"
              value={draft.cityName}
              onChange={(event) => applyCity(event.target.value)}
              placeholder={zh ? "例如：厦门" : "e.g. Xiamen"}
              autoFocus
            />
          </label>

          {facts && (
            <p className="trial-inferred" data-testid="trial-inferred">
              {zh ? "已自动设置：" : "Auto-set: "}
              {zh ? facts.labelZh : facts.labelEn} ·{" "}
              {currencyLabel(draft.currency, locale)} ·{" "}
              {timezoneLabel(draft.timezone, locale)}
            </p>
          )}

          <label className="trial-field">
            <span>{zh ? "抵达厦门" : "Arrive at"}</span>
            <input
              data-testid="trial-arrival"
              value={draft.arrivalLocation}
              onChange={(event) => update("arrivalLocation", event.target.value)}
              placeholder={zh ? "例如：厦门高崎国际机场" : "e.g. Xiamen Gaoqi Intl Airport"}
            />
          </label>
          <label className="trial-field">
            <span>{zh ? "离开厦门" : "Depart from"}</span>
            <input
              data-testid="trial-departure"
              value={draft.departureLocation}
              onChange={(event) => update("departureLocation", event.target.value)}
              placeholder={zh ? "例如：厦门北站" : "e.g. Xiamen North Station"}
            />
          </label>
          <div className="trial-row">
            <label className="trial-field">
              <span>{zh ? "抵达时间" : "Arrival time"}</span>
              <input
                data-testid="trial-start"
                type="datetime-local"
                value={draft.startAt}
                onChange={(event) => update("startAt", event.target.value)}
              />
            </label>
            <label className="trial-field">
              <span>{zh ? "离开时间" : "Departure time"}</span>
              <input
                data-testid="trial-end"
                type="datetime-local"
                value={draft.endAt}
                onChange={(event) => update("endAt", event.target.value)}
              />
            </label>
          </div>

          <details
            className="trial-advanced"
            open={advanced}
            onToggle={(event) => setAdvanced((event.target as HTMLDetailsElement).open)}
          >
            <summary>{zh ? "高级设置" : "Advanced settings"}</summary>
            <div className="trial-row">
              <label className="trial-field">
                <span>{t("trial.country")}</span>
                <input
                  data-testid="trial-country"
                  value={draft.countryCode}
                  onChange={(event) => update("countryCode", event.target.value.toUpperCase().slice(0, 3))}
                />
              </label>
              <label className="trial-field">
                <span>{t("trial.timezone")}</span>
                <input
                  data-testid="trial-timezone"
                  value={draft.timezone}
                  onChange={(event) => update("timezone", event.target.value)}
                />
              </label>
              <label className="trial-field">
                <span>{t("trial.currency")}</span>
                <input
                  data-testid="trial-currency"
                  value={draft.currency}
                  onChange={(event) => update("currency", event.target.value.toUpperCase().slice(0, 3))}
                />
              </label>
            </div>
          </details>
        </div>
      )}

      {step === 2 && (
        <div className="v8-card trial-card" data-testid="trial-step2-body">
          <div className="trial-row">
            <label className="trial-field">
              <span>{zh ? "旅行人数" : "Travellers"}</span>
              <input
                data-testid="trial-party"
                type="number"
                min="1"
                max="20"
                value={draft.partySize}
                onChange={(event) => {
                  const partySize = Number(event.target.value);
                  setDraft((current) => ({
                    ...current,
                    partySize,
                    ...(roomsTouched ? {} : { rooms: suggestedRoomCount(partySize) }),
                  }));
                }}
              />
            </label>
            <label className="trial-field">
              <span>{t("trial.rooms")}</span>
              <input
                data-testid="trial-rooms"
                type="number"
                min="1"
                max="20"
                value={draft.rooms}
                onChange={(event) => {
                  setRoomsTouched(true);
                  update("rooms", Number(event.target.value));
                }}
              />
            </label>
          </div>

          <div className="trial-row">
            <label className="trial-field">
              <span>{zh ? "总预算" : "Total budget"}</span>
              <input
                data-testid="trial-budget"
                type="number"
                min="0"
                value={draft.budgetMajor}
                onChange={(event) => update("budgetMajor", Number(event.target.value))}
              />
            </label>
            <label className="trial-field">
              <span>{t("trial.stayBudget")}</span>
              <input
                data-testid="trial-stay-budget"
                type="number"
                min="0"
                value={draft.stayBudgetMajor}
                onChange={(event) => update("stayBudgetMajor", Number(event.target.value))}
              />
            </label>
          </div>

          <fieldset className="trial-fieldset">
            <legend>{zh ? "旅行节奏" : "Pace"}</legend>
            <div className="trial-chips">
              {PACE_OPTIONS.map((option) => (
                <button
                  key={option.key}
                  type="button"
                  className={draft.pace === option.key ? "active" : ""}
                  data-testid={`trial-pace-${option.key}`}
                  onClick={() => update("pace", option.key)}
                >
                  {zh ? option.zh : option.en}
                </button>
              ))}
            </div>
          </fieldset>

          <fieldset className="trial-fieldset">
            <legend>{zh ? "兴趣" : "Interests"}</legend>
            <div className="trial-chips">
              {INTEREST_OPTIONS.map((option) => {
                const selected = (draft.interests ?? []).includes(option.key);
                return (
                  <button
                    key={option.key}
                    type="button"
                    className={selected ? "active" : ""}
                    data-testid={`trial-interest-${option.key}`}
                    onClick={() =>
                      update(
                        "interests",
                        selected
                          ? (draft.interests ?? []).filter((item) => item !== option.key)
                          : [...(draft.interests ?? []), option.key],
                      )
                    }
                  >
                    {zh ? option.zh : option.en}
                  </button>
                );
              })}
            </div>
          </fieldset>

          <label className="trial-field">
            <span>{zh ? "特殊要求" : "Special requirements"}</span>
            <textarea
              data-testid="trial-special"
              rows={3}
              value={draft.specialRequirements ?? ""}
              onChange={(event) => update("specialRequirements", event.target.value)}
              placeholder={
                zh
                  ? "例如：我妈妈坐轮椅；每天走路不超过 3000 米"
                  : "e.g. my mother uses a wheelchair; no more than 3 km walking a day"
              }
            />
          </label>
        </div>
      )}

      {step === 3 && (
        <div className="v8-card trial-card" data-testid="trial-step3-body">
          <dl className="trial-review">
            <div>
              <dt>{zh ? "目的地" : "Destination"}</dt>
              <dd data-testid="review-city">{draft.cityName || "—"}</dd>
            </div>
            <div>
              <dt>{zh ? "抵达" : "Arrival"}</dt>
              <dd data-testid="review-arrival">
                {draft.arrivalLocation || "—"} · {draft.startAt.replace("T", " ")}
              </dd>
            </div>
            <div>
              <dt>{zh ? "离开" : "Departure"}</dt>
              <dd data-testid="review-departure">
                {draft.departureLocation || "—"} · {draft.endAt.replace("T", " ")}
              </dd>
            </div>
            <div>
              <dt>{zh ? "人数 / 房间" : "Travellers / rooms"}</dt>
              <dd data-testid="review-party">
                {draft.partySize} · {draft.rooms}
              </dd>
            </div>
            <div>
              <dt>{zh ? "总预算 / 住宿" : "Total / stay budget"}</dt>
              <dd data-testid="review-budget">
                {draft.currency} {draft.budgetMajor} / {draft.stayBudgetMajor}
              </dd>
            </div>
            <div>
              <dt>{zh ? "节奏" : "Pace"}</dt>
              <dd data-testid="review-pace">{draft.pace || "—"}</dd>
            </div>
            <div>
              <dt>{zh ? "兴趣" : "Interests"}</dt>
              <dd data-testid="review-interests">
                {(draft.interests ?? []).join(", ") || "—"}
              </dd>
            </div>
            <div>
              <dt>{zh ? "特殊要求" : "Special requirements"}</dt>
              <dd data-testid="review-special">{draft.specialRequirements || "—"}</dd>
            </div>
            <div>
              <dt>{zh ? "自动设置" : "Auto-set"}</dt>
              <dd>
                {draft.countryCode} · {draft.currency} · {draft.timezone}
              </dd>
            </div>
          </dl>
          {onCancel && (
            <button type="button" className="trial-back-link" onClick={onCancel}>
              {t("trial.cancel")}
            </button>
          )}
        </div>
      )}

      {/* Sticky CTA: always reachable, never below a wall of scrolling. */}
      <div className="trial-sticky-cta" data-testid="trial-sticky-cta">
        {step > 1 && (
          <button
            type="button"
            className="v8-outline-button"
            data-testid="trial-back"
            disabled={busy}
            onClick={() => setStep((current) => (current === 3 ? 2 : 1))}
          >
            {zh ? "返回" : "Back"}
          </button>
        )}
        {step < 3 && (
          <button
            type="button"
            className="v8-primary-button"
            data-testid="trial-next"
            disabled={(step === 1 && !step1Ready) || (step === 2 && !step2Ready)}
            onClick={() => setStep((current) => (current === 1 ? 2 : 3))}
          >
            {zh ? "下一步" : "Next"}
          </button>
        )}
        {step === 3 && (
          <button
            type="button"
            className="v8-primary-button"
            data-testid="trial-create"
            disabled={busy}
            onClick={() => void submit()}
          >
            {busy ? t("trial.creating") : zh ? "确认创建" : "Create trip"}
          </button>
        )}
      </div>

      {/* Secondary, de-emphasised: the sealed demo is not the golden path. */}
      <div className="trial-secondary">
        <button
          type="button"
          className="trial-back-link"
          data-testid="trial-tianjin-demo"
          disabled={busy}
          onClick={() => void onUseTianjinDemo()}
        >
          {t("trial.tianjinDemo")}
        </button>
        {step === 1 && (
          <button
            type="button"
            className="trial-back-link"
            data-testid="trial-show-advanced"
            onClick={() => {
              setAdvanced(true);
              const node = document.querySelector(".trial-advanced") as HTMLDetailsElement | null;
              if (node) node.open = true;
            }}
          >
            {zh ? "高级设置" : "Advanced settings"}
          </button>
        )}
      </div>
    </section>
  );
}
