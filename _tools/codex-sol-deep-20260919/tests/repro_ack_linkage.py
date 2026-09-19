#!/usr/bin/env python3
"""Minimal executable proof that ACK alone is not resolution."""
events = {"e1": "ACKNOWLEDGED", "e2": "DETECTED"}
accepted = {"e2"}

def open_event(event_id: str) -> bool:
    return events[event_id] not in {"RESOLVED", "IGNORED"} and event_id not in accepted

assert open_event("e1") is True
assert open_event("e2") is False
print("PASS: ACKNOWLEDGED remains open; only the linked accepted trigger closes.")
