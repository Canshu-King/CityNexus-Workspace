import { useEffect, useMemo, useRef, useState } from "react";
import "maplibre-gl/dist/maplibre-gl.css";
import type { FeatureCollection } from "geojson";
import type { V8Data } from "../../app/v8Types";
import { useT, useLocale } from "../../i18n/LocaleContext";

export function MapPanel({
  data,
  option,
}: {
  data: V8Data | null;
  option: V8Data["options"][number] | null;
}) {
  const host = useRef<HTMLDivElement | null>(null);
  // Map truth: never centre on a hardcoded city.  If the Journey has no
  // trustworthy coordinates we say so explicitly instead of silently showing
  // an unrelated city (design corrections §10).
  const [noLocation, setNoLocation] = useState(false);
  const t = useT();
  const { locale } = useLocale();
  const route = useMemo(() => {
    if (data?.active_plan?.legs.length)
      return data.active_plan.legs.map((leg) => leg.geometry);
    if (!data || !option) return [];
    return option.leg_mode_map.flatMap((leg) => {
      const fact = data.mobility_facts.find(
        (item) =>
          item.from_key === leg.from_key &&
          item.to_key === leg.to_key &&
          item.mode === leg.mode,
      );
      return fact?.geometry ? [fact.geometry] : [];
    });
  }, [data, option]);
  const points = useMemo(() => {
    const active =
      data?.active_plan?.activities.flatMap((item) =>
        item.metadata.longitude != null && item.metadata.latitude != null
          ? [
              {
                title: item.title,
                longitude: item.metadata.longitude,
                latitude: item.metadata.latitude,
                role: item.metadata.role,
                protected: item.protected,
                current: item.id === data?.active_plan?.current_activity_id,
                disrupted:
                  data?.active_plan?.disruptions.some(
                    (event) => event.affected_activity_id === item.id,
                  ) ?? false,
              },
            ]
          : [],
      ) ?? [];
    if (active.length) return active;
    if (!data) return [];
    return data.offers.slice(0, 1).map((offer) => ({
      title: offer.property_name,
      longitude: offer.location.longitude,
      latitude: offer.location.latitude,
      role: "STAY",
      protected: false,
      current: false,
      disrupted: false,
    }));
  }, [data]);

  useEffect(() => {
    let disposed = false;
    let map: import("maplibre-gl").Map | null = null;
    let resizeObserver: ResizeObserver | null = null;
    void import("maplibre-gl").then(({ default: maplibregl }) => {
      if (disposed || !host.current) return;
      const coordinates = route
        .flatMap((feature) => feature.geometry.coordinates)
        .filter((value) => value.length >= 2);
      const center: [number, number] | null =
        (coordinates[Math.floor(coordinates.length / 2)] as [number, number] | undefined) ??
        (points[0] ? [points[0].longitude, points[0].latitude] : null);
      if (!center) {
        // No route geometry and no located activity: an honest empty state is
        // the correct answer, not another city's map.
        setNoLocation(true);
        return;
      }
      setNoLocation(false);
      const mapInstance = new maplibregl.Map({
        /* Never leave the traveller staring at an empty box when the tile
           server is unreachable (common on restricted networks). The Apple
           branch's GeoJSON typing fix dropped this line along with the comment
           that explained it; maplibre's own default happens to be false, but an
           accessibility-relevant intent belongs in the source, not in an
           implicit library default. maplibre's shipped MapOptions type omits
           this documented constructor flag, hence the narrow cast at the end of
           the options object. */
        failIfMajorPerformanceCaveat: false,
        container: host.current,
      style: {
        version: 8,
        sources: {
          "open-street-map": {
            type: "raster",
            tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
            tileSize: 256,
            attribution: t("mapComp.attribution"),
          },
          // A flat canvas behind the raster tiles means a blocked or offline
          // tile server degrades to a readable route view instead of a blank
          // white rectangle.
          "base-canvas": {
            type: "geojson",
            data: { type: "FeatureCollection", features: [] },
          },
          "journey-provider-route": {
            type: "geojson",
            data: {
              type: "FeatureCollection",
              features: route,
            } as FeatureCollection,
          },
        },
        layers: [
          {
            id: "canvas",
            type: "background",
            paint: { "background-color": "#dfeae8" },
          },
          {
            id: "open-street-map",
            type: "raster",
            source: "open-street-map",
            paint: { "raster-opacity": 0.82 },
          },
          {
            id: "journey-provider-route",
            type: "line",
            source: "journey-provider-route",
            paint: {
              "line-color": "#4658d9",
              "line-width": 4,
              "line-opacity": 0.84,
            },
          },
        ],
      },
      center: center as [number, number],
      zoom: 11,
      attributionControl: false,
      interactive: false,
      } as maplibregl.MapOptions & { failIfMajorPerformanceCaveat?: boolean });
      map = mapInstance;
      resizeObserver = new ResizeObserver(() => map?.resize());
      resizeObserver.observe(host.current);
    points.forEach((point, index) => {
      const marker = document.createElement("div");
      marker.className = `v9-map-marker ${point.role === "STAY" ? "stay" : ""} ${point.protected ? "protected" : ""} ${point.current ? "current" : ""} ${point.disrupted ? "disrupted" : ""}`;
      marker.textContent = String(index + 1);
      marker.setAttribute("aria-label", point.title);
        new maplibregl.Marker({ element: marker })
        .setLngLat([point.longitude, point.latitude])
        .addTo(mapInstance);
    });
    if (data?.active_plan?.user_location) {
      const user = document.createElement("div");
      user.className = "v9-map-marker user";
      user.textContent = "●";
      user.setAttribute(
        "aria-label",
        t("mapComp.yourLocation", { n: Math.round(data.active_plan.user_location.accuracy_m) }),
      );
      new maplibregl.Marker({ element: user })
        .setLngLat([
          data.active_plan.user_location.longitude,
          data.active_plan.user_location.latitude,
        ])
        .addTo(mapInstance);
    }
    if (coordinates.length > 1) {
      const bounds = coordinates
        .slice(1)
        .reduce(
          (value, coordinate) => value.extend(coordinate as [number, number]),
          new maplibregl.LngLatBounds(
            coordinates[0] as [number, number],
            coordinates[0] as [number, number],
          ),
        );
      const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
        mapInstance.fitBounds(bounds, {
        padding: 42,
        maxZoom: 13,
        duration: reducedMotion ? 0 : 650,
      });
    }
    });
    return () => {
      disposed = true;
      resizeObserver?.disconnect();
      map?.remove();
    };
  }, [data, points, route]);
  if (noLocation) {
    return (
      <div
        className="v8-map-panel v8-map-empty"
        data-testid="v8-map-empty"
        role="status"
        aria-live="polite"
      >
        <div className="v8-map-empty-body">
          <b>{locale.startsWith("zh") ? "尚未获取地图位置" : "No map location yet"}</b>
          <p>
            {locale.startsWith("zh")
              ? "这个行程还没有可信的坐标。添加活动地点或开启定位后，地图会显示正确的城市。"
              : "This trip has no trustworthy coordinates yet. Add located activities or enable location, and the map will show the right city."}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div
      className="v8-map-panel"
      data-testid="v8-maplibre-panel"
      aria-label={t("mapComp.journeyMap")}
    >
      <div ref={host} className="v8-maplibre-canvas" />
      <div className="v8-map-caption">
        <span className="status-dot" />
        {t("mapComp.routeContext")} <b>{t("mapComp.legs", { n: route.length })}</b>
        <span className="v8-sr-only">{t("mapComp.providerRoute")}</span>
      </div>
    </div>
  );
}
