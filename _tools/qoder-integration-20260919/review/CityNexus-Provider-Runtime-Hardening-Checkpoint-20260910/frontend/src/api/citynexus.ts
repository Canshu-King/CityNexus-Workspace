import type { JourneyTwin } from "../contracts/journeyTwin";
import type { ReplanProposal } from "../contracts/replan";

export interface Money {
  amount_minor: number;
  currency: string;
}

export interface Activity {
  id: string;
  sequence_no: number;
  title: string;
  activity_type: string;
  place_id: string | null;
  city_service_id: string | null;
  start_at: string;
  end_at: string;
  travel_from_prev_min: number;
  estimated_cost: Money;
  status: string;
  locked: boolean;
}

export interface PlanVersion {
  id: string;
  journey_id: string;
  version_no: number;
  planning_mode: string;
  status: string;
  source: string;
  parent_plan_version_id: string | null;
  total_cost: Money;
  utility_score: number | null;
  score_breakdown: Record<string, number> | null;
  activities: Activity[];
}

export interface DemoIds {
  traveler_id: string;
  journey_id: string;
}

export interface Booking {
  id: string;
  journey_id: string;
  activity_id: string | null;
  commitment_id: string | null;
  provider_key: string;
  external_ref: string | null;
  status: string;
  amount: Money;
}

export interface EventRecord {
  id: string;
  journey_id: string;
  occurred_at: string;
  event_type: string;
  affected_activity_id: string | null;
  status: string;
}

export interface AcceptReplanResponse {
  journey: {
    id: string;
    status: string;
    active_plan_version_id: string | null;
    current_activity_id: string | null;
  };
  proposal: ReplanProposal;
  twin: JourneyTwin;
}

export class CityNexusApiError extends Error {
  constructor(
    readonly status: number,
    readonly body: unknown,
    message: string,
  ) {
    super(message);
  }
}

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch("/api/v1" + path, {
    ...init,
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
  });
  const text = await response.text();
  let body: unknown = null;
  if (text) {
    try {
      body = JSON.parse(text);
    } catch {
      body = text;
    }
  }
  if (!response.ok) {
    throw new CityNexusApiError(
      response.status,
      body,
      "CityNexus API " + response.status + ": " + path,
    );
  }
  return body as T;
}

export const cityNexusApi = {
  resetDemo(): Promise<DemoIds> {
    return requestJson<DemoIds>("/demo/reset", { method: "POST" });
  },

  generatePlans(journeyId: string, candidateCount = 1): Promise<PlanVersion[]> {
    return requestJson<PlanVersion[]>("/journeys/" + journeyId + "/plans/generate", {
      method: "POST",
      body: JSON.stringify({ candidate_count: candidateCount }),
    });
  },

  selectPlan(journeyId: string, planId: string): Promise<unknown> {
    return requestJson("/journeys/" + journeyId + "/plans/" + planId + "/select", {
      method: "POST",
    });
  },

  getPlan(planId: string): Promise<PlanVersion> {
    return requestJson<PlanVersion>("/plans/" + planId);
  },

  createBooking(journeyId: string, activityId: string): Promise<Booking> {
    return requestJson<Booking>("/journeys/" + journeyId + "/bookings", {
      method: "POST",
      body: JSON.stringify({ activity_id: activityId }),
    });
  },

  captureBooking(journeyId: string, booking: Booking, idempotencyKey: string): Promise<unknown> {
    return requestJson("/journeys/" + journeyId + "/transactions", {
      method: "POST",
      headers: { "Idempotency-Key": idempotencyKey },
      body: JSON.stringify({
        booking_id: booking.id,
        transaction_type: "CAPTURE",
        amount: booking.amount,
      }),
    });
  },

  startJourney(journeyId: string): Promise<JourneyTwin> {
    return requestJson<JourneyTwin>("/journeys/" + journeyId + "/start", { method: "POST" });
  },

  completeActivity(journeyId: string, activityId: string): Promise<JourneyTwin> {
    return requestJson<JourneyTwin>(
      "/journeys/" + journeyId + "/activities/" + activityId + "/complete",
      { method: "POST" },
    );
  },

  getTwin(journeyId: string, now?: string): Promise<JourneyTwin> {
    const suffix = now ? "?now=" + encodeURIComponent(now) : "";
    return requestJson<JourneyTwin>("/journeys/" + journeyId + "/twin" + suffix);
  },

  createClosureEvent(
    journeyId: string,
    activityId: string,
    occurredAt: string,
  ): Promise<EventRecord> {
    return requestJson<EventRecord>("/journeys/" + journeyId + "/events", {
      method: "POST",
      body: JSON.stringify({
        event_type: "CLOSURE",
        severity: "MAJOR",
        affected_activity_id: activityId,
        occurred_at: occurredAt,
        payload: { reason: "Demo Event Simulator" },
      }),
    });
  },

  generateReplans(
    journeyId: string,
    eventId: string,
    candidateCount = 3,
    idempotencyKey?: string,
  ): Promise<ReplanProposal> {
    return requestJson<ReplanProposal>("/journeys/" + journeyId + "/replans", {
      method: "POST",
      headers: idempotencyKey ? { "Idempotency-Key": idempotencyKey } : undefined,
      body: JSON.stringify({ trigger_event_id: eventId, candidate_count: candidateCount }),
    });
  },

  listReplans(journeyId: string): Promise<ReplanProposal[]> {
    return requestJson<ReplanProposal[]>("/journeys/" + journeyId + "/replans");
  },

  acceptReplan(proposalId: string, idempotencyKey: string): Promise<AcceptReplanResponse> {
    return requestJson<AcceptReplanResponse>("/replans/" + proposalId + "/accept", {
      method: "POST",
      headers: { "Idempotency-Key": idempotencyKey },
    });
  },

  rejectReplan(proposalId: string): Promise<ReplanProposal> {
    return requestJson<ReplanProposal>("/replans/" + proposalId + "/reject", { method: "POST" });
  },
};
