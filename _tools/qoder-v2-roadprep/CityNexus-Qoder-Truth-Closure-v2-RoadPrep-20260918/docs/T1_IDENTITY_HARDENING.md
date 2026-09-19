# T1 — Identity Hardening v2

## Keep

- null safety
- exact row ID
- explicit wrapper reference
- provider-scoped identity tuple
- tri-state comparison

## Change

### A. Separate identity from exclusion policy

Preferred API:

- `compare_physical_venue()` -> SAME / DIFFERENT / AMBIGUOUS
- `is_same_physical_venue()` -> true only for SAME
- `should_exclude_replacement_candidate()` -> true for SAME or AMBIGUOUS

The current boolean wrapper conflates "same" with "unsafe to treat as different".

### B. Different provider IDs are not proof of different physical venues

If both provider-scoped identities exist and differ:
- do not immediately return DIFFERENT across different provider namespaces;
- inspect corroborating evidence;
- same/near coordinates + normalized compatible name/category can become
  AMBIGUOUS;
- replacement exclusion then fails safe.

### C. Restrict wrapper parsing

Current uppercase-prefix regex is broad.

Parse only documented CityNexus wrapper forms, not every arbitrary
`UPPERCASE_PREFIX:value`.

### D. Add provider_key / address where available

Use provider_key as structured context rather than relying exclusively on
external_id text.

## New regressions

1. different provider IDs + same venue evidence -> AMBIGUOUS / excluded
2. same provider namespace, different objects, clearly different venue ->
   DIFFERENT
3. arbitrary uppercase external ID must not become a CityNexus wrapper
4. AMBIGUOUS -> `is_same_physical_venue` false
5. AMBIGUOUS -> replacement candidate excluded
