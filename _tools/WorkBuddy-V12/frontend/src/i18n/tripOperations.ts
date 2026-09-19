export type TripLocale = "en" | "zh-CN";

const copy = {
  en: {
    hub: "Journey Hub",
    studio: "Trip Studio",
    stay: "Stay Explorer",
    live: "Live Journey",
    bookings: "Travel Wallet",
    intelligence: "Intelligence",
    twin: "Traveler Twin",
    agent: "AI desk",
    authoritative: "Authoritative execution",
    map: "Map",
    me: "Me",
    language: "中文",
    now: "NOW",
    next: "NEXT · LEAVE BY",
    navigate: "NAVIGATE →",
    risk: "RISK",
  },
  "zh-CN": {
    hub: "行程总览",
    studio: "行程工作台",
    stay: "住宿选择",
    live: "实时行程",
    bookings: "旅行票夹",
    intelligence: "智能守护",
    twin: "旅行者画像",
    agent: "AI 助手",
    authoritative: "权威执行",
    map: "地图",
    me: "我的",
    language: "EN",
    now: "现在",
    next: "下一步 · 最晚出发",
    navigate: "开始导航 →",
    risk: "风险",
  },
} as const;

export function tripCopy(locale: TripLocale) {
  return copy[locale];
}
