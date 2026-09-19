"""Append the shared protected-commitment helper to the journey fixture.

Done as a file edit in Python because the spec files in this tree carry CRLF line
endings, which makes naive exact-match edits fail for reasons unrelated to the
change.
"""

import io

PATH = "frontend/e2e/_qoderFreshJourney.ts"
src = io.open(PATH, encoding="utf-8", newline="")
text = src.read()
src.close()

if "protectCommitment" in text:
    print("already patched")
    raise SystemExit(0)

# 1. let post() carry headers (the transaction endpoint needs an Idempotency-Key)
old_post = """async function post(request: APIRequestContext, url: string, data?: unknown) {
  const res = await request.post(`${API}${url}`, { data });"""
new_post = """async function post<T = any>(
  request: APIRequestContext,
  url: string,
  data?: unknown,
  headers?: Record<string, string>,
): Promise<T> {
  const res = await request.post(`${API}${url}`, { data, headers });"""
assert old_post in text, "post() helper shape changed; re-read before editing"
text = text.replace(old_post, new_post, 1)

# 2. get() must accept a type argument for the new helper
old_get = """async function get(request: APIRequestContext, url: string) {
  const res = await request.get(`${API}${url}`);"""
new_get = """async function get<T = any>(request: APIRequestContext, url: string): Promise<T> {
  const res = await request.get(`${API}${url}`);"""
assert old_get in text, "get() helper shape changed; re-read before editing"
text = text.replace(old_get, new_get, 1)

helper = '''
export type ProtectedCommitment = {
  activityId: string;
  placeId: string;
  bookingId: string;
  commitmentId: string | null;
  amount: unknown;
};

/**
 * Create a real protected commitment through the path a traveller would use.
 *
 * Measured, not assumed: on the demo plan the cruise activity is `locked: true`
 * but `protected: false` until a booking exists and its payment is captured —
 * `protected` is derived from ACTIVE Commitment rows.  So a spec that asserts
 * "the protected commitment survived the recovery" without creating one is
 * asserting on a fixture that has nothing to protect, and the flag it reads is
 * true for the wrong reason.
 *
 * Must run before `/start`: booking an activity on a journey that is already
 * travelling is refused with 422.
 */
export async function protectCommitment(
  request: APIRequestContext,
  journeyId: string,
  placeId = "place-river-cruise",
): Promise<ProtectedCommitment> {
  const experience = await get<{ active_plan?: { activities?: any[] } }>(
    request,
    `/api/v1/journeys/${journeyId}/experience`,
  );
  const activity = (experience.active_plan?.activities ?? []).find(
    (item) => item.place_id === placeId,
  );
  if (!activity) {
    throw new Error(`no activity for ${placeId} on journey ${journeyId} to protect`);
  }

  const booking = await post<{
    id: string;
    commitment_id?: string | null;
    amount?: unknown;
  }>(request, `/api/v1/journeys/${journeyId}/bookings`, { activity_id: activity.id });
  await post(
    request,
    `/api/v1/journeys/${journeyId}/transactions`,
    { booking_id: booking.id, transaction_type: "CAPTURE", amount: booking.amount },
    { "Idempotency-Key": `protect-${booking.id}` },
  );

  /* Prove it landed before anything else leans on it. */
  const after = await get<{ active_plan?: { activities?: any[] } }>(
    request,
    `/api/v1/journeys/${journeyId}/experience`,
  );
  const projected = (after.active_plan?.activities ?? []).find(
    (item) => item.place_id === placeId,
  );
  if (!projected?.protected) {
    throw new Error(
      `booking ${booking.id} + CAPTURE did not make ${placeId} a protected commitment ` +
        `(locked=${projected?.locked}, protected=${projected?.protected})`,
    );
  }

  return {
    activityId: activity.id,
    placeId,
    bookingId: booking.id,
    commitmentId: booking.commitment_id ?? null,
    amount: booking.amount,
  };
}
'''

text = text.rstrip("\r\n") + "\n" + helper
io.open(PATH, "w", encoding="utf-8", newline="").write(text)
print("appended protectCommitment to", PATH)
