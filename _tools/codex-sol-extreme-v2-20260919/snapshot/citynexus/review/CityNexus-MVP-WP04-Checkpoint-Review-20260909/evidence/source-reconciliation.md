# WP04 frozen-domain source reconciliation

Source read: `domain-model/citynexus-core-domain-model-v0.4.2.yaml`  
Read method: supplied `tools/extract_wp04_domain_enums.py`  
Purpose: authoritative WP04 source values only; no inferred labels.

```yaml
commitment_strength:
  yaml_path: enums.commitment_strength
  values:
    - C0_Flexible
    - C1_Preferred
    - C2_Reserved
    - C3_Guaranteed
    - C4_Anchored
commitment_source_type:
  yaml_path: enums.commitment_source_type
  values:
    - user_lock
    - booking
    - payment
    - external_schedule
```

The exact strength tuple is generated into
`backend/app/commerce/strengths_generated.py`; the exact source-type tuple is
kept in `backend/app/commerce/source_types_generated.py`.
