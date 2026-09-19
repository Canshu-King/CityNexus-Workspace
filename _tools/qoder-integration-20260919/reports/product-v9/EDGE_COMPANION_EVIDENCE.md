# Edge Companion Evidence

## API contract

The V9 edge surface provides:

- device registration with a device-scoped token;
- compact Journey snapshot containing active PlanVersion, NOW, NEXT, mode and protected C4 state;
- low-risk typed action endpoint (for example `ACKNOWLEDGE`);
- observation endpoint for device signals.

The server rejects booking/payment/admin actions from the device principal. The edge device has no policy, payment or Commitment-management authority.

## Simulator proof

`tools/edge_companion_simulator.py` implements compact UART serialization/parsing and an HTTP round trip. The V9 flagship test verifies that the serialized frame contains `NOW|`, `NEXT|`, `MODE|` and `C4|`, parses `ACK|REPLAN`, posts an acknowledgement/observation, and rejects `CREATE_BOOKING`.

This is a Python protocol simulator, not a claim of completed PIC firmware. The required device boundary is server-enforced and the edge snapshot is derived from the same active PlanVersion/JourneyTwin truth used by web and offline clients.
