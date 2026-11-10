# notes-app-proposal-v2.md

**Status:** Draft for scrum north-star — v2 web pivot planning.
**Date:** 2026-11-06
**Scope:** v1 (stdlib CLI) → v2 (simple stdlib web app), gated ON the v1 corrections and coverage floor.

---

## 1. v1 recap (for the record)

- Verdict: **PASS** — all **50 tests green** (0.44s).
- Branch coverage gate met: `src/models.py` **95%**, `src/storage.py` **83%** (≥80%).
- CI gate: `scope-check` → `import-gate` (stdlib-only) → `pytest --cov-branch --cov=src` → `deploy-staging`.
- Corrections landed: `src/storage.py::_coerce_tags` strips + drops empties; `test_concurrent_writes_no_corruption` fails on worker errors; storage/models coverage tests added.
- v1 handoffs in place: `tasks/` (task-01..06 + v2 task-07..11), `team-handoff/`, `team-folder/agent-startup-team-roles.md`.
- The v1 push is complete and green (confirmed by QA independently).

---

## 2. v2 vision

Transition from a single-file CLI notes tool to a **simple, stdlib-only web application**.

Non-goals for v2:
- No Flask/FastAPI, no npm, no build step, no external dependencies.
- No auth in v2.
- No new schema break: the JSON store is unchanged in shape.

Architectural direction (per @system-architect):
- **Entrypoint:** `python -m src.server` (importable `src/__init__.py`).
- **Server:** stdlib `ThreadingHTTPServer` — supports concurrent tabs; binds to `127.0.0.1` only.
- **Protocol:** JSON REST API + server-rendered HTML / vanilla JS frontend.
- **Endpoints (6):** list, get, create, update, delete, + static index.
- **Storage:** JSON store unchanged (single source of truth); tag normalization on read in `load_notes`.
- **Config:** port via `NOTES_PORT` env var, default **8000** (`src/server.py`); bind `127.0.0.1`.
- **Deferred:** concurrency-safe store (B), one-note-per-file storage, auth, CORS.

---

## 3. Product directions for v2 (product-discovery)

| Direction | Description | Status |
|---|---|---|
| **A. Tag hygiene contract** | Normalize tags on input **and** read (strip + drop empties); `tags --prune`/`auto-cleanup` | Recommended for A+C first |
| **B. Concurrency-safe store** | No silent note loss; conflicts surface (lockfile/merge-on-conflict) | Flagship, but hold until A+C land |
| **C. Sync/export surface** | `export --format md|json` + `import` with dedup by id | Low-risk, high-trust — do with A |
| **D. Richer content** | Markdown body, attachments, reminders | Deferred until A–C land |

**Recommendation:** Scope v2 as **A + C** first (low-risk, high-trust), with **B** as the flagship.

---

## 4. v2 task cards (executive)

| Card | Description | Owner lane |
|---|---|---|
| `task-07` | Web server: `src/server.py` + importable `src/__init__.py` | @code-runner |
| `task-08` | Static frontend: server-rendered HTML + vanilla JS | @system-architect |
| `task-09` | Storage normalization (strip + drop empties on input & read) | @code-runner |
| `task-10` | Web tests (TRD §11.1 + 7 extra validation/security cases) | @qa-safety |
| `task-11` | Concurrency spike (B): how to model safe multi-writer merges | @product-discovery |

Pending QA gate: `src/server.py` ≥80% branch coverage **and** v1 modules staying ≥80% branch.

---

## 5. Acceptance criteria (product-facing, W1–W5)

- **W1 — Notes CRUD:** add, list, get, update, delete working through the web UI.
- **W2 — Tag integrity:** tag chips render normalized tags; `?tag=work&q=milk` combined filter returns the correct intersection.
- **W3 — Export/import:** `export --format md|json` + `import` (dedup by id) move notes between machines without loss.
- **W4 — Empty-state UX:** "No notes found" messaging, form validation, and loading states present and correct.
- **W5 — Concurrency:** no silent note loss when the store is edited from two terminals/devices (B, when implemented).

---

## 6. Cross-cutting risks & open items

- **Concurrency TOCTOU** in `add_note` (`load → append → save`) is permitted by AC7 (last-write-wins) but will bite under multi-terminal sync.
- **Threading + file I/O** race surface on the store file.
- **Port conflicts** on `127.0.0.1:8000`; `NOTES_PORT` env var wires the bind.
- **CORS** deferred (local, same-origin v2).
- **v2 store migration** not in scope until B lands (don't mix two big changes).

---

## 7. Handoff status

- `tasks/` — 11 cards (v1: task-01..06; v2: task-07..11). ✅
- `team-handoff/` — 6 agent handoffs. ✅
- `team-folder/agent-startup-team-roles.md` — consolidated roles doc (v2 context). ✅
- `notes-app-proposal-v2.md` — this file. ✅
- Next: `src/server.py` lands → `NOTES_PORT` wired into CI → v2 staging preview → QA web-layer gate.
