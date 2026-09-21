# Revolution Lab First Shift

Date: 2026-09-22
Lane: REVOLUTION-LAB-001
Parent authoritative code SHA: f2708dd
Purpose: turn the charter into a running experiment quickly, without importing authoritative-line bureaucracy into the lab.

## 0. Isolation proof before coding

Record these facts in the lab running log before the first edit:

- worktree path = D:\moodle\CityNexus-RevolutionLab
- branch = experiment/deepseek-hermes-revolution
- parent = f2708dd
- disposable DB path / connection
- disposable preview port
- live preview DB is not reachable from the lab configuration
- no production/payment/booking credentials are present in the lab process
- authoritative worktree is read-only from this lane

If any one of these is unknown, stop only long enough to resolve the isolation fact. Do not turn this into a general audit.

## 1. First mission: unseen destination

Start with Mission A only. Do not split DeepSeek and Hermes across all four flagship missions at once.

Target path:

raw unseen destination
-> resolve
-> prepare
-> usable truthful plan OR exact blocker
-> visible mobile state

Use a destination that is not preseeded in the disposable lab DB.

### DeepSeek Builder

DeepSeek owns implementation.

Its first loop is:

1. run the current lab product once from the user's normal entry path;
2. identify the smallest critical-path architecture that prevents unseen-destination success;
3. simplify or replace that architecture directly;
4. boot the product;
5. repeat the same journey;
6. commit a coherent runnable milestone.

DeepSeek may replace service boundaries, state flow, provider orchestration, destination preparation, planner entrypoints, or UI state ownership if that produces a simpler coherent product.

Do not spend the first shift writing an architecture memo.

### Hermes Operator/Critic

Hermes owns adversarial use of the running lab product.

For each DeepSeek milestone Hermes must:

- enter through the visible product first;
- attempt one unseen destination from blank/disposable state;
- inspect the visible state transition;
- inspect logs/API/DB only to explain what the product actually did;
- distinguish structural no-match from provider/runtime failure;
- challenge any hidden mock, silent fallback, hash/pending identity, or duplicated planner path;
- hand DeepSeek one ranked finding set tied to reproducible evidence.

Hermes may make local lab fixes when that is faster, but DeepSeek reviews the resulting architecture before the next milestone.

## 2. Product truth for the lab experiment

The lab is allowed to redesign internal contracts, but Mission A evidence is not accepted if it only changes labels.

A valid milestone must show one of:

- a truthful usable plan for an unseen destination; or
- the first exact blocker reached through the visible product.

The following do not count as success by themselves:

- provider-only MATCH;
- direct DB insertion of canonical identity;
- direct API-only success when the visible product cannot reach it;
- a mock/frozen fixture silently presented as live evidence;
- a generic network error replacing a known structural state;
- a SELECTABLE result whose used places/edges cannot be explained.

## 3. Evidence receipt for each lab milestone

Keep it compact:

```text
lab_commit
parent
user_entry_path
destination_raw
preseed_check
visible_state_sequence
provider_mode
canonical_identity_result
catalog/preparation_result
planner_result
first_blocker_if_any
time_to_first_usable_or_blocker
files_or_modules_removed_or_collapsed
browser_or_screenshot_evidence
Hermes_findings
DeepSeek_response
```

No giant report bundle.

## 4. First-shift time discipline

Target, not a hard timeout:

- first 15 minutes: isolation + one baseline journey;
- next 30 minutes: first implementation change and boot;
- by ~60 minutes: first visible re-run;
- by ~90 minutes: one committed product milestone or one exact architectural blocker.

If blocked for more than 15 minutes on setup, switch to another implementation route that still advances Mission A. Do not spend the night perfecting the lab harness.

## 5. Comparison discipline

Do not compare the lab to the authoritative branch by legacy pass count.

For Mission A compare:

- steps from raw input to usable plan/blocker;
- time to first usable result;
- number of duplicated truth transitions;
- number of hidden fallbacks;
- failure transparency;
- visible mobile usability;
- critical-path code complexity.

A smaller architecture that is equally truthful is a win candidate.
A prettier UI with weaker truth is not.

## 6. When Mission A is coherent

Only after Mission A has a runnable milestone should the lab move to:

1. Mission B: natural-language budget truth;
2. Mission C: disruption + protected commitment;
3. Mission D: 390x844 mobile flow.

If Mission A discovers a reusable simplification, carry that architecture forward rather than opening four unrelated rewrites.

## 7. Port-back rule

Do not merge the lab wholesale.

Any candidate worth porting back must later be reduced to:

- the specific winning behavior;
- migration impact;
- authoritative truth contracts it preserves or replaces;
- targeted evidence proving the win.

The lab discovers. The authoritative line arbitrates.
