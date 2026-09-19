# GPT Review Package

Review the P1 use-case route candidate against `visio-spec/pages/p1_uc_overview.yaml`.

Run from `visio-renderer`:

```powershell
python -m pytest .\tests -q
python .\calibration\validate_p1_route_candidate_v2.py
```

The package records the current failing Contact Gate state. `MANIFEST.json` contains the size and SHA-256 for every packaged file.
