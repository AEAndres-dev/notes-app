# Product Discovery — v2 Handoff

**Role:** Product Discovery (feature generator) — Agent Startup Team
**App:** notes-app-tasks (v1 → v2 web pivot)
**Date:** v2 handoff (pre-GitHub-push)

---

## v1 product read

Shipped v1 is a stdlib-only CLI notes tool: add/list/search (text + tag)/tags over a local JSON store. QA PASS, 35/35 tests, 82% aggregate branch coverage (models 75%, storage 77% — both below the 80% gate, task-05/06 open).

Two product-level signals surfaced from v1 that carry into v2:

1. **Tags are a first-class user-facing concept** (search --tag, tags summary), but tag data quality was never a designed contract — `_coerce_tags` lets empty/whitespace tags persist and print as junk in the `tags` view. This is a UX papercut that must become an explicit AC in v2, not a follow-up fix.
2. **Concurrent-write semantics are "last-write-wins + valid JSON."** Documented v1 limitation, but the single biggest latent user-pain point for anyone syncing the store file across devices or running two terminals. Not a v1 blocker (AC7 permits it), but the natural v2 headline.

## v2 product directions (proposed)

- **A. Tag hygiene as a designed contract** — normalize on input (storage) AND on read (legacy data); `tags --prune` or auto-cleanup. No API/schema change.
- **B. Concurrency-safe store** — atomic append with per-note files or lockfile + merge-on-conflict. Flagship v2 candidate.
- **C. Sync/export surface** — `export --format md|json` + `import` with dedup by id; git-friendly one-note-per-file layout. Strongly enables B.
- **D. Richer note content (deferred)** — markdown body, attachments, reminders. Hold until A–C land; content features on a fragile store is how data loss happens.

Recommendation: scope v2 as **A + C first** (low-risk, high-trust, no schema break), with B as the flagship if the team wants a v2 marketing beat. D stays in backlog.

## Web pivot reaction

User-approved pivot: CLI → simple web app. @system-architect's recommendation (stdlib `ThreadingHTTPServer` + JSON REST API + server-rendered HTML/vanilla JS, no Flask/FastAPI, no npm, no build step) is the right call for this team's constraints — it preserves the stdlib-only import gate, keeps deploy trivial, and avoids a build toolchain we'd have to own.

Product implications of the pivot I want on record:

- **Keep the CLI alongside the web app** (architect confirmed yes). The CLI is the scriptable/automation surface; the web app is the human surface. Don't force a single entrypoint.
- **Client-side search for v2** (architect proposed). Good — keeps the server stateless and the store simple. Revisit if note counts exceed ~1k.
- **Tag hygiene (A) must ship in the web v2**, not be deferred. The web UI will make junk tags more visible (tag chips, filter pills), so the `_coerce_tags` fix is a prerequisite, not a nice-to-have.
- **No auth in v2** (architect). Fine for a local single-user tool, but the product positioning must be explicit: "personal notes, runs locally." Don't imply multi-user or shared.
- **Port 8000 + `python -m src.server`** (architect proposed, devops-bot to confirm). Product ask: a stable, documented URL + a `--port` override so it doesn't collide with other local tools.

## Open questions I'm carrying

- Do we want a "first-run" empty-state UX in the web app (guided "add your first note")? Product leans yes — cheap, high perceived polish.
- Should tags be editable inline in the web UI, or only at create time? Product leans inline-edit (low cost, high value), gated on A landing.
- v2 naming/positioning: is this still "notes-app-tasks" or do we rebrand for the web pivot? Defer to @project-manager.

## What I need from others

- @system-architect: confirm port 8000 + entrypoint; flag any constraint that blocks inline tag editing or empty-state UX.
- @devops-bot: once run command + port are locked, document them in CI so staging deploy can post a real preview URL.
- @qa-safety: web-layer test targets — at minimum: empty store renders "No notes found" equivalent, tag filter round-trips, malformed store → graceful error (no traceback), concurrent-tab smoke.
- @project-manager: cut v2 discovery card for A+C (and a spike card for B's concurrency model) once task-05/06 land green; confirm whether to rebrand.

## Status

- v1 handoff: complete. Ready for GitHub push.
- v2: awaiting task-05/06 green + architect/devops confirmations before I draft full user stories + ACs.

— @product-discovery
