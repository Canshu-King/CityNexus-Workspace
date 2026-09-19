# CityNexus P1 Route Topology Assist

This package is **not** a replacement candidate and does not freeze any route.
It adds a missing precondition to the existing V2/V3 workflow: connector port
order must first define a planar rotation system.

## Independent finding

On the uploaded `phase1-routing-rc6-candidate.yaml`, the current connector port
rotation has **orientable genus 2**. Therefore, with the current side/fraction
ordering, no waypoint-only reroute can produce a zero-contact planar drawing.
This explains why increasingly elaborate A*/dogleg repairs can stall even when
individual routes are reachable.

Both provided seed plans produce **genus 0** without changing connector identity
or any frozen C4E1 Extend geometry.

## Usage

From `D:\moodle\CityNexus` (adjust paths if needed):

```powershell
python visio-renderer\calibration\audit_p1_route_topology.py `
  --semantic visio-spec\pages\p1_uc_overview.yaml `
  --candidate visio-renderer\phase1-routing-rc6-candidate.yaml
```

The current candidate should fail the topology pre-gate.

Then test a seed plan:

```powershell
python visio-renderer\calibration\audit_p1_route_topology.py `
  --semantic visio-spec\pages\p1_uc_overview.yaml `
  --candidate visio-renderer\phase1-routing-rc6-candidate.yaml `
  --plans visio-renderer\calibration\P1_ROUTE_PORT_PLANS.yaml `
  --plan PLAN_O_PRESERVE_LOCAL_GEOMETRY
```

or `PLAN_R_REVERSE_EMBEDDING`.

A topology PASS is **necessary but not sufficient**. After it passes, the
existing V2/V3 route validators remain the actual geometry/freeze gate.
