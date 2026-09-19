export const desktopRoutes = [
  { key: "hub", label: "Journey Hub", icon: "map", group: "TODAY" },
  { key: "live", label: "Live Journey", icon: "spark", group: "TODAY" },
  { key: "map", label: "Map", icon: "map", group: "TODAY" },
  { key: "studio", label: "Trip Studio", icon: "calendar", group: "PLAN" },
  { key: "stay", label: "Stay Explorer", icon: "bed", group: "PLAN" },
  { key: "discover", label: "City Discovery", icon: "map", group: "PLAN" },
  { key: "bookings", label: "Travel Wallet", icon: "ticket", group: "TRAVEL" },
  { key: "agent", label: "Copilot", icon: "spark", group: "TRAVEL" },
  { key: "authoritative", label: "Recovery", icon: "spark", group: "SYSTEM" },
  { key: "intelligence", label: "Intelligence", icon: "spark", group: "SYSTEM" },
  { key: "twin", label: "Traveler Twin", icon: "calendar", group: "SYSTEM" },
] as const;

// Official primary navigation (see docs/DESIGN_CORRECTIONS_REQUIRED.md §1).
// Wallet/bookings deliberately left the golden path; they now live under
// Trips ("预订与凭证") and Me ("钱包").
export const mobileRoutes = [
  { key: "hub", label: "Today", icon: "map" },
  { key: "trips", label: "Trips", icon: "calendar" },
  { key: "map", label: "Map", icon: "map" },
  { key: "agent", label: "Copilot", icon: "spark" },
  { key: "me", label: "Me", icon: "user" },
] as const;
