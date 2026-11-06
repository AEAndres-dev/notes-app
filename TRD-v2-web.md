# Technical Requirement Document — v2 Web Application

**Author:** @system-architect
**Status:** Draft — pending @project-manager card scoping
**Date:** 2026-11-06

## 1. Overview

Transition the notes-app from a CLI-only tool to a **simple, stdlib-only web application** while preserving all v1 functionality. The web layer is a thin HTTP wrapper over the existing storage/search/model layers. No new dependencies, no build step, no framework.

## 2. Constraints (carried from v1)

| Constraint | Source |
|---|---|
| stdlib-only in `src/` | v1 architecture decision |
| No third-party deps without license review (AGPL flag before dev starts) | System Architect policy |
| Coverage floor ≥80% branch on `src/` | QA gate |
| CI gate order: scope-check → stdlib-only import → pytest --cov-branch → staging deploy | v1 pipeline |
| Bind to `127.0.0.1` only (no external exposure) | Security assumption |
| Single-user, no auth in v2 | Product scope |

## 3. Module Breakdown

| File | Responsibility | Depends On | New? |
|---|---|---|---|
| `src/models.py` | `Note` dataclass — unchanged from v1 | (none) | No |
| `src/storage.py` | Read/write `notes.json` — unchanged + read-time tag normalization | `models.py` | Patched |
| `src/search.py` | Text search, tag filter — unchanged | `models.py` | No |
| `src/cli.py` | CLI entry point — retained as thin wrapper | `storage.py`, `search.py` | No |
| `src/server.py` | **NEW** — HTTP server, REST handlers, static file serving | `storage.py`, `search.py`, `models.py` | **Yes** |
| `static/index.html` | **NEW** — single-page frontend (vanilla JS) | — | **Yes** |
| `static/style.css` | **NEW** — minimal styling | — | **Yes** |
| `static/app.js` | **NEW** — frontend logic (fetch API calls to REST) | — | **Yes** |
| `tests/test_server.py` | **NEW** — web-layer tests | — | **Yes** |

**Allowed paths (v2):** `src/server.py`, `static/*`, `tests/test_server.py`, plus existing allowed paths.
**DO NOT touch:** `src/models.py` internals (only add tests), no new deps, no auth, no database drivers, no config files beyond `notes.json`.

## 4. HTTP Server

- **Module:** `http.server.ThreadingHTTPServer`
- **Bind address:** `127.0.0.1`
- **Default port:** `8000` (overridable via env `NOTES_PORT`)
- **Entry point:** `python -m src.server` (requires `src/__init__.py` — verify exists or create)
- **Request handler:** Custom `BaseHTTPRequestHandler` subclass with JSON body parsing
- **Threading:** `ThreadingHTTPServer` handles concurrent browser tabs; last-write-wins semantics (AC7) carried over
- **No CORS:** same-origin only

### 4.1 Request/Response Format

All API responses are JSON with `Content-Type: application/json; charset=utf-8`.

| Status | Meaning |
|---|---|
| 200 | Success (GET, PUT) |
| 201 | Created (POST) |
| 204 | No Content (DELETE) |
| 400 | Bad Request (validation failure, malformed JSON) |
| 404 | Not Found |
| 500 | Internal Server Error (malformed store, unexpected) |

Error responses: `{"error": "<user-facing message>"}` — never include tracebacks.

## 5. REST API Specification

### 5.1 Endpoints

| Method | Path | Request Body | Response | Notes |
|---|---|---|---|---|
| GET | `/` | — | `index.html` (text/html) | Serves static frontend |
| GET | `/static/<file>` | — | Static file (CSS/JS) | Whitelist: `.css`, `.js`, `.html` only |
| GET | `/api/notes` | — | `[{Note}]` | Optional query params: `?tag=<tag>`, `?q=<query>` |
| GET | `/api/notes/<id>` | — | `{Note}` or 404 | UUID validation on `<id>` |
| POST | `/api/notes` | `{"title", "body", "tags"?}` | `{Note}` (201) | `tags` optional, defaults to `[]` |
| PUT | `/api/notes/<id>` | `{"title"?, "body"?, "tags"?}` | `{Note}` or 404 | Partial update |
| DELETE | `/api/notes/<id>` | — | 204 or 404 | |

### 5.2 Query Parameters (GET /api/notes)

- `?tag=<tag>` — filter by tag (case-insensitive, normalized)
- `?q=<query>` — search title + body (case-insensitive substring)
- Both can combine: `?tag=work&q=milk`

### 5.3 Request Body Validation

- `title`: required, non-empty string, max 200 chars
- `body`: required, string (can be empty), max 10000 chars
- `tags`: optional, string (comma-separated) or array of strings; normalized via `_coerce_tags`
- Unknown fields: ignored (not rejected)
- Missing required fields: 400 with `{"error": "title is required"}`

### 5.4 Note JSON Schema (response)

```json
{
  "id": "uuid4-string",
  "title": "string",
  "body": "string",
  "tags": ["string"],
  "created_at": "ISO 8601",
  "updated_at": "ISO 8601"
}
```

## 6. Storage Layer Changes (v2)

### 6.1 Read-time tag normalization

Add normalization in `load_notes`: after `Note.from_dict(item)`, re-normalize tags via `_coerce_tags(note.tags)`. This ensures legacy data with junk tags (empty strings, unstripped) is cleaned on every load. Single enforcement point — no scattering across handlers.

### 6.2 No other storage changes

- Same `data/notes.json` file, same atomic write pattern
- Same `add_note`, `edit_note`, `delete_note` functions
- Web handlers call these directly (no new storage abstraction)

## 7. Frontend (static/)

- **No build step, no bundler, no npm** — vanilla HTML/CSS/JS
- `index.html`: single page with note list, add form, search input, tag filter
- `app.js`: uses `fetch()` to call REST API; renders notes as cards/list
- `style.css`: minimal, responsive, no framework (no Bootstrap/Tailwind)
- Static files served by `server.py` from `static/` directory relative to project root

### 7.1 Frontend Behavior

- On load: `GET /api/notes` → render list
- Add note: form submit → `POST /api/notes` → prepend to list → clear form
- Edit: inline edit → `PUT /api/notes/<id>` → update card
- Delete: button → `DELETE /api/notes/<id>` → remove card
- Search: input → debounce 300ms → `GET /api/notes?q=<query>` → re-render
- Tag filter: click tag → `GET /api/notes?tag=<tag>` → re-render
- Empty state: "No notes found" message

## 8. CLI Retention

The CLI (`src/cli.py`) is retained as a thin wrapper over the same storage/search layers. Both CLI and web server share `data/notes.json`. No code duplication — CLI calls the same functions as the web handlers.

## 9. Security Considerations

- Bind `127.0.0.1` only — no `0.0.0.0`, no network exposure
- No auth in v2 (single-user local tool)
- Static file serving: whitelist extensions (`.html`, `.css`, `.js`), reject path traversal (`..`, absolute paths)
- JSON body size limit: 1MB (reject oversized with 413)
- No CORS headers (same-origin)
- Error responses never include stack traces or file paths

## 10. Concurrency Model (v2)

- `ThreadingHTTPServer` handles concurrent requests
- Storage layer uses last-write-wins (AC7 carried over)
- No file locking in v2 (deferred to v3 concurrency spike — see product-discovery direction B)
- Risk: concurrent `load→save` can lose writes, but store stays valid JSON (atomic tmp+replace)

## 11. Test Plan (for @qa-safety)

### 11.1 Unit Tests (tests/test_server.py)

| Test | Description |
|---|---|
| `test_get_index` | GET / returns 200 with HTML content-type |
| `test_get_notes_empty` | GET /api/notes on empty store → `[]` |
| `test_get_notes_populated` | GET /api/notes with notes → list |
| `test_get_notes_filter_tag` | GET /api/notes?tag=work → filtered list |
| `test_get_notes_search` | GET /api/notes?q=milk → filtered list |
| `test_get_note_by_id` | GET /api/notes/<id> → single note (200) |
| `test_get_note_not_found` | GET /api/notes/<bad-id> → 404 |
| `test_create_note` | POST /api/notes → 201 + note with UUID |
| `test_create_note_missing_title` | POST with no title → 400 |
| `test_create_note_tags_normalized` | POST with tags " a , , b " → `["a", "b"]` |
| `test_update_note` | PUT /api/notes/<id> → 200 + updated |
| `test_update_note_not_found` | PUT /api/notes/<bad-id> → 404 |
| `test_delete_note` | DELETE /api/notes/<id> → 204 |
| `test_delete_note_not_found` | DELETE /api/notes/<bad-id> → 404 |
| `test_malformed_store` | Corrupt notes.json → 500 with clean error (no traceback) |
| `test_static_file_serving` | GET /static/style.css → 200 with CSS content-type |
| `test_path_traversal_blocked` | GET /static/../src/models.py → 403 or 404 |
| `test_bind_localhost_only` | Server binds to 127.0.0.1 (verify via socket) |

### 11.2 Coverage Target

- `src/server.py` must reach ≥80% branch coverage
- Existing modules must not drop below 80% (regression guard)

## 12. CI Changes (for @devops-bot)

- Add `src/server.py` to stdlib-only import gate (no new imports)
- Add `tests/test_server.py` to pytest run
- Coverage gate: `--cov-branch --cov=src` (unchanged, now includes server.py)
- Staging deploy: serve `python -m src.server` on port 8000, post URL to Discord
- Run command: `python -m src.server` (or `python src/server.py` as fallback)

## 13. v2 Scope Boundaries

### In Scope (v2)
- Web server + REST API (this TRD)
- Static frontend (HTML/CSS/JS)
- Tag hygiene on read (storage normalization)
- CLI retention
- Web-layer tests

### Out of Scope (v2) — deferred to v3
- One-note-per-file storage (product-discovery direction C)
- Concurrency-safe store with file locking (direction B — spike first)
- Markdown body, attachments, reminders (direction D)
- Authentication / multi-user
- Cloud sync / export-import
- CORS / external network access

## 14. Open Questions (resolved)

| Question | Decision |
|---|---|
| Keep CLI alongside web? | Yes — zero cost, high value for scripting |
| Client-side vs server-side search? | Client-side for v2 (filter in JS); server-side deferred to v3 |
| One-note-per-file? | Deferred to v3 — don't mix storage migration with web pivot |
| Auth in v2? | No — single-user local tool |
| Framework? | No — stdlib `http.server` only |

## 15. Task Card Mapping (for @project-manager)

| Card | Scope | Allowed Paths | Depends On |
|---|---|---|---|
| `task-07-web-server.md` | `src/server.py` — HTTP server + REST handlers + static serving | `src/server.py`, `src/__init__.py` | This TRD |
| `task-08-static-frontend.md` | `static/index.html`, `static/style.css`, `static/app.js` | `static/*` | task-07 |
| `task-09-storage-normalization.md` | Read-time tag normalization in `load_notes` | `src/storage.py` | None (can parallel with 07) |
| `task-10-web-tests.md` | `tests/test_server.py` — all 18 test cases from §11.1 | `tests/test_server.py` | task-07, task-09 |
| `task-11-concurrency-spike.md` | Spike: lockfile vs per-note files vs merge-on-conflict | `docs/spike-concurrency.md` | None (can parallel) |

**DO NOT start v2 cards until v1 push is complete.**

---

*This TRD is the single source of truth for v2 web application scope. @project-manager should cut cards from §15. @devops-bot should wire port 8000 + `python -m src.server` into CI per §12. @qa-safety should execute the test plan in §11. @code-runner should walkthrough the web UI once live.*