# Task Card 06 — Model Coverage (src/models.py, tests/test_models.py)

## Goal
Lift `src/models.py` branch coverage to ≥80% by adding tests for uncovered branches. No production-code changes unless a test reveals a defect (none expected).

## Allowed Paths
- `tests/test_models.py`
- `src/models.py` (read-only; edit only if a test exposes a real defect, with justification)

## DO NOT Touch
- `src/storage.py`, `src/search.py`, `src/cli.py`
- Any network, auth, database, or config code

## Dependencies
- Task 01 (models) complete.

## Spec
Add tests covering:
- `Note(tags=None)` → tags becomes `[]`.
- `_validate` raise branches: bad id (non-str / empty), non-str title, non-str body, bad tags (non-list / non-str element), non-str created_at, non-str updated_at.
- `Note.__eq__` with a non-Note argument → False.
- `Note.__repr__` returns `"Note(...)"`.
- `from_dict` reject paths already covered; ensure branch parts for missing keys defaults are exercised.

## Acceptance Criteria
- `src/models.py` branch coverage ≥80%.
- All existing tests still pass.

## Test Requirements
- `test_note_tags_none_defaults_empty`
- `test_validate_bad_id`, `test_validate_bad_title`, `test_validate_bad_body`, `test_validate_bad_tags`, `test_validate_bad_created_at`, `test_validate_bad_updated_at`
- `test_eq_with_non_note_returns_false`
- `test_repr_format`

## Verification
- `pytest tests/test_models.py -q` — all pass.
- `pytest --cov=src --cov-branch` → `src/models.py` ≥80%.