# Task Card 07 — Web Server (src/server.py)

## Goal
Implement the stdlib-only HTTP server and REST API per TRD-v2-web §4–§5. Single file `src/server.py`. No new dependencies.

## Allowed Paths
- `src/server.py`
- `src/__init__.py` (verify exists; create empty if missing so `python -m src.server` works)

## DO NOT Touch
- `src/models.py`, `src/storage.py`, `src/search.py`, `src/cli.py`
- `static/*`, `tests/*`
- Any network/auth/DB/config beyond `notes.json` and env `NOTES_PORT`

## Dependencies
- v1 push complete. TRD-v2-web.md §4–§5 is the spec source.

## Spec
- Module: `http.server.ThreadingHTTPServer`, bind `127.0.0.1`, default port `8000`, overridable via env `NOTES_PORT`.
- Entry point: `python -m src.server` (and `python src/server.py` fallback).
- Custom `BaseHTTPRequestHandler` subclass with JSON body parsing.
- Endpoints per TRD §5.1 (GET /, GET /static/<file>, GET /api/notes, GET /api/notes/<id>, POST /api/notes, PUT /api/notes/<id>, DELETE /api/notes/<id>).
- Query params: `?tag=` (case-insensitive, normalized) and `?q=` (case-insensitive substring); combinable.
- Validation per §5.3 (title required non-empty ≤200, body required string ≤10000, tags optional str/array normalized, unknown fields ignored, missing required → 400).
- Error responses `{\"error\": \"...\"}` never include tracebacks. Status codes per §4.1.
- Static serving: whitelist `.html/.css/.js`, reject path traversal and disallowed extensions.
- JSON body size limit 1MB → 413.
- Missing `notes.json` → `[]` (200); corrupt file → 500 with clean error.
- Storage/search/model layers called directly; no new abstraction.

## Clarifications (from @qa-safety)
- Web `?tag=` filter is **case-insensitive** (TRD §5.2) — deliberately divergent from CLI `search --tag` which stays case-sensitive. Do not unify.
- Handler must distinguish missing store (200 `[]`) from malformed store (500 clean error).

## Acceptance Criteria
- `src/server.py` runs via `python -m src.server` and binds `127.0.0.1:8000` (or `NOTES_PORT`).
- All endpoints return correct status codes and JSON; no tracebacks in error bodies.
- Static whitelist + path-traversal protection.
- ≥80% branch coverage on `src/server.py` (tests in task-10).

## Verification
- `python -m src.server` starts and serves; `curl`/fetch round-trip.
- Imports only stdlib. No changes to existing src modules.