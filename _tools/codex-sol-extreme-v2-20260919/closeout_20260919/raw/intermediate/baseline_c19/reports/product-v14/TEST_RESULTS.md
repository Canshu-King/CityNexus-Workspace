# V14 Test and Release Results

Runtime labels: local Windows worktree, Python backend, Vite frontend, Playwright Chromium, Asia/Shanghai time. No external live provider or model key was configured for this run.

## Focused implementation runs

Focused recovery/provider/weather tests were run during implementation. The final focused set after the concrete legacy compatibility correction was green: `25 passed`.

## Broad backend convergence

The single convergence backend regression completed with:

```text
390 passed, 2 skipped, 2 warnings in 40.42s
```

## Frontend convergence

The final production build completed successfully:

```text
vite v7.3.6
1899 modules transformed
✓ built in 5.21s
PWA precache generated
```

The build emitted the existing large-chunk warning for the main JavaScript bundle; it did not fail the build.

## Playwright Golden

Session `v14` exercised:

1. authoritative execution page;
2. fully grounded selected journey;
3. executed arrival;
4. sealed weather disruption;
5. recovery proposal with provider and deterministic evidence;
6. accepted child PlanVersion;
7. offline reload to the saved read-only Journey snapshot;
8. online restoration.

## Fresh-extract release gate

The final artifact is expanded into a new directory outside the repository. The fresh copy runs the targeted V14 backend runtime test, not merely an inventory or import check. The post-package gate is recorded as PASS in the release result and final response.

## Secret and artifact handling

The release staging procedure excludes `.git`, virtual environments, dependency caches, databases, SQLite files, frontend build output, Playwright output, environment files, nested archives, and other generated caches. No API key is included in source, reports, or the final ZIP.

