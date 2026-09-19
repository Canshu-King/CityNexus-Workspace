# Frontend foundation

## MapLibre + Turf

MapLibre renders:
- Place markers;
- Activity sequence;
- current activity;
- protected Commitment marker;
- Event marker;
- old route and proposed route.

Turf performs client-side display calculations only:
- bounds for fit-to-route;
- line length display checks;
- buffers/highlight zones;
- nearest-point helpers.

No frontend spatial helper can override backend feasibility.

## XState

Use XState only for UI/workflow orchestration, for example:

```text
idle -> loading -> executing -> disrupted -> comparingReplan
     -> accepting -> executing
```

Backend state remains authoritative. Server responses/events drive transitions.

## shadcn/ui

Use for accessible layout/components only:
- cards;
- dialogs;
- tabs;
- badges;
- timeline panels;
- alert boxes;
- sheet/drawer for Copilot.

Do not import another application's domain components wholesale.
