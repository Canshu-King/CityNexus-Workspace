export function formatV8Money(minor: number | null | undefined, currency = "CNY") {
  return minor == null ? "Provider price unavailable" : new Intl.NumberFormat("zh-CN", { style: "currency", currency, maximumFractionDigits: 0 }).format(minor / 100);
}

export function formatV8Date(value?: string) {
  return value ? new Intl.DateTimeFormat("en-GB", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit", hour12: false }).format(new Date(value)) : "—";
}
