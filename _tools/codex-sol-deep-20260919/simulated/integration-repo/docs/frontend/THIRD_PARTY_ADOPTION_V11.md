# Third-party adoption — V11

The V11 UI uses maintained projects where they reduce product risk, and records
the boundary instead of copying unlicensed examples.

| Project | Ref used | License/source | CityNexus use |
|---|---|---|---|
| `clauderic/dnd-kit` | npm `@dnd-kit/core`, `@dnd-kit/sortable` | MIT | Trip Studio drag creates a local draft reorder and preview callback; it does not mutate the active plan. |
| `TanStack/query` | `@tanstack/react-query` already pinned | MIT | ExecutionClock and web evidence are server-state queries with freshness/error state. |
| `lucide-icons/lucide` | `lucide-react` already pinned | ISC | consistent product icon language. |
| `storybookjs/storybook` | Storybook 9.x already pinned | MIT | state-driven component catalog and build gate. |
| `openapi-ts/openapi-typescript` | `frontend/src/generated/api.ts` | MIT | ExecutionClock response is derived from the generated operation type. |
| `react-hook-form` / `zod` | npm dependencies added in V11 | MIT | available for imported booking and policy forms; imported payload validation remains explicit. |
| `21st-dev/codex-plugin` | direct MCP search used in V10/V11 | source search only | component alternatives/inspiration; no ambiguous-license code copied. |

Optional provider evaluation: `searxng/searxng` is represented by the
sourceful adapter in `backend/app/integrations/web/searxng.py`; it is not a
mandatory deployment dependency and DeepSeek built-in search remains the
fallback.
