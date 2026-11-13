# Changelog

## v3.0.1 / v3.1 debt

- v3.0.1 removed the phantom migration-safety and reduced-motion CI jobs (each called a nonexistent test file); the suggest-contract test is folded into regression-guard as a named step, not a parallel job; the deploy-staging step is deleted (no URL echoed) and remains unverified until a real deploy lands.
- v3.0.1 fixed the committed `/api/notes/suggest` route, which previously pointed at a nonexistent `_handle_suggest`; `_handle_suggest` now serves the frozen contract (combined tag names + note titles, case-insensitive dedup and prefix match, sorted, capped at 10, `<mark>` highlight with user-controlled content escaped, 400 JSON on missing/empty `q`). The dropdown UI lands in v3.0.2.
- v3.1 debt: migration fixtures for task-15 (RELEASE-BLOCKING), due dates for task-16, reduced-motion 0ms collapse plus contrast-audit tests (unwritten and untested as of v3.0.1), B5–B9 deferred to v3.1 with a named owner and target to be assigned at v3.1 planning, and nearest-guess parked as a telemetry-gated open question (requires a no-result rate measurement).
