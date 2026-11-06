# Devops Bot — v2 Handoff Notes

**Role:** DevOps & Deployment (CI/CD, build failure analysis, preview deployments)
**Project:** notes-app-tasks (v1 CLI → v2 web pivot)
**Date:** 2026-11-06

## v1 Walkthrough Summary

- Verdict: PASS — all 35 tests green (0.38s).
- CLI journeys exercised: add (3 notes), list, search "milk", search --tag work, tags.
- Output: compact single-line records (`<uuid> | <title> | <tags>`).
- Empty store prints `No notes found`; malformed store exits 1 (no traceback).
- No web preview possible (stdlib-only CLI, no HTTP server) — expected for v1.

## Deployment & CI Status (as of today)

- CI gate order: `scope-check` → `import-gate` (stdlib-only in src/) → `pytest --cov-branch --cov-report=term-missing` (branch coverage, enforced) → `deploy-staging` (main push only).
- `deploy-staging` currently only echoes the preview URL (`https://staging-pr14.dev`) — it is a placeholder until v2 has a real web build to deploy.
- Staging deploy is gated behind task-05/06 (branch coverage ≥80% on src/models.py and src/storage.py). Not yet green.
- `src/models.py` at 75% branch and `src/storage.py` at 77% branch (below the 80% gate) — awaiting task-05/06 tests.

## Web Pivot — DevOps Notes

- v2 needs an HTTP server; I will need a documented run command + fixed port (e.g., 8000/5000) so Hermes Preview can mount it.
- The v1 `deploy-staging` step must become a real preview build: build the web app, then mirror to the staging target at `https://staging-pr14.dev` (or the agreed v2 staging host).
- Keep the store as the single source of truth; decide whether the web server reads/writes `data/notes.json` directly or via the existing storage API (stdlib `http.server` preferred to avoid a new dependency).
- Env vars to document: store path (if overridable) and any bind/port setting. No secrets required for v1→v2 staging.

## What I Need from the Team

- @system-architect: chosen web stack (stdlib `http.server` vs Flask/FastAPI) and fixed port.
- @project-manager: v2 staging deploy target / host for `deploy-staging`.
- @qa-safety: web-layer test plan (route smoke tests, form validation) — I'll wire it into CI and run the deploy smoke.

## Handoff Status

Ready for the v1 GitHub push. v2 handoff notes land here; once task-05/06 green and a web run command + port are agreed, I can flip the staging deploy + post the preview URL.
