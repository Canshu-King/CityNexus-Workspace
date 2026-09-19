# Projection Divergence Report

The final real-persistence differential oracle executed seven cases:

1. null cursor, all pending;
2. null cursor, first terminal then pending;
3. valid first cursor;
4. valid middle cursor;
5. valid final cursor;
6. present-but-unknown cursor;
7. no activities.

Result: **0 divergences** across authoritative persistence, `/experience`, JourneyTwin, offline snapshot, and execution clock fields covered by the oracle.

The Live browser gate separately executed the six requested UI cases and passed 6/6. Unknown cursor rendered no fabricated current activity, next activity, or leg duration.

Machine evidence: `raw/final/projection_oracle.json`; browser evidence: `raw/final/browser_projection.log`.
