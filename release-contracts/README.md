# CityNexus release-package acceptance contract

Mission 003 uses release-contracts/mission-003.acceptance.json as the package-content source of truth.

The manifest intentionally uses package-relative paths. It is not a claim that the Workspace snapshot itself already contains every required M3 file.

Run:

node release-contracts/verify-release-package.mjs <path-to-release-package>

A package fails when any required executable gate/config is absent or when forbidden transient/dependency/database paths are present.

The <44px mobile tap-target gate is bound to frontend/e2e/qoder-mobile-ui-overnight.spec.ts. Do not rename it during Mission 003.

The USER_CRITICAL_PATH_PRODUCTION_GATE is required. If ORD-0039 has not yet landed its executable spec at frontend/e2e/qoder-user-critical-path.spec.ts, the manifest is expected to remain red. Missing a release gate is not converted into an optional condition merely because packaging happened first.

This verifier checks package contents, not runtime correctness. Commander must still run the authoritative backend/frontend/user gates against the exact packaged candidate and record the real collected/passed/skipped counts.