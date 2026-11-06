# Task Card 11 — Concurrency Spike (docs/spike-concurrency.md)

## Goal
Spike: evaluate lockfile vs per-note files vs merge-on-conflict for v3 concurrency. Produce a recommendation doc only — no code shipped.

## Allowed Paths
- `docs/spike-concurrency.md`

## DO NOT Touch
- `src/*`, `tests/*`, `static/*`

## Dependencies
None — can run in parallel.

## Spec
- Evaluate three models: file lockfile, one-note-per-file, merge-on-conflict.
- Output a recommendation doc with trade-offs and a proposed v3 direction.
- No production code changes.

## Acceptance Criteria
- `docs/spike-concurrency.md` exists with recommendation.

## Verification
- Doc present and readable.