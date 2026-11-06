# Code Runner — v2 Handoff Notes

**Role:** UX Evaluator & Runtime Tester
**Project:** notes-app-tasks (v1 CLI → v2 web pivot)
**Date:** 2026-11-06

## v1 Walkthrough Summary

- All 35 tests passed (0.38s).
- CLI journeys verified: add (3 notes), list, search "milk", search --tag work, tags.
- Output format: compact single-line records (`<uuid> | <title> | <tags>`).
- Empty store prints `No notes found`; malformed store exits with code 1.
- No web preview possible (stdlib-only CLI, no HTTP server) — expected for v1.

## v2 Web Pivot — UX Considerations

1. **Keep it simple.** v2 should be a minimal web app (single page, no build toolchain). Avoid over-engineering; mirror the CLI's compact data model (notes with title, tags, uuid).
2. **Preview workflow.** v2 must expose an HTTP server on localhost so Hermes Preview can mount it. Pick a fixed, documented port (e.g., 8000 or 5000) and a `run` command.
3. **Core journeys to preserve:** add note, list notes, search by title/text, filter by tag, list all tags.
4. **UX friction to watch:** form validation (empty title), loading indicators on submit, empty-state messaging ("No notes found"), error handling for malformed store.
5. **Responsiveness:** basic mobile-friendly layout; no heavy CSS framework needed.

## What I Need from the Team

- @system-architect: confirm chosen web stack (stdlib http.server vs Flask/FastAPI) and port.
- @devops-bot: ensure run command and any env vars are documented.
- @qa-safety: define web-layer test plan (route smoke tests, form validation).

## Handoff Status

Ready for v1 GitHub push. v2 UX walkthrough will re-run once the web server is live.
