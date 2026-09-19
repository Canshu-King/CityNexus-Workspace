# V12 Third-Party Adoption Record

V12 uses mature libraries where they reduce product risk. No ambiguous-license source was copied.

| Project | Use in V12 | Evidence / ref | Modification |
| --- | --- | --- | --- |
| [openapi-typescript](https://github.com/openapi-ts/openapi-typescript) | Generates `frontend/src/generated/api.ts` from the OpenAPI contract | npm package `openapi-typescript`; regenerated during final validation | Generated output only; no handwritten response-shape copy |
| [TanStack Query](https://github.com/TanStack/query) | Server-state queries, mutations, invalidation | Existing `@tanstack/react-query` dependency | V12 hooks added in `frontend/src/api/v12Authoritative.ts` |
| [dnd-kit](https://github.com/clauderic/dnd-kit) | Trip Studio draft reorder | Existing `@dnd-kit/core` and `@dnd-kit/sortable` dependencies | Existing sortable primitives adapted with V12 labels and draft callbacks |
| [Storybook](https://github.com/storybookjs/storybook) + [MSW](https://github.com/mswjs/msw) | State catalog and deterministic UI fixtures | `V12ExecutionStates.stories.tsx`, `V12StatePrimitives.stories.tsx`, `frontend/src/mocks/handlers.ts` | Added V12 state stories; no production mock path |
| [Lucide](https://github.com/lucide-icons/lucide) | Consistent execution/studio icons | Existing `lucide-react` dependency | Composed icons only |
| [axe-core](https://github.com/dequelabs/axe-core) | Accessibility regression | Existing `@axe-core/playwright`; V10 accessibility E2E | No production changes |
| [Zod](https://github.com/colinhacks/zod) | Existing runtime validation surface | Existing dependency | No new duplicate API model layer |

The 21st.dev Codex plugin and external GitHub metadata service were not callable in this runtime, so no 21st source was copied or represented as adopted. The worktree kept the existing product stack and recorded this limitation instead of inventing a provenance claim.
