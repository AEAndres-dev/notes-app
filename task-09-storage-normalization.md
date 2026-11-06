# Task Card 09 — Storage Read-Time Tag Normalization (src/storage.py)

## Goal
Add read-time tag normalization in `load_notes` per TRD-v2-web §6.1. Single enforcement point. No other storage changes.

## Allowed Paths
- `src/storage.py`

## DO NOT Touch
- `src/models.py`, `src/search.py`, `src/cli.py`, `src/server.py`
- `tests/*` (task-10 owns server tests; existing storage tests must still pass)

## Dependencies
None — can run in parallel with task-07.

## Spec
- In `load_notes`, after `Note.from_dict(item)`, re-normalize tags via `_coerce_tags(note.tags)` before appending. Ensures legacy junk tags (empty strings, unstripped) are cleaned on every load.
- No other changes to storage (same file, same atomic write, same functions).

## Acceptance Criteria
- Legacy data with junk tags is cleaned on load.
- Existing storage tests still pass; no regression in branch coverage (≥80%).

## Verification
- `pytest tests/test_storage.py -q` — all pass.
- `--cov-branch --cov=src` → storage.py ≥80%.