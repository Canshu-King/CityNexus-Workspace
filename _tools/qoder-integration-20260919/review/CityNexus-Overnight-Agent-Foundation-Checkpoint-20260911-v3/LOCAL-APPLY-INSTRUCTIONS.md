# CityNexus Next Stage Apply Instructions

Merge the `use-cases/` and `visio-spec/` directories into `D:\moodle\CityNexus\`.

Do not modify `domain-model/` or `requirements/`.

Then run:

```powershell
cd D:\moodle\CityNexus\use-cases
python .\scripts\validate-use-cases.py
python .\scripts\self-test-use-cases-validator.py

cd D:\moodle\CityNexus\visio-spec
python .\scripts\validate-visio-spec.py
```

Expected results:

- Use Case Validator: 16 PASS / 0 FAIL
- Use Case Self-Test: 4 PASS / 0 FAIL
- Visio Spec Validator: 10 PASS / 0 FAIL

After local validation, review `git diff -- use-cases visio-spec`. If only expected files changed, create two commits:

```powershell
git add use-cases
git commit -m "feat(use-cases): establish CityNexus use case baseline v0.1"

git add visio-spec
git commit -m "feat(visio): establish CityNexus Visio model specification v1.0"
```

Do not generate Visio in the same commit. Rendering should start only after both specification commits are clean.
