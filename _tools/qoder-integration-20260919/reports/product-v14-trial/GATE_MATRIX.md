# V14 Trial-Readiness Gate Matrix

| Gate | Evidence | Result |
|---|---|---|
| No Tianjin first boot | Fresh browser context at `/v8/hub` | PASS; setup screen shown |
| User-created Journey | Setup form and POST `/api/v1/journeys` | PASS |
| Timezone-aware dates | Selected IANA timezone conversion helper | PASS; build/runtime path exercised |
| Prominent locale switch | Setup and Hub buttons using `LocaleContext` | PASS |
| Locale persistence | `localStorage` plus `html[lang]` browser evaluation | PASS |
| Explicit Tianjin demo | Sealed demo button | PASS |
| Generic discovery default | Fuzhou screen selected `实时供应商` | PASS |
| Wrong-city replay prevention | Focused backend tests and Fuzhou browser result | PASS |
| Human anchor grounding | Arrival location included in live geocoder request path | PASS |
| Sourced query neutrality | Journey city/arrival context replaces hard-coded Tianjin | PASS |
| Generic stay query | `stay-aware journey` schema default | PASS |
| Return to setup | `试用其他城市` from Hub | PASS |
| Existing V14 recovery | Existing grounded recovery test | PASS |
| Focused regression | Trial readiness plus V14 recovery | `4 passed` |
| Broad backend regression | Single convergence run | `392 passed, 2 skipped` |
| Frontend production build | `npm run build` | PASS |
| Browser trial | Playwright `v14trial` | PASS |
| Release hygiene | Staging excludes `.db`, `.db-wal`, `.db-shm`, env files, caches, build output, nested archives | PASS |
| Fresh-extract gate | Target ZIP expanded outside worktree and targeted runtime tests run | PASS after packaging |

