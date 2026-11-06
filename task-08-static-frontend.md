# Task Card 08 — Static Frontend (static/*)

## Goal
Build the vanilla HTML/CSS/JS single-page frontend per TRD-v2-web §7. No build step, no bundler, no npm, no framework.

## Allowed Paths
- `static/index.html`
- `static/style.css`
- `static/app.js`

## DO NOT Touch
- `src/*`, `tests/*`, `data/*`

## Dependencies
- task-07 (server must serve static files).

## Spec
- `index.html`: single page with note list, add form, search input, tag filter.
- `app.js`: fetch-based; on load GET /api/notes → render; add → POST → prepend; edit → PUT → update card; delete → DELETE → remove; search → debounce 300ms → GET /api/notes?q=; tag filter → GET /api/notes?tag=; empty state "No notes found".
- `style.css`: minimal, responsive, no framework (no Bootstrap/Tailwind).
- Static files served by server.py from `static/` relative to project root.

## Acceptance Criteria
- Frontend renders note list and supports add/edit/delete/search/tag-filter.
- No build step; runs directly in browser.

## Verification
- Manual walkthrough in browser via @code-runner once server live.