# Notes App

A lightweight, dependency-free notes application. **v1** is a stdlib-only CLI over a local
JSON store. A **v2** web pivot (stdlib `http.server.ThreadingHTTPServer` + JSON REST API +
vanilla-JS frontend) is planned per `TRD-v2-web.md`; see the "v2 Web App (planned)" section
below. No third-party dependencies anywhere in `src/`.

## Status

- **v1 (shipped):** `add` / `list` / `search` (text + tag) / `tags`. 50 tests pass.
  Branch coverage: `src/` aggregate 89%; every module ≥ 80% (`models` 95%, `storage` 83%,
  `search` 100%, `cli` 94%).
- **v2 (planned, not yet implemented):** thin HTTP wrapper over the same storage/search/model
  layers. Task cards `task-07` … `task-11` track delivery (web server, static frontend,
  storage read-time tag normalization, web tests, concurrency spike).

## Project Layout

```
notes-app-tasks/
├── notes-app-proposal.md       # Locked source of truth (brief + acceptance criteria)
├── TRD-v2-web.md               # v2 web application technical requirements
├── UX_EXPERIENCE.md            # UX walkthrough notes
├── task-01-models.md … task-11-concurrency-spike.md   # Task cards
├── team-handoff/               # Per-role v2 handoff notes
├── data/notes.json             # Runtime store (created on first add)
├── src/
│   ├── __init__.py
│   ├── models.py               # Note dataclass + serialization/validation
│   ├── storage.py              # JSON read/save, atomic tmp+replace, UUID4
│   ├── search.py               # Text + tag search
│   ├── cli.py                  # Entry point: add/list/search/tags
│   └── server.py               # (planned, v2) HTTP server + REST handlers
├── static/                     # (planned, v2) index.html, style.css, app.js
└── tests/
    ├── test_models.py
    ├── test_storage.py
    ├── test_search.py
    ├── test_cli.py
    └── test_server.py          # (planned, v2)
```

## Run Locally (v1 CLI)

```bash
python -m pytest                                    # full suite (50 tests)
python -m pytest --cov=src --cov-branch             # with branch coverage
python -m src.cli add "Hello" --tags work           # add a note
python -m src.cli list                              # list notes
python -m src.cli search "query"                    # full-text search
python -m src.cli search --tag work                 # tag filter
python -m src.cli tags                              # list tags with counts
```

Empty store prints `No notes found`; a malformed `data/notes.json` exits with code 1 and a
clean error (no traceback). Output format: compact single-line records
`<uuid> | <title> | <tags>`.

## v2 Web App (planned)

Per `TRD-v2-web.md` (stdlib-only, no build step, no framework):

- **HTTP server:** `http.server.ThreadingHTTPServer`, bind `127.0.0.1` only.
- **Default port:** `8000`, overridable via env var `NOTES_PORT`.
- **Entry point (planned):** `python -m src.server` (fallback: `python src/server.py`).
- **Run command for Hermes Preview (planned):** `python -m src.server` on port `8000`.
- **Static files:** served from `static/` (`.html`, `.css`, `.js` only; path traversal blocked).
- **Store:** same `data/notes.json`; last-write-wins semantics (AC7) carried over.

### REST API (planned)

| Method | Path | Notes |
|---|---|---|
| GET | `/` | Serves `index.html` |
| GET | `/static/<file>` | Whitelisted static assets |
| GET | `/api/notes` | List all; optional `?tag=` (case-insensitive) and `?q=` (substring) |
| GET | `/api/notes/<id>` | Single note or 404 |
| POST | `/api/notes` | Create `{title, body, tags?}` → 201 |
| PUT | `/api/notes/<id>` | Partial update → 200 |
| DELETE | `/api/notes/<id>` | → 204 |

Errors return `{"error": "..."}` with no tracebacks. JSON body limit 1 MB (413 when exceeded).

### Environment Variables

| Variable | Default | Description |
|---|---|---|
| `NOTES_PORT` | `8000` | Port for the v2 web server (planned) |
| (store path) | `data/notes.json` | Override only where supported by storage API |

### Security (planned)

- Bind `127.0.0.1` only (no `0.0.0.0`, no network exposure).
- No auth in v2 (single-user local tool).
- Static whitelist + path-traversal protection; no CORS.

## Concurrency

Last-write-wins with atomic tmp+replace writes: the store stays valid JSON even under
concurrent writes; no leftover `.tmp` files. Full file locking is deferred to the v3
concurrency spike (`task-11`).

## CI Gates (in order)

1. Scope-check — PR only touches `src/*.py`, `tests/*`, `data/notes.json` (v2 adds `static/*`).
2. Stdlib-only import gate — no third-party imports in `src/`.
3. Build + tests — `python -m pytest --cov=src --cov-branch`.
4. On pass → build + deploy staging, post URL (e.g. `https://staging-pr14.dev`).

## Source of Truth

- Brief / acceptance criteria: `notes-app-proposal.md`
- v2 technical requirements: `TRD-v2-web.md`
- v2 user stories & ACs: `team-handoff/product-discovery-v2-stories.md`
- Task cards: `task-01-models.md` through `task-11-concurrency-spike.md`
- CI gates read from these, not from intuition.

