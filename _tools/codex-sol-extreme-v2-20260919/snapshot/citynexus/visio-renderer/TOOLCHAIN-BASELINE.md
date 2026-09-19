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

Formal CityNexus association routing uses a dual-layer baseline: a genuine native UML Association retains SpecId/source/target semantics and explicit live side-port glue, while deterministic presentation route segments render the approved `phase1-routing.yaml` orthogonal path. Direct mutation of the glued native connector Geometry section is CLOSED for this project. No additional GitHub Visio project research is authorised.

## Historical routing POC qualification

The historical POC measured 5 connectors, `fullyGluedRatio = 1.0`, `orthogonalRouteRatio = 0.4`, and `connectorConnectorCrossingCount = 2`.

It used plain win32com COM and PinX glue. It did not invoke VisioAutomation routing or MSAGL. Automatic routing is excluded from the CityNexus baseline because the required quality was not demonstrated within the project evaluation budget.

## Current milestone

Renderer version: v0.3.2 mainline. C1 is FROZEN_PASS; C2.2 (C2_Anchored_Class_v3) is FROZEN_PASS using native UML Class plus formula-linked presentation field overlays; C3 Presentation is FROZEN_PASS. Full C4 routing mechanics are externally FROZEN_PASS. Association relations retain genuine native Microsoft UML Association semantics and explicit live side-port glue while deterministic presentation segments own the approved visible orthogonal route. Extend relations use the same dual-layer architecture with genuine native Microsoft UML Extend semantics, explicit directional glue, dashed presentation routing, terminal open target arrows, and explicit <<extend>> / condition text. Direct native connector Geometry mutation is permanently closed. The next milestone is pure-geometry planning and external review of all 21 formal P1_UC_Overview routes before any RC6 Visio render.
