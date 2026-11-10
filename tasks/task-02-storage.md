# Task Card 02 — Storage Layer (src/storage.py)

## Goal
Implement read/write of `data/notes.json` with atomic writes and JSON validation on load. ID generation via UUID4.

## Allowed Paths
- `src/storage.py`
- `tests/test_storage.py`

## DO NOT Touch
- `src/models.py` (read-only dependency; do not modify)
- `src/search.py`, `src/cli.py`
- Any network, auth, database, or config code beyond `notes.json`

## Dependencies
- Task 01 (models.py) must be complete.

## Spec
- `load_notes(path="data/notes.json") -> list[Note]`: read file, parse JSON, validate against Note schema. If file missing, return empty list. If malformed JSON or bad schema, raise `ValueError` with user-facing message.
- `save_notes(notes, path="data/notes.json")`: write to `{path}.tmp`, then `os.replace()` to path. Create parent dir if missing.
- `add_note(title, body, tags) -> Note`: create Note with UUID4 id and timestamps, append, save, return.
- `delete_note(note_id) -> bool`: remove by id, save, return True if found.
- `edit_note(note_id, **fields) -> Note | None`: update fields, set updated_at, save.

## Acceptance Criteria (from TRD)
- AC 1: `add` creates note with title/body/tags, persists to `notes.json`.
- AC 6: Malformed `notes.json` → user-facing error, clean exit, no traceback.
- AC 7: Concurrent writes don't corrupt the store (atomic tmp+replace). Semantics: last-write-wins, no partial/corrupt file, no leftover `.tmp`. "Both notes present" is NOT required (v2 enhancement if needed).

## Test Requirements (from @qa-safety)
- `test_storage.py`:
  - `test_load_missing_file_returns_empty`
  - `test_load_malformed_json_raises_valueerror`
  - `test_load_bad_schema_raises_valueerror`
  - `test_save_atomic_tmp_replace` — assert tmp file used then replaced.
  - `test_save_crash_leaves_original_intact` — simulate crash mid-write.
  - `test_concurrent_writes_no_corruption` — parallel adds: valid JSON, at least one note (last-write-wins), no leftover `.tmp`.
  - `test_add_note_persists_and_returns`
  - `test_delete_note_removes_and_returns_true`
  - `test_edit_note_updates_fields_and_timestamp`
  - `test_uuid_uniqueness` — no two notes share id.

## Verification
- Run `pytest tests/test_storage.py -q` — all pass.
- Imports only `models.py` and stdlib.