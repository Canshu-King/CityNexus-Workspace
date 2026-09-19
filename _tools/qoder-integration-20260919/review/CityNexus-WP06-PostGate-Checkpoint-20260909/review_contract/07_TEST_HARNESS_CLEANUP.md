# Test Harness Cleanup

## Observation

Independent split runs reproduce all checkpoint tests as green, but one large Linux pytest process can reach the full test-dot output and then fail to return before the review harness timeout.

This is not currently proven to be a product defect.

## Likely contributor

Several modules create module-global:

```python
client = TestClient(app)
```

These clients are not explicitly closed. The current test design also resets shared application state repeatedly.

## Recommended cleanup before CI/frontend E2E growth

Use a central fixture, preferably:

```python
@pytest.fixture
def client():
    with TestClient(app) as client:
        yield client
```

or a session/module-scoped fixture with explicit teardown if isolation remains correct.

Keep demo/reset behavior deterministic and avoid parallelizing tests until DB/test state isolation is explicit.

Do not block WP06/live-provider work solely on this cleanup, but solve it before the suite becomes hundreds of integration/E2E tests.
