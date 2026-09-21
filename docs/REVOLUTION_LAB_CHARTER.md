# CityNexus Revolution Lab Charter

Date: 2026-09-22
Lane: REVOLUTION_LAB
Intent: deliberately relax CityNexus implementation constraints inside an isolated branch/worktree and let DeepSeek + Hermes redesign the product architecture from first principles.

## 1. Why this lane exists

The authoritative CityNexus line has accumulated many correctness contracts, compatibility rules, ownership splits, migration constraints, and historical design decisions. Those protections are valuable for production truth, but they can also make architectural change slow.

This lane asks a different question:

If a capable engineering agent were given the current product, current tests, current user pain, current provider reality, and broad engineering freedom, what simpler and better CityNexus would it build?

The purpose is NOT to weaken the authoritative branch. The purpose is to create a competing experimental branch and compare outcomes.

## 2. Branch/worktree isolation

Commander should create a local code branch/worktree from the CURRENT authoritative CityNexus tip at the moment this experiment begins.

Suggested branch: experiment/deepseek-hermes-revolution
Suggested worktree: D:\moodle\CityNexus-RevolutionLab\

Record the exact parent SHA.

Use a disposable database and disposable preview runtime.

Never point Revolution Lab at the user's live preview DB.

## 3. Permissions inside the lab

Inside the isolated branch/worktree, DeepSeek and Hermes are intentionally granted broad engineering autonomy.

They MAY:
- read and edit the whole repository;
- delete obsolete abstractions;
- refactor across backend/frontend/contracts/tests;
- change internal APIs;
- replace architecture;
- rewrite state flow;
- simplify or merge services;
- remove redundant compatibility layers;
- add/remove dependencies;
- install development dependencies locally;
- run shell commands;
- run tests;
- launch local services;
- use browser automation against the lab preview;
- use filesystem tools;
- inspect local logs;
- use the disposable lab database directly;
- create migrations for the lab DB;
- seed/reset the lab DB;
- build new UI;
- import or adapt compatible open-source UI components with attribution;
- use Hermes MCP and non-MCP engineering tools inside the lab;
- create new tools if they materially simplify the product;
- run autonomous multi-step loops;
- critique their own earlier design and replace it.

They do NOT need to preserve historical internal APIs merely because the authoritative branch currently has them.

They should prefer a simpler working end-to-end design over preserving a complicated abstraction that exists only because of project history.

## 4. Only four hard blast-radius boundaries

The lab has fewer rules. These four remain non-negotiable because they protect assets outside the experiment:

1. Do not modify the authoritative/main worktree or published protected history.
2. Do not connect destructive actions to the user's live preview database or real user data.
3. Do not expose, commit, print, or copy secrets into reports/issues/repository history.
4. Do not execute real-money, real-booking, irreversible external-world actions.

Everything else inside the disposable lab is open to redesign.

## 5. DeepSeek role

DeepSeek acts as the principal autonomous software architect/implementer.

It should:
- inspect current product pain;
- identify unnecessary complexity;
- choose a simpler architecture;
- implement it directly;
- run the product;
- use browser/API evidence;
- iterate instead of writing long speculative reports.

DeepSeek is explicitly allowed to disagree with the authoritative architecture.

It may decide that existing boundaries, schemas, modules, or flow control should be removed or replaced.

## 6. Hermes role

Hermes acts as both product-internal autonomous Agent and engineering operator inside the lab.

Unlike the authoritative product profile, the lab Hermes may be given broad local tools:
- terminal;
- filesystem;
- browser;
- code execution;
- lab DB;
- local HTTP;
- CityNexus MCP;
- engineering scripts.

This is intentional.

The experiment should test whether a more capable Hermes can:
- inspect current state;
- reason over the Journey;
- request or perform safe lab-side changes;
- diagnose failures;
- improve the product;
- operate the travel workflow with less orchestration glue.

Do not confuse this broad LAB authority with production authority.

## 7. The self-revolution rule

DeepSeek and Hermes are allowed to challenge these assumptions if evidence says they are harming the product:
- current page structure;
- current Agent Gateway shape;
- current MCP boundary;
- current planner orchestration;
- current JourneyTwin presentation;
- current Simulation architecture;
- current provider hydration design;
- current frontend state architecture;
- current service boundaries;
- current test organization;
- current error taxonomy;
- current UI navigation;
- current dependency choices.

They may preserve ideas that are good and discard ones that are not.

The lab should not optimize for small diff.

It should optimize for:
- product coherence;
- visible usefulness;
- maintainability;
- real end-to-end behavior;
- less duplicated truth;
- fewer split-brain flows;
- fewer silent failures.

## 8. Product goals

The Revolution Lab should attack the biggest user-visible/product-level weaknesses, not polish internal abstractions for their own sake.

### Mission A — unseen destination
User enters a previously unseeded destination.
The product should:
- understand the place;
- prepare real city data;
- show progress;
- produce a truthful usable plan or a clear named blocker;
- avoid hash identities and fake success.

### Mission B — natural-language planning
Input example:
两个人三天全部加起来别超过一千六百块，想睡懒觉，喜欢夜景、酒吧和特色美食。

The product should:
- preserve 1600 CNY as actual total budget;
- preserve party size and trip scope;
- not silently convert unknown values to zero;
- produce a useful plan or explicit reason.

### Mission C — disruption with commitment
Create a real lab Journey with a protected commitment.
Trigger a disruption.
Hermes/CityNexus should:
- explain impact;
- produce alternatives;
- preserve the commitment;
- accept a valid replan;
- show the new Now/Next truthfully.

### Mission D — mobile product quality
A user on 390x844 should be able to:
- create/select a Journey;
- understand Today / Now / Next;
- use the map;
- see an event;
- understand a replan;
- inspect booking/wallet state;
- use AI without silent no-op behavior.

## 9. OSS UI donor freedom

The lab may aggressively borrow/adapt from compatible open-source projects.

Preferred references already researched:
- stvlynn/OpenTrip
- clawnify/OpenTripPlanner
- shusingh/michi-planner
- Serkanbyx/travel-planner

The lab may replace major frontend sections if that gets to a better product faster.

Keep source/license attribution.

Do not import AGPL code unless Commander explicitly chooses to accept the licensing consequence.

## 10. How to judge the experiment

Do NOT judge the lab primarily by how many authoritative-branch tests it passes.

Judge it by side-by-side product evidence.

Required comparison against the current authoritative branch:
1. unseen destination from blank state;
2. natural-language budget plan;
3. disruption + protected commitment + replan;
4. mobile 390x844 end-to-end;
5. failure transparency;
6. time-to-first-usable-result;
7. amount of duplicated planner/Agent logic;
8. code complexity of the critical path.

The lab may initially fail legacy tests if it replaces obsolete behavior. It should add its own coherent tests for the new design.

## 11. Anti-bureaucracy rule

Do not spend the experiment creating dozens of new ORD numbers.

Use one lane, one task board, and a short running log.

Do not stop after a design memo.

Every architectural claim should quickly become code, running product, screenshot/trace, or a reproducible blocker.

Prefer 30 minutes of implementation to 30 minutes of policy prose.

## 12. Iteration loop

Use this loop repeatedly:
1. inspect current behavior;
2. choose one painful system-level problem;
3. simplify or replace the design;
4. implement;
5. run;
6. use the product like a user;
7. let Hermes critique it;
8. let DeepSeek improve it;
9. commit;
10. compare to authoritative branch.

DeepSeek and Hermes should be allowed to critique each other's work.

## 13. Morning deliverable

Create REVOLUTION_LAB_MORNING_REPORT.md.

Keep it concise.

Include:
- parent authoritative SHA;
- lab branch/worktree;
- major architecture changes;
- major files deleted/replaced;
- working demo URL if available;
- Mission A result;
- Mission B result;
- Mission C result;
- Mission D result;
- before/after screenshots;
- Hermes autonomy result;
- tests actually run;
- failures still present;
- what is clearly better than authoritative;
- what is worse;
- 3 to 8 candidate changes worth porting back.

Do not recommend merging the whole branch automatically.

The point is to discover better architecture and product ideas, then selectively port what wins.

## 14. Success condition

A successful Revolution Lab does NOT need to prove that the authoritative architecture was wrong.

It succeeds if by morning it produces at least one of:
- a substantially better end-to-end product path;
- a simpler architecture with equal truthfulness;
- a visibly better mobile product with real backend behavior;
- a Hermes-driven workflow that removes orchestration complexity;
- a concrete proof that an existing major abstraction should be removed;
- a candidate implementation clearly worth cherry-picking.

The experiment should be ambitious enough that the answer might genuinely surprise us.