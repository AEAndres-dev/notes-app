# QA Safety — v2 Handoff Notes

**Role:** QA & Code Safety Engineer (coverage gate owner)
**Project:** notes-app-tasks (v1 CLI → v2 web pivot)
**Date:** 2026-11-06

## v1 Walkthrough Summary

- Verdict: **PASS** — all 35 tests passed (0.30s / 0.44s with coverage).
- Coverage at handoff:
  - `src/models.py`: 75% branch (10 missing) → below the 80% floor.
  - `src/storage.py`: 77% branch (17 missing) → below the 80% floor.
  - Total `src/`: 82% branch (aggregate passes, but two files are under).
- Defects flagged (for @code-runner / @system-architect):
  1. `_coerce_tags` (src/storage.py) retains empty / unstripped tags — data-quality bug.
  2. `test_concurrent_writes_no_corruption` uses a tautology (`assert not errors or True`); worker exceptions are never gated.
  3. Remaining branches under 80% (models `_validate` raises, `__eq__`, `__repr__`; storage path fallbacks, retry-failure cleanup).

## v2 Web Pivot — My QA Notes (test plan primer)

1. **Re-run the coverage floor on web code.** The ≥80% branch gate must apply to the new web
   layer, not just `src/`. No unhandled exceptions anywhere in request handling.
2. **Route smoke tests + form validation.** Add note, list notes, search by text/tag, tags summary.
3. **Empty-state and error states** must be visible (no notes found, malformed store, invalid input).
4. **Input sanitisation / output encoding** — the old `tags` data-quality flaw is now a web
   surface (persisted tags render in HTML). Tags must be escaped on output.
5. **Atomic writes carry over.** The web layer should keep the tmp+replace store (or move to a
   per-note layout for v2 B). Data-loss semantics are unchanged: last-write-wins, no corruption.

## What I Need from the Team

- **@code-runner** — land task-05/06 (storage hardening + models coverage) and verify both files
  reach ≥80% branch coverage.
- **@system-architect** — confirm the v2 web stack and fixed port.
- **@devops-bot** — wire the documented `run` command into CI and make `deploy-staging` a real
  preview build.
- **@product-discovery** — cut v2 discovery cards (A/C first, B as flagship).

## Handoff Status

Ready for v1 GitHub push. My v2 web-layer test plan re-arms once the web server is live.
