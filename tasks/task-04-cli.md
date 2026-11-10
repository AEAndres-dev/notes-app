# Task Card 04 — CLI (src/cli.py)

## Goal
Implement the argparse CLI entry point wiring storage and search into subcommands: `add`, `list`, `search`, `tags`.

## Allowed Paths
- `src/cli.py`
- `tests/test_cli.py`

## DO NOT Touch
- `src/models.py`, `src/storage.py`, `src/search.py` (read-only deps)
- Any network, auth, database, or config code

## Dependencies
- Task 01, 02, 03 must be complete.

## Spec
Subcommands (argparse):
- `add "title" "body" [--tags t1,t2]` — create note, print "Added note <id>".
- `list` — print all notes as `id | title | tags`, or "No notes found" if empty.
- `search "query"` — print matching notes.
- `search --tag <tag>` — print notes with that tag.
- `tags` — print unique tags with counts, one per line: `<tag>: <count>`.

Error handling:
- Malformed store → print user-facing error to stderr, exit code 1.
- Unknown subcommand → argparse handles (exit 2).
- Every error path prints a message; no unhandled exceptions or tracebacks.

Exit codes: 0 success, 1 user-facing error.

## Acceptance Criteria (from TRD)
- AC 1, 2, 3, 4, 5 (full CLI surface).
- AC 6 (malformed store clean exit).
- AC 8 (tags round-trip via CLI).

## Test Requirements (from @qa-safety)
- `test_cli.py`:
  - `test_add_creates_and_persists`
  - `test_list_empty_prints_no_notes`
  - `test_list_populated`
  - `test_search_text`
  - `test_search_tag`
  - `test_tags_output`
  - `test_malformed_store_clean_exit` — assert exit code 1, no traceback in stderr.
  - `test_cli_exit_codes` — 0 on success.

## Verification
- Run `pytest tests/test_cli.py -q` — all pass.
- Run `python -m src.cli --help` — no error.
- Imports only storage, search, models, stdlib.