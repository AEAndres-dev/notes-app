# UX_EXPERIENCE.md — Notes App v1

## Setup & Execution Steps

- **Repository:** `C:\Users\dev\notes-app-tasks`
- **Stack:** Python 3.x, stdlib-only (no third-party dependencies). CLI-driven (`argparse` subcommands).
- **Build/Test command:** `python -m pytest` → **35/35 tests passed** (0.38s).
- **Run command:** `python -m src.cli <subcommand>` (add/list/search/tags).
- **Preview side-tab:** **Not applicable.** This application is a pure CLI tool with no HTTP server, no frontend, and no web interface. There is no `localhost:<port>` to mount in the Hermes preview pane. The "walkthrough" below was conducted via terminal execution of the CLI commands.

## Visual & Structural Evaluation

- **Layout / Typography:** N/A — terminal stdout. Output format is compact single-line records:
  `<uuid> | <title> | <comma-separated tags>`.
- **Theme consistency:** N/A (no UI). CLI uses plain ASCII, no color, no progress indicators.
- **Responsiveness:** N/A.

## User Journey Walkthrough

Executed against a fresh store (no `data/notes.json`):

1. **Add notes** — `python -m src.cli add "Welcome to Notes" "..." --tags welcome,work` etc.
   - Result: `Added note <uuid>` printed for each; 3 notes persisted.
   - Exit code 0.
2. **List** — `python -m src.cli list`
   - Result: 3 single-line records with id, title, tags. Empty store prints `No notes found`.
3. **Full-text search** — `python -m src.cli search "milk"`
   - Result: matched the "Shopping list" note (case-insensitive substring on title/body).
   - Empty query returns all notes; no match prints nothing.
4. **Tag filter** — `python -m src.cli search --tag work`
   - Result: 2 notes with the `work` tag.
5. **Tags summary** — `python -m src.cli tags`
   - Result: tags sorted by count desc then name asc (`work: 2`, `personal: 1`, `welcome: 1`).
6. **Malformed store handling** — verified by tests: malformed JSON raises `ValueError` → CLI prints `Error: ...` to stderr and exits 1.

## UX Friction Points & Edge Cases

- **No interactive help beyond argparse** — `--help` exists per subcommand; acceptable for a CLI.
- **No body display in list/search** — only title + tags shown; users must open `data/notes.json` to read note bodies. Minor UX limitation.
- **`search` with no query and no `--tag`** defaults to empty string and returns all notes (could be surprising; tests assert this).
- **No pagination** — fine for a lightweight local store.
- **No color / formatting** — plain text; acceptable for v1 stdlib-only scope.
- **Atomic writes** — tmp+replace with 50 retries; crash-safety verified by tests.

## Final Verdict

**PASS** — All 35 tests pass; CLI user journeys (add/list/search/tags) work as documented. No web frontend exists, so no browser preview could be mounted; this is expected for a stdlib-only CLI app. No modifications required.
