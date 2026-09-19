import { useEffect, useRef } from "react";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import type { Activity, PlaceRecord, PlanVersion, RouteEvidence } from "../api/citynexus";
import type { JourneyTwin } from "../contracts/journeyTwin";
import type { ReplanProposal } from "../contracts/replan";

interface JourneyMapProps {
  plan: PlanVersion;
  twin: JourneyTwin;
  places: PlaceRecord[];
  eventActive: boolean;
  proposals: ReplanProposal[];
  routeEvidence: RouteEvidence | null;
}

type Coordinate = [number, number];

const OPENFREEMAP_STYLE_URL = "https://tiles.openfreemap.org/styles/liberty";

function coordinatesFor(activity: Activity, places: Map<string, PlaceRecord>): Coordinate | null {
  const place = activity.place_id ? places.get(activity.place_id) : null;
  return place ? [place.location.longitude, place.location.latitude] : null;
}

function fallbackRouteFor(plan: PlanVersion, places: Map<string, PlaceRecord>): Coordinate[] {
  return plan.activities
    .slice()
    .sort((a, b) => a.sequence_no - b.sequence_no)
    .map((activity) => coordinatesFor(activity, places))
    .filter((value): value is Coordinate => value !== null);
}

function lineFeature(
  coordinates: Coordinate[],
  properties: Record<string, unknown>,
): GeoJSON.Feature<GeoJSON.LineString> {
  const safe =
    coordinates.length >= 2
      ? coordinates
      : [
          coordinates[0] ?? [117.19, 39.13],
          coordinates[0] ?? [117.19, 39.13],
        ];
  return {
    type: "Feature",
    properties,
    geometry: { type: "LineString", coordinates: safe },
  };
}

function featureCollection(features: GeoJSON.Feature[]): GeoJSON.FeatureCollection {
  return { type: "FeatureCollection", features };
}

export function JourneyMap({
  plan,
  twin,
  places,
  eventActive,
  proposals,
  routeEvidence,
}: JourneyMapProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const proposal = proposals[0] ?? null;

  useEffect(() => {
    if (!containerRef.current || !places.length) return undefined;
    const placeMap = new Map(places.map((place) => [place.id, place]));
    const fallbackOld = fallbackRouteFor(plan, placeMap);
    const oldFeature = routeEvidence
      ? (routeEvidence.old_route as unknown as GeoJSON.Feature<GeoJSON.LineString>)
      : lineFeature(fallbackOld, {
          provider: "client-place-fallback",
          provider_backed: false,
          fallback: true,
          fallback_reason: "ROUTE_EVIDENCE_NOT_LOADED",
        });
    const newFeature = routeEvidence?.new_route
      ? (routeEvidence.new_route as unknown as GeoJSON.Feature<GeoJSON.LineString>)
      : proposal
        ? lineFeature(fallbackOld, {
            provider: "client-place-fallback",
            provider_backed: false,
            fallback: true,
            fallback_reason: "ROUTE_EVIDENCE_NOT_LOADED",
          })
        : null;
    const disruptionScope = routeEvidence?.disruption_scope
      ? (routeEvidence.disruption_scope as unknown as GeoJSON.Feature)
      : null;
    const impactedActivityIds = new Set(routeEvidence?.impacted_activity_ids ?? []);
    const oldCoordinates = oldFeature.geometry.coordinates as Coordinate[];
    const map = new maplibregl.Map({
      container: containerRef.current,
      attributionControl: false,
      style: OPENFREEMAP_STYLE_URL,
      center: oldCoordinates[0] ?? [117.19, 39.13],
      zoom: 11,
    });
    (containerRef.current as HTMLDivElement & { __cityNexusMap?: maplibregl.Map }).__cityNexusMap = map;
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");

    map.on("load", () => {
      map.addSource("citynexus-old-route", {
        type: "geojson",
        data: featureCollection([oldFeature]),
      });
      map.addLayer({
        id: "citynexus-old-route",
        type: "line",
        source: "citynexus-old-route",
        paint: {
          "line-color": "#7d8ba4",
          "line-width": 3,
          "line-dasharray": [2, 2],
          "line-opacity": 0.75,
        },
      });
      if (disruptionScope) {
        map.addSource("citynexus-disruption-scope", {
          type: "geojson",
          data: disruptionScope,
        });
        map.addLayer({
          id: "citynexus-disruption-scope-fill",
          type: "fill",
          source: "citynexus-disruption-scope",
          paint: { "fill-color": "#e05b4d", "fill-opacity": 0.16 },
        });
        map.addLayer({
          id: "citynexus-disruption-scope-line",
          type: "line",
          source: "citynexus-disruption-scope",
          paint: { "line-color": "#c9473d", "line-width": 2, "line-dasharray": [2, 1] },
        });
      }
      if (newFeature) {
        map.addSource("citynexus-new-route", {
          type: "geojson",
          data: featureCollection([newFeature]),
        });
        map.addLayer({
          id: "citynexus-new-route",
          type: "line",
          source: "citynexus-new-route",
          paint: { "line-color": "#4259d8", "line-width": 5, "line-opacity": 0.9 },
        });
      }
      const points = plan.activities
        .map((activity) => {
          const coordinate = coordinatesFor(activity, placeMap);
          if (!coordinate) return null;
          const protectedActivity = twin.upcoming_commitments.some(
            (commitment) =>
              commitment.activity_id === activity.id && commitment.level === "C4_Anchored",
          );
          return {
            type: "Feature" as const,
            properties: {
              title: activity.title,
              role:
                activity.id === twin.current_activity_id
                  ? "current"
                  : protectedActivity
                    ? "protected"
                    : impactedActivityIds.has(activity.id)
                      ? "risk"
                    : "upcoming",
            },
            geometry: { type: "Point" as const, coordinates: coordinate },
          };
        })
        .filter((feature): feature is NonNullable<typeof feature> => feature !== null);
      map.addSource("citynexus-activities", {
        type: "geojson",
        data: { type: "FeatureCollection", features: points },
      });
      map.addLayer({
        id: "citynexus-activity-points",
        type: "circle",
        source: "citynexus-activities",
        paint: {
          "circle-radius": 7,
          "circle-color": [
            "match",
            ["get", "role"],
            "current",
            "#4259d8",
            "protected",
            "#12653a",
            "risk",
            "#c9473d",
            "#e05b4d",
          ],
          "circle-stroke-color": "#ffffff",
          "circle-stroke-width": 2,
        },
      });
      map.addLayer({
        id: "citynexus-activity-labels",
        type: "symbol",
        source: "citynexus-activities",
        layout: {
          "text-field": ["get", "title"],
          "text-size": 11,
          "text-offset": [0, 1.5],
        },
        paint: {
          "text-color": "#172033",
          "text-halo-color": "#ffffff",
          "text-halo-width": 1,
        },
      });
      if (routeEvidence?.markers) {
        map.addSource("citynexus-markers", {
          type: "geojson",
          data: routeEvidence.markers,
        });
        map.addLayer({
          id: "citynexus-marker-points",
          type: "circle",
          source: "citynexus-markers",
          paint: {
            "circle-radius": 8,
            "circle-color": [
              "match",
              ["get", "role"],
              "current",
              "#4259d8",
              "next",
              "#7e95ff",
              "c4",
              "#12653a",
              "disruption",
              "#e05b4d",
              "#e6a43b",
            ],
            "circle-stroke-color": "#ffffff",
            "circle-stroke-width": 2,
          },
        });
      }
      if (oldCoordinates.length > 1) {
        const bounds = oldCoordinates.reduce(
          (current, coordinate) => current.extend(coordinate),
          new maplibregl.LngLatBounds(oldCoordinates[0], oldCoordinates[0]),
        );
        map.fitBounds(bounds, { padding: 45, maxZoom: 13, duration: 0 });
      }
      if (eventActive && routeEvidence?.markers) {
        const disruption = routeEvidence.markers.features.find(
          (feature) => feature.properties.role === "disruption",
        );
        if (disruption) {
          new maplibregl.Marker({ color: "#e05b4d" })
            .setLngLat(disruption.geometry.coordinates)
            .setPopup(new maplibregl.Popup({ offset: 12 }).setText("Disruption scope"))
            .addTo(map);
        }
      }
    });
    return () => {
      delete (containerRef.current as HTMLDivElement & { __cityNexusMap?: maplibregl.Map })
        .__cityNexusMap;
      map.remove();
    };
  }, [eventActive, places, plan, proposal, routeEvidence, twin]);

  return (
    <div
      ref={containerRef}
      className="maplibre-container"
      aria-label="MapLibre Journey map"
      data-route-source={routeEvidence?.source ?? "unavailable"}
      data-route-provider={routeEvidence?.provider ?? "unavailable"}
      data-route-fallback={String(routeEvidence?.fallback ?? true)}
      data-basemap-provider="openfreemap"
    />
  );
}
