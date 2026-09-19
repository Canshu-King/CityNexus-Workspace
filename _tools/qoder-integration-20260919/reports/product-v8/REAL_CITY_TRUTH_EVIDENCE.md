# Real-city truth and provider status

V8 preserves the V6 real-city truth boundary. The product distinguishes captured evidence from live provider state rather than presenting fixtures as live data.

| Surface | Current V8 status | Truth boundary |
|---|---|---|
| Tianjin stay offers | `CAPTURED_REPLAY` | Immutable local offer snapshots with explicit CNY/cancellation/expiry evidence |
| Tianjin mobility matrix | `CAPTURED_REPLAY` | Frozen mode facts; unknown WALK fare remains unknown |
| Live hotel adapter | `NOT_CONFIGURED` | The provider seam exists; no live credential is claimed |
| Valhalla routing | `NOT_CONFIGURED` | No live route or fare is invented |
| OpenTripPlanner / transit | `NOT_CONFIGURED` | Transit is valid in the replay only where captured provider facts exist |
| Ride-hail | `CAPTURED_REPLAY` | Captured estimate only; not a live quote |
| Nominatim / Overpass | inherited V6 captured/replay boundary | Place discovery remains provenance-bearing; no room price is sourced from OSM |

The V8 gate is therefore a truthful captured/replay product path. Live provider gates are not promoted to PASS by inference.

