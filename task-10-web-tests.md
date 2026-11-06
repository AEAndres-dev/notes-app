# Task Card 10 — Web Layer Tests (tests/test_server.py)

## Goal
Implement `tests/test_server.py` per TRD-v2-web §11.1 (18 cases) plus @qa-safety's 7 additional security/validation cases. No production code changes.

## Allowed Paths
- `tests/test_server.py`

## DO NOT Touch
- `src/*` (read-only dependency)

## Dependencies
- task-07 (server) and task-09 (storage normalization).

## Spec — TRD §11.1 (18 cases)
`test_get_index`, `test_get_notes_empty`, `test_get_notes_populated`, `test_get_notes_filter_tag`, `test_get_notes_search`, `test_get_note_by_id`, `test_get_note_not_found`, `test_create_note`, `test_create_note_missing_title`, `test_create_note_tags_normalized`, `test_update_note`, `test_update_note_not_found`, `test_delete_note`, `test_delete_note_not_found`, `test_malformed_store`, `test_static_file_serving`, `test_path_traversal_blocked`, `test_bind_localhost_only`.

## Additional QA cases (required)
- `test_malformed_json_body` → 400
- `test_create_note_missing_body` → 400
- `test_create_note_body_too_long` → 400
- `test_create_note_title_too_long` → 400
- `test_unknown_fields_ignored` → 200, extra fields dropped
- `test_oversized_body_rejected_413` → 413
- `test_disallowed_static_extension` → 403/404
- `test_server_starts_and_binds` (startup integration: binds 127.0.0.1 on NOTES_PORT override, serves, shuts down cleanly)

## Acceptance Criteria
- `src/server.py` ≥80% branch; existing modules do not drop below 80% (regression guard).
- No tracebacks in any error response body.

## Verification
- `pytest tests/test_server.py -q` — all pass.
- `pytest --cov=src --cov-branch` — server.py ≥80%, models/storage/search/cli ≥80%.