# C4 execution contract for Codex

C4 is a calibration of **mechanics**, not the formal P1 page.

Do not render RC6 or Part 2 during this task.

1. Apply this patch and run the pure-Python C4 plan validator first.
2. Only if the static plan passes, create a fresh Visio document containing the five C4 nodes.
3. Use native UML Actor / Use Case masters and native UML Association connectors.
4. Create explicit side connection points on node instances when the native master does not expose stable side ports.
5. Glue each connector to the specified source/target side port. `PinX` centre glue is not an acceptable C4 result.
6. Realize the listed waypoints as one native connector path. Do not substitute five separate line shapes.
7. If the current MCP/COM API cannot deterministically realize explicit waypoints on one native Association connector, report `WAYPOINT_REALIZATION_UNSUPPORTED` and stop. Do not fake PASS.
8. Export raw SVG and measure the actual path geometry independently.

Required measured release gate:

- connectorCount = 5
- fullyGluedRatio = 1.0
- explicitSidePortRatio = 1.0
- orthogonalRouteRatio = 1.0
- connectorConnectorCrossingCount = 0
- connectorThroughUnrelatedNodeCount = 0
- endpointIntrusionCount = 0
- outOfPageCount = 0
- nativeAssociationConnectorRatio = 1.0

Only after this C4 calibration passes should the full 21-connector P1 routing be implemented.
