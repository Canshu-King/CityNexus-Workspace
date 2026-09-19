export const desktopRoutes = [
  { key: "hub", label: "Journey Hub", icon: "map" },
  { key: "studio", label: "Trip Studio", icon: "calendar" },
  { key: "stay", label: "Stay Explorer", icon: "bed" },
  { key: "live", label: "Live Journey", icon: "spark" },
  { key: "authoritative", label: "Authoritative execution", icon: "spark" },
  { key: "bookings", label: "Bookings", icon: "ticket" },
  { key: "intelligence", label: "Intelligence", icon: "spark" },
  { key: "twin", label: "Traveler Twin", icon: "calendar" },
  { key: "agent", label: "AI desk", icon: "spark" },
] as const;

export const mobileRoutes = [
  { key: "hub", label: "Journey", icon: "map" },
  { key: "map", label: "Map", icon: "map" },
  { key: "agent", label: "AI", icon: "spark" },
  { key: "bookings", label: "Bookings", icon: "ticket" },
  { key: "me", label: "Me", icon: "user" },
] as const;
