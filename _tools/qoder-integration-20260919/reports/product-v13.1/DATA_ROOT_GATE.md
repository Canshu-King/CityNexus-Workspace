# V13.1 Canonical Data-Root Gate

## Required invariant

The release has one canonical runtime/test fixture tree at
`<repository>/data`. The final archive does not depend on an untracked
`backend/data` duplicate.

## Audit

| Consumer | Final resolution | Result |
| --- | --- | --- |
| `backend/app/commerce/service_impl.py::load_catalog` | `Path(__file__).resolve().parents[3] / data / mock / wp04_commerce_catalog.json` | **PROVEN** |
| `backend/tests/test_wp04_order_pricing.py` | `Path(__file__).resolve().parents[2] / data / mock / wp04_commerce_catalog.json` | **PROVEN** |
| `backend/app/services.py` | repository-level `PROJECT_ROOT / data/...` | **PROVEN** |
| `backend/app/stay_mobility.py` | repository-level `data/v9/city_operations.json` | **PROVEN** |
| `backend/app/integrations/mock/providers.py` | repository-level `data/mock` | **PROVEN** |
| Final ZIP | includes `data/mock`; excludes `backend/data`, databases and caches | **PROVEN FROM FRESH EXTRACT** |

The existing dirty worktree duplicate was not deleted because unrelated user
changes must be preserved. It is outside the curated release source set and
cannot satisfy any final-extract import.

## Runtime evidence

The old V13 archive reproduced the failure in a clean extraction. After the
path correction, the worktree WP04 pricing and endpoint tests passed. The
final release gate ran those same tests from the V13.1 fresh extraction. The
fresh layout reported `root_catalog=True backend_data_directory=False` and the
WP04 tests passed from that extracted source.
