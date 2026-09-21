# Revolution Lab Autonomy Profile

Purpose: give Qoder a concrete low-friction operating model for DeepSeek + Hermes inside the isolated Revolution Lab.

## A. DeepSeek autonomy

DeepSeek gets repo-wide write access INSIDE the lab worktree.

Allowed without per-file approval:
- backend/**
- frontend/**
- contracts/**
- tests/**
- scripts/tools for the lab
- disposable migrations and schema changes
- dependency changes
- removal of obsolete files
- local preview/runtime configuration

DeepSeek may reorganize modules and APIs if the end-to-end product becomes simpler.

Default behavior:
1. inspect the product;
2. pick one high-impact system problem;
3. implement, not memo;
4. run targeted tests;
5. open the product in browser;
6. fix what the user actually sees;
7. commit a coherent milestone;
8. repeat.

Do not require an ORD per micro-change.

## B. Hermes autonomy

Lab Hermes may use broad local engineering tools rather than the narrow production product profile.

Suggested enabled categories in the LAB only:
- filesystem read/write
- terminal/shell
- code execution
- browser automation
- local HTTP requests
- CityNexus MCP
- local logs
- disposable lab DB access
- test runners
- package/dependency inspection

Suggested disabled/blocked even in the lab:
- access to live production DB
- access to real payment/booking systems
- secret-printing/exfiltration
- destructive Git actions against protected/main history

Hermes can propose and execute changes in the lab worktree, then verify the running product.

## C. Two-agent loop

Use a short adversarial loop rather than hierarchical bureaucracy:

DeepSeek Builder:
- chooses architecture;
- implements;
- owns the working branch.

Hermes Operator/Critic:
- runs the product;
- tries realistic journeys;
- inspects failures;
- challenges assumptions;
- suggests or performs local lab fixes when helpful.

Then DeepSeek reviews Hermes findings and either:
- accepts and simplifies;
- rejects with evidence;
- or replaces the design.

Repeat until one of the flagship missions becomes materially better than the authoritative branch.

## D. Permission to break compatibility

Inside the lab, these are acceptable if intentional:
- legacy tests fail because an obsolete interface was removed;
- internal API shape changes;
- current service boundaries disappear;
- old adapters are deleted;
- frontend information architecture changes;
- duplicated AI/direct planning flows are collapsed;
- current Agent Gateway or MCP adapters are replaced by a simpler boundary.

However, any change considered for port-back must explain the migration impact.

## E. Evidence over ceremony

Each meaningful iteration should produce at least one of:
- working route/API;
- visible UI improvement;
- browser trace;
- screenshot;
- benchmark;
- simpler call graph;
- removed duplicate code;
- reproducible failure with exact cause.

Do not create a 20-page architecture report without a running artifact.

## F. Suggested first revolution bets

These are hypotheses, not constraints:

1. Collapse AI planning and direct planning onto one explicit PlanningIntent -> deterministic planner pipeline.
2. Make Destination preparation a first-class async product flow rather than scattered capability/hydration branches.
3. Let Hermes consume one coherent Journey snapshot and a small set of meaningful commands rather than orchestration glue.
4. Replace generic validation/no-op AI outcomes with typed product outcomes that always render visibly.
5. Rebuild the mobile Journey/Map surface using a mature OSS donor structure while keeping CityNexus data semantics.
6. Remove compatibility layers that only exist to preserve abandoned intermediate versions.

The lab is allowed to discover that some of these bets are wrong.

## G. Commit cadence

Commit whenever a coherent product behavior becomes demonstrable.

Recommended milestone commits:
- lab boots
- Mission A first working path
- Mission B natural-language truth
- Mission C Hermes replan
- Mission D mobile UX
- final comparison

Do not squash away the experiment history until review.