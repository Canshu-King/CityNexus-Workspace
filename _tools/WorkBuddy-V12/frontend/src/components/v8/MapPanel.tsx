import { useEffect, useMemo, useRef } from "react";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import type { V8Data } from "../../app/v8Types";

export function MapPanel({
  data,
  option,
}: {
  data: V8Data | null;
  option: V8Data["options"][number] | null;
}) {
  const host = useRef<HTMLDivElement | null>(null);
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
    if (!host.current) return undefined;
    const coordinates = route
      .flatMap((feature) => feature.geometry.coordinates)
      .filter((value) => value.length >= 2);
    const center =
      coordinates[Math.floor(coordinates.length / 2)] ??
      (points[0] ? [points[0].longitude, points[0].latitude] : [117.19, 39.13]);
    const map = new maplibregl.Map({
      container: host.current,
      style: {
        version: 8,
        sources: {
          "open-street-map": {
            type: "raster",
            tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
            tileSize: 256,
            attribution: "© OpenStreetMap contributors",
          },
          "journey-provider-route": {
            type: "geojson",
            data: {
              type: "FeatureCollection",
              features: route,
            } as GeoJSON.FeatureCollection,
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
    });
    const resizeObserver = new ResizeObserver(() => map.resize());
    resizeObserver.observe(host.current);
    points.forEach((point, index) => {
      const marker = document.createElement("div");
      marker.className = `v9-map-marker ${point.role === "STAY" ? "stay" : ""} ${point.protected ? "protected" : ""} ${point.current ? "current" : ""} ${point.disrupted ? "disrupted" : ""}`;
      marker.textContent = String(index + 1);
      marker.setAttribute("aria-label", point.title);
      new maplibregl.Marker({ element: marker })
        .setLngLat([point.longitude, point.latitude])
        .addTo(map);
    });
    if (data?.active_plan?.user_location) {
      const user = document.createElement("div");
      user.className = "v9-map-marker user";
      user.textContent = "●";
      user.setAttribute(
        "aria-label",
        `Your location · ${Math.round(data.active_plan.user_location.accuracy_m)} m accuracy`,
      );
      new maplibregl.Marker({ element: user })
        .setLngLat([
          data.active_plan.user_location.longitude,
          data.active_plan.user_location.latitude,
        ])
        .addTo(map);
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
      map.fitBounds(bounds, { padding: 42, maxZoom: 13, duration: 0 });
    }
    return () => {
      resizeObserver.disconnect();
      map.remove();
    };
  }, [data, points, route]);
  return (
    <div
      className="v8-map-panel"
      data-testid="v8-maplibre-panel"
      aria-label="Journey map"
    >
      <div ref={host} className="v8-maplibre-canvas" />
      <div className="v8-map-caption">
        <span className="status-dot" />
        Route context <b>{route.length} legs</b>
        <span className="v8-sr-only">Provider-backed route · WGS84</span>
      </div>
    </div>
  );
}
