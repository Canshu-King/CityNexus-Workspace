import type { TravelerCapability } from "../api/citynexus";

export type V8Data = {
  journey: { id: string; traveler_id: string; title: string; city_code: string; timezone: string; start_at: string; end_at: string; budget: { amount_minor: number; currency: string } };
  trip: { arrival_anchor: { at?: string; location?: string }; departure_anchor: { at?: string; location?: string }; party_size: number; occupancy: Record<string, unknown>; stay_budget: { amount_minor: number; currency: string } };
  offers: Array<{ id: string; external_offer_id: string; property_name: string; room_type: string; total_amount_minor: number; nightly_amount_minor: number; currency: string; refundable: boolean; check_in_at: string; check_out_at: string; cancellation_policy: { summary?: string }; evidence: { source?: string; confidence?: number }; location: { latitude: number; longitude: number; crs?: string } }>;
  options: Array<{ id: string; rank: number; status: string; score: number; stay: V8Data["offers"][number]; stay_total_minor: number; daily_travel_minor: number; mobility_total_minor: number; walking_min: number; protected_margin_min: number; arrival_fit: number; departure_fit: number; cancellation_score: number; days: Array<{ day: number; label: string; anchor: string; activities: string[]; mode: string }>; leg_modes: string[]; leg_mode_map: Array<{ from_key: string; to_key: string; mode: string; mobility_fact_id?: string }>; journey_impact: Record<string, any>; hard_constraints_passed: boolean; optimizer_kind: string; weather_state: string; materialized_plan_version_id?: string | null }>;
  selected_option_id: string | null;
  mobility_facts: Array<{ id?: string; mode: string; from_key: string; to_key: string; duration_min: number; cost_amount_minor: number | null; currency: string | null; cost_status: string; walking_min: number; transfers: number; weather_exposure: string; reliability_score: number; provider_key?: string; provenance?: string; crs?: string; geometry?: { type: "Feature"; properties?: Record<string, unknown>; geometry: { type: "LineString"; coordinates: number[][] } } }>;
  active_plan: null | { id: string; version_no: number; status: string; source: string; mobility_snapshot_id?: string | null; mobility_evidence?: { snapshot_id?: string | null; expires_at?: string | null; aggregate_provenance?: string; replayable?: boolean }; current_activity_id: string | null; activities: Array<{ id: string; sequence_no: number; type: string; title: string; start_at: string; end_at: string; locked: boolean; protected: boolean; metadata: { latitude?: number; longitude?: number; crs?: string; role?: string } }>; legs: Array<{ id: string; from_key: string; to_key: string; mode: string; duration_min: number; provider_key: string; provenance: string; crs: string; geometry: { type: "Feature"; properties?: Record<string, unknown>; geometry: { type: "LineString"; coordinates: number[][] } } }>; user_location: null | { latitude: number; longitude: number; accuracy_m: number; captured_at: string; source: string }; disruptions: Array<{ id: string; type: string; severity: string; status?: string; affected_activity_id: string | null; occurred_at: string; resolved_at?: string | null }> };
  traveler_twin?: { explicit_dimensions: string[]; learned_soft_dimensions: string[]; authority: string; explicit_capabilities?: TravelerCapability[]; capability_summary?: Record<string, unknown> };
  provider_mesh?: Record<string, any>;
  recovery?: RecoveryState | null;
  experience_flags?: {
    needs_review: boolean;
    recovery_required: boolean;
    staleness: boolean;
    feasibility_failures: string[];
  };
};

/**
 * Durable, governed recovery state returned by `/experience` and by the
 * capability confirm endpoints.  Present only when a confirmed HARD capability
 * (or an evidence regression) invalidated the active plan.  The active plan is
 * never silently mutated.
 */
export type RecoveryState = {
  state: "RECOVERY_REQUIRED" | "RECOVERY_REQUIRED_NO_ALTERNATIVE" | "RESOLVED";
  kind: string;
  event_id: string;
  event_status: "DETECTED" | "ACKNOWLEDGED" | "RESOLVED";
  acknowledged: boolean;
  no_alternative: boolean;
  capability_code: string | null;
  active_plan_version_id: string | null;
  failures: string[];
  candidate_plan_count: number;
  candidate_plan_ids: string[];
  requires_user_decision: boolean;
  silent_plan_mutation: false;
  actions: Array<"REPLAN" | "ACKNOWLEDGE_NO_ALTERNATIVE">;
  detected_at: string;
  journey_status?: string;
};

export const v8Modes = ["WALK", "BICYCLE", "TRANSIT", "AUTO", "RIDE_HAIL"] as const;
export type V8Mode = (typeof v8Modes)[number];
