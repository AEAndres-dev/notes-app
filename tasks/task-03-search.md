# Task Card 03 — Search (src/search.py)

## Goal
Implement text search (case-insensitive substring on title+body) and tag filtering.

## Allowed Paths
- `src/search.py`
- `tests/test_search.py`

## DO NOT Touch
- `src/models.py`, `src/storage.py`, `src/cli.py` (read-only deps)
- Any network, auth, database, or config code

## Dependencies
- Task 01 (models.py) must be complete.

## Spec
- `search_text(notes: list[Note], query: str) -> list[Note]`: return notes whose title or body contains query (case-insensitive). Empty query returns all notes.
- `search_tag(notes: list[Note], tag: str) -> list[Note]`: return notes where tag in note.tags. Case-sensitive tag match.
- `all_tags(notes: list[Note]) -> dict[str, int]`: unique tags → count, sorted by count desc then name asc.

## Acceptance Criteria (from TRD)
- AC 3: `search <query>` returns notes whose title or body contains query (case-insensitive).
- AC 4: `search --tag <tag>` returns notes tagged with that tag.
- AC 5: `tags` lists all unique tags with counts (data layer; CLI formats output).
- AC 8: Tags round-trip (search reflects storage faithfully).

## Test Requirements (from @qa-safety)
- `test_search.py`:
  - `test_search_text_case_insensitive`
  - `test_search_text_empty_query_returns_all`
  - `test_search_text_no_match_returns_empty`
  - `test_search_tag_filters_correctly`
  - `test_search_tag_no_match`
  - `test_all_tags_counts_and_sorting`
  - `test_all_tags_empty_store`

## Verification
- Run `pytest tests/test_search.py -q` — all pass.
- Imports only `models.py` and stdlib.