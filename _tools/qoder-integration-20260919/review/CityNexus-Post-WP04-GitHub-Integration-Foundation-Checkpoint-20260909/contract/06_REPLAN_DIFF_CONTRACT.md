# ReplanDiff contract

Treat the difference between old and proposed plan as a first-class deterministic object.

Required fields:
- kept activities;
- moved activities;
- removed activities;
- added activities;
- preserved protected commitments;
- cost delta;
- travel delta when available;
- schedule-end delta;
- risk/reason-code delta;
- before/after feasibility envelope.

This object drives:
- ReplanProposal UI;
- audit evidence;
- AI explanation;
- Playwright assertions;
- coursework screenshots.

Do not ask the AI to infer the diff from two free-form itineraries.
