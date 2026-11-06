# Task Card 05 — Storage Hardening & Coverage (src/storage.py, tests/test_storage.py)

## Goal
Fix the `_coerce_tags` empty/whitespace-tag bug, harden the concurrent-writes test so worker errors fail the test, and lift `src/storage.py` branch coverage to ≥80%. No new features.

## Allowed Paths
- `src/storage.py`
- `tests/test_storage.py`

## DO NOT Touch
- `src/models.py`, `src/search.py`, `src/cli.py`
- Any network, auth, database, or config code beyond `notes.json`
- `data/notes.json` (test fixtures only via tmp paths)

## Dependencies
- Task 02 (storage) complete; Task 01 (models) complete.

## Spec
1. `_coerce_tags` must consistently strip and drop empty tags on the list/tuple path:
   - For each element: if it is a str containing ",", split and strip+filter each piece; otherwise `str(element).strip()` and drop if empty.
   - Remove the `if not out: return [str(t) for t in tags]` fallback that returns raw unstripped values.
   - Result: `_coerce_tags(["a,b",""])` → `["a","b"]`; `_coerce_tags([" , "])` → `[]`.
2. Harden `test_concurrent_writes_no_corruption`: collect exceptions raised by worker threads; assert the list is empty (or fail with the captured errors). Keep the existing valid-JSON / ≥1 note / no-leftover-`.tmp` assertions.
3. Add tests covering previously-uncovered branches:
   - `_resolve_path(None)` → `DEFAULT_PATH`.
   - `_coerce_tags` list-path branches (comma-in-element split, non-str element, all-empty → `[]`).
   - `save_notes` retry-failure path and `except Exception` cleanup (simulate `os.replace` always raising; assert tmp removed and exception propagates).
   - `_resolve_path_arg` kwargs fallbacks (`path` then `file` then default).

## Acceptance Criteria
- AC 7 (concurrency) still holds; test now fails on worker errors.
- AC 8 (tags round-trip): no empty/whitespace tags persist.
- `src/storage.py` branch coverage ≥80%.

## Test Requirements
- `test_coerce_tags_drops_empty_and_strips`
- `test_coerce_tags_all_empty_returns_empty`
- `test_resolve_path_none_returns_default`
- `test_save_notes_retry_failure_cleans_tmp`
- `test_resolve_path_arg_kwargs_fallback`
- Existing `test_concurrent_writes_no_corruption` updated to assert no worker errors.

## Verification
- `pytest tests/test_storage.py -q` — all pass.
- `pytest --cov=src --cov-branch` → `src/storage.py` ≥80%.
- Imports only `models.py` and stdlib.