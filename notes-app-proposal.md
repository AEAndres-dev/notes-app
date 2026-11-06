# Simple Notes Application — Product Proposal

## Problem Statement
Users need a lightweight, dependency-free way to capture, search, and organize short notes from the command line. Existing note tools are either too heavy (GUI apps, cloud sync) or too unstructured (plain text files with no search or tagging).

## Target User
Developers and power users who live in the terminal and want fast, local, searchable note capture without leaving the shell.

## MVP Scope (v1)

### In-Scope Commands
| Command | Description |
|---|---|
| `add <title> <body> [--tags t1,t2]` | Create a note with title, body, and optional tags; persist to `notes.json`. |
| `list` | Print all notes (id, title, tags) or "No notes found" for empty store. |
| `search <query>` | Return notes whose title or body contains the query (case-insensitive). |
| `search --tag <tag>` | Return notes tagged with the given tag. |
| `tags` | List all unique tags across notes with counts. |

### Data Model
Each note is a JSON object with the following fields:

| Field | Type | Description |
|---|---|---|
| `id` | string (UUID4) | Unique identifier. |
| `title` | string | Note title. |
| `body` | string | Note body text. |
| `tags` | list[str] | Tags as a dedicated field (not embedded `#tags` in body). |
| `created_at` | string (ISO 8601) | Creation timestamp. |
| `updated_at` | string (ISO 8601) | Last update timestamp. |

### Storage
- Single file: `data/notes.json`.
- Atomic writes: write to `data/notes.json.tmp`, then `os.replace()` to `data/notes.json`.
- Load validation: on startup, validate JSON structure. If malformed, print a user-facing error and exit cleanly (no traceback).

### Tag Syntax
- Tags are stored as a dedicated `tags` field (list of strings) in the Note model — **not** embedded `#tags` in the body.
- CLI convenience: `notes add "Buy milk" --tags work,shopping` parses into the tags field.
- `notes search --tag work` filters by tag.
- Tags must round-trip through edit and delete without loss.

## Out of Scope (v1)
- No network code, cloud sync, or API.
- No authentication or user accounts.
- No database drivers (SQLite, etc.).
- No GUI or web layer.
- No config files beyond `notes.json`.
- No additional CLI flags beyond those listed above.

## Module Breakdown (from @system-architect)

| File | Responsibility | Depends On |
|---|---|---|
| `src/models.py` | `Note` dataclass — `id`, `title`, `body`, `tags: list[str]`, `created_at`, `updated_at`. Serialization/deserialization to dict. | (none) |
| `src/storage.py` | Read/write `notes.json`. Atomic writes, JSON validation on load, ID generation (UUID4). | `models.py` |
| `src/search.py` | Text search (title+body substring), tag filter, combined queries. | `models.py` |
| `src/cli.py` | Entry point. Subcommands: `add`, `list`, `search`, `tags`. Argparse. Error handling + clean exit codes. | `storage.py`, `search.py` |
| `tests/` | One test file per module: `test_models.py`, `test_storage.py`, `test_search.py`, `test_cli.py`. | — |

## Scope Boundaries (for task cards & CI gates)

- **Allowed paths**: `src/models.py`, `src/storage.py`, `src/search.py`, `src/cli.py`, `tests/*`, `data/notes.json`
- **DO NOT touch**: No network code, no auth, no database drivers, no config files beyond `notes.json`, no GUI/web layer.

## Seed Acceptance Criteria (confirmed)

1. `add` creates a note with title, body, and optional tags; persists to `notes.json`.
2. `list` prints all notes (id, title, tags) or "No notes found" for empty store.
3. `search <query>` returns notes whose title or body contains the query (case-insensitive).
4. `search --tag <tag>` returns notes tagged with that tag.
5. `tags` lists all unique tags across notes with counts.
6. Malformed `notes.json` on load → user-facing error, clean exit (no traceback).
7. Concurrent writes don't corrupt the store (atomic write via tmp+replace).
8. Tags round-trip through edit and delete without loss.

## QA Coverage Expectations (from @qa-safety)

1. Every in-scope command (`add`/`list`/`search`/`tags`) has a failing test before the fix (RED), then a passing test (GREEN).
2. Edge cases covered at minimum: empty store, note with only tags, search with no match, duplicate-tag handling, malformed JSON on load, interruption mid-write (partial file recovery).
3. No unhandled exceptions in the CLI entry point — every error path prints a user-facing message and exits cleanly.

## Success Metrics
- All 8 acceptance criteria pass automated tests.
- Zero unhandled exceptions in CLI entry point.
- `notes.json` remains valid after interrupted writes.
- Test coverage ≥ 80% on non-trivial paths.
