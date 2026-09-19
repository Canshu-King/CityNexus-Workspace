# Provider capture and replay evidence

`scripts/capture_trip_provider_snapshot.py` captures normalized mobility facts and writes only redacted evidence. It labels configured Valhalla output `LIVE_CAPTURE` and the default deterministic mock `SYNTHETIC_FIXTURE`; it never calls a synthetic formula `CAPTURED_REPLAY`.

`backend/app/integrations/mobility/replay.py` verifies the sealed checksum, validates provenance, and passes the facts through `MobilitySnapshot.from_evidence`, the same normalizer used by the deterministic feasibility gate. Synthetic data is rejected by replay unless an explicit test-only allow flag is supplied.

Current provider status:

- live Valhalla: `NOT_CONFIGURED`;
- Amap: `NOT_CONFIGURED` in the local profile;
- OTP/GTFS-RT: `NOT_CONFIGURED`, with realtime absence represented as `UNKNOWN_REALTIME`;
- deterministic fixture/replay path: green and auditable.

