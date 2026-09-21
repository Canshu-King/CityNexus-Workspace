# Aggregate Evidence Resample Receipt

Purpose: prevent old aggregate mobility counts from being repeated after their source, schema, or sampling command can no longer be reproduced.

This does not change the blocker rule. Aggregate counts remain background/risk context only. Candidate blockers must come from the candidate's actual `used_edge_ids` inventory.

## 1. Required provenance for any aggregate count

Any report such as:

`explicit=144 / synthetic_default=184 / unknown=91 / frozen=24`

must carry all of:

```text
source_repository_or_worktree
source_ref_or_sha
source_path
source_file_sha256_or_blob
source_schema_or_key_path
sampling_command_or_query
sampling_population_definition
row_count_before_filter
row_count_after_filter
sampled_at
result_counts
```

Without these fields, the number is historical anecdote, not resampled evidence.

## 2. Resample states

Use exactly one:

```text
RESAMPLED_EXACT
RESAMPLED_EQUIVALENT_SOURCE
NOT_RESAMPLED_SOURCE_MISSING
NOT_RESAMPLED_SCHEMA_MISMATCH
NOT_RESAMPLED_SOURCE_AMBIGUITY
HISTORICAL_UNVERIFIED
```

`RESAMPLED_EQUIVALENT_SOURCE` requires an explicit explanation of why the new source is semantically equivalent to the old source.

## 3. Source ambiguity handling

If the remembered path does not exist, or a nearby file lacks the required schema/key, do not substitute it merely because the filename looks plausible.

Example:

- expected source missing;
- nearby matrix exists but lacks `fact_quality`;
- another file contains `fact_quality` but is a narrow Tianjin journey snapshot;

then the correct result is:

`NOT_RESAMPLED_SOURCE_AMBIGUITY`

not a reconstructed aggregate count.

## 4. Blocker firewall

Even a perfectly resampled aggregate count cannot prove:

`MOBILITY_EVIDENCE_NOT_HARD_ELIGIBLE`

for a specific candidate.

That blocker still requires:

```text
candidate_id
used_edge_ids
per_edge_source_kind
per_edge_fact_quality
per_edge_hard_eligible
first_blocking_edge_or_edges
blocker_basis = USED_EDGE_INVENTORY
aggregate_repository_counts_used_as_blocker = false
```

Aggregate evidence may appear only in a separate background/risk field.

## 5. Morning-report wording

When a historical aggregate cannot be reproduced, prefer:

`NOT-RESAMPLED(source ambiguity; non-blocking background only)`

Do not silently delete the old number if it mattered historically, but do not present it as current truth either.

## 6. Frozen rule

> A remembered number without a reproducible source is history, not current evidence. Aggregate evidence may predict risk; only candidate used-edge evidence may prove the blocker.
