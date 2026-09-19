# WP06 deterministic core — target architecture

## Non-negotiable execution rule

A ReplanProposal is not a second free-form itinerary generator. It is an evidence-backed replacement for the *remaining executable suffix* of an ACTIVE Journey.

## Snapshot

Capture, at one logical decision point:

- Journey + active PlanVersion;
- current Activity/execution position;
- completed/terminal prefix;
- active constraints;
- active C4 Commitments from durable commerce policy;
- trigger Event;
- Place/CityService availability;
- frozen mobility facts;
- optional context facts.

## Partition

```text
terminal prefix     -> immutable history
current execution   -> preserve/remap unless disruption explicitly invalidates it
C4 anchors          -> hard pinned
mutable suffix      -> replan search space
```

## Candidate families

Implement in this order:

### F0 Minimal replacement

Replace only the directly disrupted flexible Activity while preserving times of every later protected anchor.

Canonical witness:

```text
Tech Art Center CLOSED
13:20 Tech Art Center -> 13:20 Design Library
15:30 River Cruise C4 unchanged
```

### F1 Remove disrupted optional Activity

Only if removal keeps all hard constraints feasible and no C4 is lost.

### F2 Shift flexible suffix

Useful for delay events. Never shift a C4 anchor.

### F3 Alternative Place in the same Opportunity Window

Use verified place availability + frozen travel estimates.

### F4 Advanced solver candidate

Only after F0-F3 and the deterministic gate are stable. OR-Tools may propose a candidate, but it never replaces the authoritative gate.

## Required gate before proposal persistence

Every candidate must pass:

- Journey time window;
- activity validity/non-overlap;
- opening/service availability;
- frozen travel-gap checks;
- budget/currency;
- all hard Journey constraints;
- every durable active C4 anchor;
- current execution-position compatibility.

## ReplanDiff

Persist deterministic evidence:

- kept;
- moved;
- removed;
- added;
- preserved protected commitments;
- cost delta;
- travel delta when mobility snapshot exists;
- end-time delta;
- before/after FeasibilityEnvelope;
- reason codes.

## Acceptance

Immediately before activation:

1. confirm Journey is still ACTIVE;
2. confirm base plan is still active;
3. re-run proposed-plan feasibility against **current** authoritative facts;
4. re-check C4 preservation;
5. remap current activity/execution position;
6. supersede base + activate proposal + update Journey + Twin atomically;
7. audit once.

Do not accept stale proposals because they happened to be feasible when generated.
