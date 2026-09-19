# Blockers and Non-Blocking Notes

No blocker remains for the Vertical Slice Hardening stop gate.

The opt-in Valhalla smoke test remains skipped because no live URL is
configured. The deterministic Mock and frozen evidence paths remain the
default. The two reported warnings come from upstream FastAPI/Starlette
TestClient and AnyIO deprecations.

Provider-runtime expansion, OR-Tools, LiteLLM/DeepSeek, live payments, and
external Providers remain outside this checkpoint and require independent
review before work resumes.
