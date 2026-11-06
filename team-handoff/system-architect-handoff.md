# System Architect — v2 Handoff

## v1 Architecture (frozen, for GitHub push)

- **Stack:** stdlib-only Python (`src/` has zero third-party imports)
- **Storage:** single JSON file `data/notes.json`, atomic tmp+replace writes, UUID4 IDs
- **Model:** `Note` dataclass with `id`, `title`, `body`, `tags` (dedicated field, not embedded `#tags`), `created_at`, `updated_at`
- **CLI:** `add`, `list`, `search`, `search --tag`, `tags`
- **Tests:** 35/35 pass, 82% aggregate branch coverage; `models.py` 75% and `storage.py` 77% (below 80% gate, task-05/06 pending)
- **CI gate order:** scope-check → stdlib-only import on `src/` → `pytest --cov-branch --cov=src` → staging deploy
- **Concurrency:** last-write-wins, valid JSON guaranteed; TOCTOU in `add_note` explicitly permitted by AC7

## v2 Pivot: CLI → Simple Web App

### Recommended Stack (stdlib-only, no new deps)

| Layer | Choice | Rationale |
|-------|--------|-----------|
| HTTP server | `http.server.ThreadingHTTPServer` | stdlib, threaded (handles concurrent requests), no framework |
| API format | JSON REST | Reuses existing `Note.to_dict()` / `Note.from_dict()` |
| Frontend | Server-rendered HTML + vanilla JS (fetch API) | No build step, no bundler, no npm — keeps stdlib-only invariant |
| Storage | Same `data/notes.json` | No schema migration needed for v2 web; one-note-per-file is a v3 concern |
| Port | 8000 (configurable via env `NOTES_PORT`) | Avoids common conflicts; documented in README |

### Proposed REST API

| Method | Path | Action |
|--------|------|--------|
| GET | `/api/notes` | List all notes (optional `?tag=` filter, `?q=` search) |
| GET | `/api/notes/<id>` | Get single note |
| POST | `/api/notes` | Create note `{title, body, tags}` |
| PUT | `/api/notes/<id>` | Update note `{title?, body?, tags?}` |
| DELETE | `/api/notes/<id>` | Delete note |
| GET | `/` | Serve `index.html` (static) |

### Key Architectural Decisions for v2

1. **ThreadingHTTPServer over HTTPServer** — web app means concurrent browser tabs. `ThreadingHTTPServer` is stdlib and handles this. The concurrency model stays last-write-wins (AC7), but the web layer must not introduce new race surfaces beyond what the storage layer already has.

2. **Storage layer is unchanged** — `load_notes` / `save_notes` / `add_note` / `edit_note` / `delete_note` all carry over. The web handlers are thin HTTP wrappers. No refactoring of storage internals for v2.

3. **Tag hygiene on read** — normalize in `load_notes` (single enforcement point), not scattered across CLI/web handlers. This fixes legacy data and ensures web API returns clean tags.

4. **No session/auth in v2** — single-user local tool. Auth is a v3 concern. The web server binds to `127.0.0.1` only (not `0.0.0.0`) to prevent accidental network exposure.

5. **Static files** — serve `static/` (HTML, CSS, JS) from a dedicated directory. No template engine; vanilla JS calls the REST API.

### Constraints (carry forward)

- stdlib-only in `src/` — no Flask, no FastAPI, no Django
- No new third-party deps without license review (AGPL flag before dev starts)
- CI gate order unchanged: scope-check → stdlib-only import → pytest --cov-branch → staging deploy
- Coverage floor ≥80% branch on `src/` (web handlers must be tested too)

### What I Need From Others

- **@devops-bot:** Confirm port 8000 + run command (`python -m src.server` or `python src/server.py`). I'll provide the exact entrypoint once the module structure is settled. Need `deploy-staging` to serve a live preview URL, not just run tests.
- **@qa-safety:** Web-layer test plan — at minimum: GET /api/notes (empty + populated), POST create, PUT update, DELETE, 404 handling, malformed JSON body → 400. Coverage must include the new `server.py` module.
- **@code-runner:** Walkthrough of the web UI once it's live — same as v1 but via browser. Need a `UX_EXPERIENCE.md` update reflecting the web pivot.
- **@project-manager:** v2 task cards should be: (1) storage read-normalization, (2) HTTP server + REST handlers, (3) static frontend, (4) web tests. Keep each card narrow — no mixing storage fixes with web handlers.

### Risks

- **Threading + file I/O:** `ThreadingHTTPServer` means concurrent `load→save` cycles. This is the same TOCTOU as v1 CLI, but web makes it more likely to trigger. File locking (fcntl/msvcrt) should be evaluated in the v2 concurrency spike, not bolted on ad hoc.
- **No CORS needed** (same-origin, single-user). If we add CORS later, it's a security surface — flag it.
- **Port conflicts:** Default to 8000, allow override via env. Document in README.

### Open Questions for v2 Scoping

1. Should the CLI be retained alongside the web app, or replaced? (Recommendation: keep CLI as a thin wrapper over the same storage layer — zero cost, high value for scripting.)
2. Should `search` be server-side (query param) or client-side (filter in JS)? (Recommendation: server-side for large stores, but v2 stores are small — client-side is simpler and avoids API complexity. Defer server-side to v3.)
3. One-note-per-file storage (from product-discovery's direction C) — defer to v3. v2 keeps single JSON file to avoid schema migration risk alongside the web pivot. Two big changes at once = debugging hell.