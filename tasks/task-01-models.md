# Task Card 01 — Note Model (src/models.py)

## Goal
Implement the `Note` dataclass and its serialization/deserialization to dict. No other files.

## Allowed Paths
- `src/models.py`
- `tests/test_models.py`

## DO NOT Touch
- `src/storage.py`, `src/search.py`, `src/cli.py`
- Any network, auth, database, or config code
- `data/notes.json`

## Dependencies
None. This is the foundation task.

## Spec
`Note` dataclass with fields:
- `id: str` (non-empty)
- `title: str`
- `body: str`
- `tags: list[str]`
- `created_at: str` (ISO timestamp)
- `updated_at: str` (ISO timestamp)

Serialization:
- `to_dict() -> dict` returns a JSON-serializable dict with all fields.
- `from_dict(data: dict) -> Note` reconstructs a Note, validating types:
  - `tags` must be `list[str]`; raise `ValueError` otherwise.
  - `id` must be non-empty string.
  - timestamps must be strings.
- On invalid input, raise `ValueError` with a user-facing message (no traceback propagation).

## Acceptance Criteria (from TRD)
- Tags field survives serialization round-trip (AC 8 partial).

## Test Requirements (from @qa-safety)
- `test_models.py`:
  - `test_note_to_dict_roundtrip` — tags survive edit/delete.
  - `test_from_dict_rejects_bad_tags` — non-list tags raises ValueError.
  - `test_from_dict_rejects_empty_id` — empty id raises ValueError.
  - `test_from_dict_rejects_bad_timestamps` — non-string timestamps raise ValueError.

## Verification
- Run `pytest tests/test_models.py -q` — all pass.
- No imports of storage/search/cli.