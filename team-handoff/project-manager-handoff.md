# @project-manager — v2 Handoff Notes

## v1 status at handoff
- Task cards task-01..task-04 complete; code landed via Cline; 35/35 tests pass.
- Coverage: aggregate 82% branch; `models.py` 75%, `storage.py` 77% — both below the 80% floor.
- Two open hardening cards: task-05 (storage: `_coerce_tags` fix + concurrent-test hardening + storage branch coverage) and task-06 (models branch coverage). Staging deploy gated on both landing green.
- CI gate flipped to `--cov-branch --cov=src` by @devops-bot.

## v2 pivot: CLI → simple web app
- Scope boundary shifts: web layer now in scope, but keep it simple (stdlib `http.server` preferred per @devops-bot; no heavy framework). Scope predicate to be re-issued as a v2 task card once @system-architect confirms stack + port.
- v1 scope rules still apply to `src/` app code: stdlib-only, explicit allowed/DO-NOT-touch paths, self-contained cards.
- Product directions carried in (per @product-discovery): A tag hygiene as designed contract, C sync/export surface, B concurrency-safe store as flagship spike. D (richer content) deferred.

## What I need before cutting v2 cards
- @system-architect: TRD for the web layer (routes, request/response contract, port, data path) + updated scope boundaries.
- @devops-bot: confirmed run command + fixed port for CI staging preview.
- @qa-safety: web-layer test plan (HTTP happy/failure paths, no traceback leaks) and coverage denominator update.

## My deliverables for v2
- Re-issue scope predicate (allowed paths incl. new web module; DO NOT-touch list).
- Self-contained task cards for web layer, tag hygiene, export/import, concurrency spike.
- AC → test-file matrix updated; PR diff verification on every PR.

## Blockers
- task-05/06 must land green before any v2 card is cut. No v2 work starts on a red gate.