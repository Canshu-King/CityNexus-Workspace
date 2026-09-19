PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS travelers (
    id TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    email TEXT,
    locale TEXT NOT NULL DEFAULT 'en-GB',
    timezone TEXT NOT NULL DEFAULT 'UTC',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS preferences (
    id TEXT PRIMARY KEY,
    traveler_id TEXT NOT NULL REFERENCES travelers(id) ON DELETE CASCADE,
    category TEXT NOT NULL,
    preference_key TEXT NOT NULL,
    value_json TEXT NOT NULL,
    weight REAL NOT NULL DEFAULT 0.5 CHECK (weight >= 0.0 AND weight <= 1.0),
    source TEXT NOT NULL DEFAULT 'user',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(traveler_id, category, preference_key)
);

CREATE TABLE IF NOT EXISTS journeys (
    id TEXT PRIMARY KEY,
    traveler_id TEXT NOT NULL REFERENCES travelers(id) ON DELETE RESTRICT,
    title TEXT NOT NULL,
    city_code TEXT NOT NULL,
    timezone TEXT NOT NULL,
    start_at TEXT NOT NULL,
    end_at TEXT NOT NULL,
    budget_currency TEXT NOT NULL,
    budget_amount_minor INTEGER NOT NULL CHECK (budget_amount_minor >= 0),
    planning_mode TEXT NOT NULL DEFAULT 'balanced' CHECK (planning_mode IN ('balanced','budget','explore','strict_schedule')),
    status TEXT NOT NULL CHECK (status IN ('DRAFT','PLANNED','ACTIVE','COMPLETED','CANCELLED')),
    active_plan_version_id TEXT REFERENCES plan_versions(id) ON DELETE SET NULL,
    current_activity_id TEXT REFERENCES activities(id) ON DELETE SET NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    CHECK (end_at > start_at)
);

CREATE TABLE IF NOT EXISTS constraints (
    id TEXT PRIMARY KEY,
    journey_id TEXT NOT NULL REFERENCES journeys(id) ON DELETE CASCADE,
    kind TEXT NOT NULL CHECK (kind IN ('HARD','SOFT')),
    category TEXT NOT NULL,
    rule_code TEXT NOT NULL,
    params_json TEXT NOT NULL DEFAULT '{}',
    weight REAL NOT NULL DEFAULT 1.0 CHECK (weight >= 0.0),
    active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0,1)),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS plan_versions (
    id TEXT PRIMARY KEY,
    journey_id TEXT NOT NULL REFERENCES journeys(id) ON DELETE CASCADE,
    version_no INTEGER NOT NULL CHECK (version_no >= 1),
    planning_mode TEXT NOT NULL CHECK (planning_mode IN ('balanced','budget','explore','strict_schedule')),
    status TEXT NOT NULL CHECK (status IN ('CANDIDATE','SELECTED','ACTIVE','SUPERSEDED','REJECTED')),
    source TEXT NOT NULL CHECK (source IN ('INITIAL','REPLAN','MANUAL')),
    parent_plan_version_id TEXT REFERENCES plan_versions(id) ON DELETE SET NULL,
    total_cost_minor INTEGER NOT NULL DEFAULT 0 CHECK (total_cost_minor >= 0),
    currency TEXT NOT NULL,
    estimated_duration_min INTEGER NOT NULL DEFAULT 0 CHECK (estimated_duration_min >= 0),
    utility_score REAL,
    score_breakdown_json TEXT,
    explanation_json TEXT,
    created_at TEXT NOT NULL,
    UNIQUE(journey_id, version_no)
);

CREATE TABLE IF NOT EXISTS places (
    id TEXT PRIMARY KEY,
    provider_key TEXT NOT NULL,
    external_id TEXT NOT NULL,
    city_code TEXT NOT NULL,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    opening_hours_json TEXT NOT NULL DEFAULT '{}',
    tags_json TEXT NOT NULL DEFAULT '[]',
    metadata_json TEXT NOT NULL DEFAULT '{}',
    updated_at TEXT NOT NULL,
    UNIQUE(provider_key, external_id)
);

CREATE TABLE IF NOT EXISTS city_services (
    id TEXT PRIMARY KEY,
    provider_key TEXT NOT NULL,
    external_id TEXT NOT NULL,
    place_id TEXT REFERENCES places(id) ON DELETE SET NULL,
    city_code TEXT NOT NULL,
    service_type TEXT NOT NULL,
    name TEXT NOT NULL,
    availability_json TEXT NOT NULL DEFAULT '{}',
    metadata_json TEXT NOT NULL DEFAULT '{}',
    updated_at TEXT NOT NULL,
    UNIQUE(provider_key, external_id)
);

CREATE TABLE IF NOT EXISTS activities (
    id TEXT PRIMARY KEY,
    plan_version_id TEXT NOT NULL REFERENCES plan_versions(id) ON DELETE CASCADE,
    sequence_no INTEGER NOT NULL CHECK (sequence_no >= 1),
    activity_type TEXT NOT NULL,
    title TEXT NOT NULL,
    place_id TEXT REFERENCES places(id) ON DELETE SET NULL,
    city_service_id TEXT REFERENCES city_services(id) ON DELETE SET NULL,
    start_at TEXT NOT NULL,
    end_at TEXT NOT NULL,
    travel_from_prev_min INTEGER NOT NULL DEFAULT 0 CHECK (travel_from_prev_min >= 0),
    estimated_cost_minor INTEGER NOT NULL DEFAULT 0 CHECK (estimated_cost_minor >= 0),
    currency TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('PLANNED','READY','ACTIVE','COMPLETED','SKIPPED','CANCELLED')),
    locked INTEGER NOT NULL DEFAULT 0 CHECK (locked IN (0,1)),
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(plan_version_id, sequence_no),
    CHECK (end_at > start_at)
);

CREATE TABLE IF NOT EXISTS commitments (
    id TEXT PRIMARY KEY,
    journey_id TEXT NOT NULL REFERENCES journeys(id) ON DELETE CASCADE,
    activity_id TEXT REFERENCES activities(id) ON DELETE SET NULL,
    kind TEXT NOT NULL CHECK (kind IN ('BOOKING','ORDER','PAYMENT','APPOINTMENT','OTHER')),
    level TEXT NOT NULL CHECK (level IN ('C0_Flexible','C1_Preferred','C2_Reserved','C3_Guaranteed','C4_Anchored')),
    status TEXT NOT NULL CHECK (status IN ('PROPOSED','ACTIVE','FULFILLED','CANCELLED','BREACHED')),
    monetary_value_minor INTEGER NOT NULL DEFAULT 0 CHECK (monetary_value_minor >= 0),
    currency TEXT NOT NULL,
    external_ref TEXT,
    policy_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS bookings (
    id TEXT PRIMARY KEY,
    journey_id TEXT NOT NULL REFERENCES journeys(id) ON DELETE CASCADE,
    activity_id TEXT REFERENCES activities(id) ON DELETE SET NULL,
    commitment_id TEXT REFERENCES commitments(id) ON DELETE SET NULL,
    provider_key TEXT NOT NULL,
    external_ref TEXT,
    status TEXT NOT NULL CHECK (status IN ('DRAFT','PENDING','CONFIRMED','COMPLETED','CANCELLED','FAILED')),
    amount_minor INTEGER NOT NULL DEFAULT 0 CHECK (amount_minor >= 0),
    currency TEXT NOT NULL,
    cancellation_policy_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS orders (
    id TEXT PRIMARY KEY,
    journey_id TEXT NOT NULL REFERENCES journeys(id) ON DELETE CASCADE,
    activity_id TEXT REFERENCES activities(id) ON DELETE SET NULL,
    commitment_id TEXT REFERENCES commitments(id) ON DELETE SET NULL,
    provider_key TEXT NOT NULL,
    external_ref TEXT,
    status TEXT NOT NULL CHECK (status IN ('DRAFT','PENDING','CONFIRMED','FULFILLED','CANCELLED','FAILED')),
    amount_minor INTEGER NOT NULL DEFAULT 0 CHECK (amount_minor >= 0),
    currency TEXT NOT NULL,
    items_json TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS transactions (
    id TEXT PRIMARY KEY,
    journey_id TEXT NOT NULL REFERENCES journeys(id) ON DELETE CASCADE,
    booking_id TEXT REFERENCES bookings(id) ON DELETE SET NULL,
    order_id TEXT REFERENCES orders(id) ON DELETE SET NULL,
    provider_key TEXT NOT NULL,
    idempotency_key TEXT NOT NULL,
    transaction_type TEXT NOT NULL CHECK (transaction_type IN ('AUTHORIZE','CAPTURE','REFUND','VOID')),
    status TEXT NOT NULL CHECK (status IN ('INITIATED','AUTHORIZED','SUCCEEDED','FAILED','REFUNDED','VOIDED')),
    amount_minor INTEGER NOT NULL CHECK (amount_minor >= 0),
    currency TEXT NOT NULL,
    external_ref TEXT,
    provider_payload_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(provider_key, idempotency_key)
);

CREATE TABLE IF NOT EXISTS events (
    id TEXT PRIMARY KEY,
    journey_id TEXT NOT NULL REFERENCES journeys(id) ON DELETE CASCADE,
    provider_key TEXT NOT NULL,
    event_type TEXT NOT NULL CHECK (event_type IN ('TRAFFIC_DELAY','CLOSURE','WEATHER','SCHEDULE_DELAY','SERVICE_UNAVAILABLE','USER_CHANGE','OTHER')),
    severity TEXT NOT NULL CHECK (severity IN ('INFO','MINOR','MAJOR','CRITICAL')),
    status TEXT NOT NULL CHECK (status IN ('DETECTED','ACKNOWLEDGED','RESOLVED','IGNORED')),
    affected_activity_id TEXT REFERENCES activities(id) ON DELETE SET NULL,
    occurred_at TEXT NOT NULL,
    detected_at TEXT NOT NULL,
    resolved_at TEXT,
    payload_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS replan_proposals (
    id TEXT PRIMARY KEY,
    journey_id TEXT NOT NULL REFERENCES journeys(id) ON DELETE CASCADE,
    trigger_event_id TEXT REFERENCES events(id) ON DELETE SET NULL,
    base_plan_version_id TEXT NOT NULL REFERENCES plan_versions(id) ON DELETE RESTRICT,
    proposed_plan_version_id TEXT NOT NULL REFERENCES plan_versions(id) ON DELETE RESTRICT,
    status TEXT NOT NULL CHECK (status IN ('GENERATED','PRESENTED','ACCEPTED','REJECTED','EXPIRED','INVALIDATED')),
    hard_constraints_passed INTEGER NOT NULL CHECK (hard_constraints_passed IN (0,1)),
    locked_commitments_preserved INTEGER NOT NULL CHECK (locked_commitments_preserved IN (0,1)),
    utility_score REAL NOT NULL,
    score_breakdown_json TEXT NOT NULL,
    diff_json TEXT NOT NULL,
    explanation_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    decided_at TEXT,
    CHECK (base_plan_version_id <> proposed_plan_version_id)
);

CREATE TABLE IF NOT EXISTS recommendations (
    id TEXT PRIMARY KEY,
    traveler_id TEXT NOT NULL REFERENCES travelers(id) ON DELETE CASCADE,
    journey_id TEXT REFERENCES journeys(id) ON DELETE CASCADE,
    plan_version_id TEXT REFERENCES plan_versions(id) ON DELETE CASCADE,
    kind TEXT NOT NULL CHECK (kind IN ('PLACE','ACTIVITY','PLAN','REPLAN_EXPLANATION')),
    source TEXT NOT NULL CHECK (source IN ('RULES','AI','HYBRID')),
    score REAL,
    explanation TEXT,
    payload_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS journey_twins (
    journey_id TEXT PRIMARY KEY REFERENCES journeys(id) ON DELETE CASCADE,
    active_plan_version_id TEXT REFERENCES plan_versions(id) ON DELETE SET NULL,
    current_activity_id TEXT REFERENCES activities(id) ON DELETE SET NULL,
    latest_event_id TEXT REFERENCES events(id) ON DELETE SET NULL,
    projection_status TEXT NOT NULL CHECK (projection_status IN ('READY','STALE','DEGRADED')),
    snapshot_at TEXT NOT NULL,
    context_json TEXT NOT NULL DEFAULT '{}',
    upcoming_commitments_json TEXT NOT NULL DEFAULT '[]',
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS provider_calls (
    id TEXT PRIMARY KEY,
    provider_key TEXT NOT NULL,
    operation TEXT NOT NULL,
    request_json TEXT NOT NULL,
    response_json TEXT,
    status TEXT NOT NULL CHECK (status IN ('SUCCESS','FAILURE','TIMEOUT','DEGRADED')),
    latency_ms INTEGER,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id TEXT PRIMARY KEY,
    actor_type TEXT NOT NULL,
    actor_id TEXT,
    journey_id TEXT,
    action TEXT NOT NULL,
    entity_type TEXT,
    entity_id TEXT,
    before_json TEXT,
    after_json TEXT,
    trace_id TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS idempotency_keys (
    key TEXT PRIMARY KEY,
    operation TEXT NOT NULL,
    request_hash TEXT NOT NULL,
    response_status INTEGER,
    response_json TEXT,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_journeys_traveler ON journeys(traveler_id);
CREATE INDEX IF NOT EXISTS idx_plan_versions_journey ON plan_versions(journey_id, version_no);
CREATE INDEX IF NOT EXISTS idx_activities_plan ON activities(plan_version_id, sequence_no);
CREATE INDEX IF NOT EXISTS idx_commitments_journey ON commitments(journey_id, status, level);
CREATE INDEX IF NOT EXISTS idx_events_journey ON events(journey_id, detected_at);
CREATE INDEX IF NOT EXISTS idx_replans_journey ON replan_proposals(journey_id, created_at);
CREATE INDEX IF NOT EXISTS idx_audit_journey ON audit_logs(journey_id, created_at);
