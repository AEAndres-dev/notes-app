# Browser GUI Testing — Notes App v2 Web App

**Status:** Ready for manual browser testing  
**Date:** 2026-11-10  
**Related:** task-07 (server), task-08 (frontend), task-10 (web tests)

---

## 1. Quick start — manual browser test

The v2 web app is a stdlib-only HTTP server with a vanilla-JS frontend. No build step, no npm, no framework.

### Step 1 — Start the server

```bash
# Default port 8000
python -m src.server

# Or override the port
NOTES_PORT=9000 python -m src.server
```

You should see:
```
Serving notes on http://127.0.0.1:8000
```

### Step 2 — Open in browser

Navigate to: **`http://127.0.0.1:8000`**

The page loads `static/index.html` with:
- A note list area (shows "No notes found" when empty)
- An add-note form (title, body, tags)
- A search input (debounced 300ms)
- A tag filter input

### Step 3 — Exercise the GUI journeys

| Journey | Action | Expected result |
|---------|--------|-----------------|
| Load empty state | Open `http://127.0.0.1:8000` with no `data/notes.json` | "No notes found" message |
| Add note | Fill title/body/tags, click **Add Note** | New note card appears at top of list |
| List notes | Page auto-loads `/api/notes` on load | All notes rendered as cards |
| Search | Type in search box | List filters after 300ms debounce |
| Tag filter | Type a tag in filter box | List filters to matching notes |
| Combined | Search + tag filter together | Intersection of both filters |
| Edit note | Click **Edit** on a card, change fields, click **Save** | Card updates in place |
| Delete note | Click **Delete** on a card, confirm | Card removed from list |

---

## 2. API endpoints (for manual verification)

All API traffic goes to `http://127.0.0.1:8000/api/notes` — you can verify with `curl` or browser DevTools Network tab:

```bash
# List all notes
curl http://127.0.0.1:8000/api/notes

# Create a note
curl -X POST http://127.0.0.1:8000/api/notes \
  -H "Content-Type: application/json" \
  -d '{"title":"Hello","body":"World","tags":"web,demo"}'

# Get a single note
curl http://127.0.0.1:8000/api/notes/<note-id>

# Update a note
curl -X PUT http://127.0.0.1:8000/api/notes/<note-id> \
  -H "Content-Type: application/json" \
  -d '{"title":"Updated"}'

# Delete a note
curl -X DELETE http://127.0.0.1:8000/api/notes/<note-id>

# Filter by tag
curl "http://127.0.0.1:8000/api/notes?tag=web"

# Search
curl "http://127.0.0.1:8000/api/notes?q=hello"
```

---

## 3. Requirements / skills for automated browser testing

The current test suite (`tests/test_server.py`) covers the API layer with 32 cases using only `stdlib` + `pytest`. It does **not** include automated browser (DOM) testing. To add GUI automation, you would need one of the following:

| Tool | Type | Notes |
|------|------|-------|
| **Playwright** | Browser automation | Chromium/Firefox/WebKit; Python package `playwright` |
| **Selenium** | Browser automation | Chrome/Firefox/Edge; Python package `selenium` + WebDriver |
| **Pyppeteer** | Chrome automation | Python port of Puppeteer |

### Constraint warning

The project is **stdlib-only in `src/`** (TRD-v2-web §2). Browser automation tools are third-party packages and **cannot be added to `src/`**. They could be added to `tests/` as test-only dependencies, but that would require a license review per the System Architect policy (AGPL flag before dev starts).

### Recommended approach for v2

For v2, manual browser testing (Section 1) plus the API test suite (`tests/test_server.py`) is sufficient. If automated GUI testing becomes a priority in v3, add a browser automation tool as a test-only dependency and create `tests/test_gui.py`.

---

## 4. CI / staging preview

Per TRD-v2-web §12, the CI staging deploy runs `python -m src.server` on port 8000 and posts a preview URL (e.g. `https://staging-pr14.dev`). That URL can be opened in a browser for end-to-end GUI verification on each PR.

---

## 5. Troubleshooting

| Issue | Likely cause | Fix |
|-------|--------------|-----|
| `Port already in use` | Another process on 8000 | Use `NOTES_PORT=9000 python -m src.server` |
| Page loads but no notes appear | Server not running, or API error | Check browser DevTools Console + Network tab |
| Changes not reflecting | Browser cache | Hard refresh (Ctrl+F5) or disable cache in DevTools |
| `data/notes.json` malformed | Corrupt write | Delete `data/notes.json` and restart (store recreated on next add) |
