# Trial Readiness

Completed: focused capability/evidence/API tests, C4-related planning compatibility tests, frontend build, and phone runbook. Required manual/real-device gates remain geolocation permission, HTTPS PWA standalone launch, SSE reconnect, and real-phone comparison in SHADOW mode.

The backend exposes explicit degraded state when an ARRIVAL commitment lacks routable evidence; it does not return a generic 500 from Twin/start for that condition.
