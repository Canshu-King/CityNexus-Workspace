# CityNexus Visio Toolchain Baseline

## Tool ownership

- Native UML rendering: current Visio MCP and Microsoft Visio COM.
- Typed ShapeData / User Cell strings: Visio PowerShell 4.7.2 / VisioAutomation.
- VSDX page / shape / child-shape traversal: vsdx 0.6.1.
- Authoritative low-level structural validation: raw Open XML.
- Raw Open XML owns: `Prop.SpecId`, Master references, `Connects`, and ShapeSheet cells/formulas.
- Live validation: Visio MCP / COM.
- JiaxI2 `visio-diagram`: GUIDELINES ONLY; do not globally install or invoke its `diagram_*` tools.

Reusable JiaxI2 concepts are glue quality, connector crossing, connector-through-node, endpoint intrusion, page bounds, text collision, font/style mismatch, and geometry tolerances.

VisioAutomation routing is NOT ADOPTED FOR BASELINE. It is not stated to have failed and is not required. MSAGL is NOT IN BASELINE and was not executed during the final gate; no further evaluation is planned.

Formal CityNexus routing uses native UML Association, explicit connection ports, explicit `phase1-routing.yaml`, and explicit waypoints. No additional GitHub Visio project research is authorised.

## Historical routing POC qualification

The historical POC measured 5 connectors, `fullyGluedRatio = 1.0`, `orthogonalRouteRatio = 0.4`, and `connectorConnectorCrossingCount = 2`.

It used plain win32com COM and PinX glue. It did not invoke VisioAutomation routing or MSAGL. Automatic routing is excluded from the CityNexus baseline because the required quality was not demonstrated within the project evaluation budget.

## Current milestone

Renderer version: v0.3.2 mainline. C1 is frozen PASS; C2 is PASS using native UML Class plus presentation overlays; C3 and C4 remain blocked. RC6, formal Phase 1, and Part 2 are not generated in this milestone.
