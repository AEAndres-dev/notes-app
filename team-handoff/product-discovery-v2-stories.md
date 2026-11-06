# Product Discovery — v2 User Stories & Acceptance Criteria

**Source:** `TRD-v2-web.md` (system-architect) + product handoff v2 directions A–D
**Scope (this round):** A (tag hygiene) + C (sync/export) as committed; B (concurrency-safe store) as flagship spike; D (richer content) deferred to v3.
**Owner of scope/guardrails:** @project-manager (cuts cards from §15 of TRD).

---

## Story A — Tag hygiene as a designed contract

**User story:** As a note-taker, when I add or edit tags with stray spaces, commas, or empty entries, the app normalizes them so my `tags` view and `search --tag` are trustworthy — in both the CLI and the web UI.

**Acceptance criteria:**
- A1. On create and update (CLI + API), tags input is split on comma, each trimmed, empties dropped, duplicates collapsed (case-sensitive match).
- A2. Legacy data: `load_notes` normalizes tags on read, so old stores with junk tags are cleaned transparently on next load (single enforcement point per TRD §7).
- A3. `tags` summary never prints empty/whitespace-only tags; count reflects normalized tags only.
- A4. `search --tag <t>` matches after normalization (e.g. ` --tag " work "` matches a note tagged `work`).
- A5. Web UI: tag chips render normalized tags; inline tag edit re-normalizes on save (gated on A1).
- A6. No schema change: `tags` remains `list[str]` in the data model.

**Out of scope:** tag rename/merge across notes; tag colors; tag hierarchy.

---

## Story C — Sync/export surface

**User story:** As a user, I can move my notes between machines without hand-copying JSON, and round-trip without data loss or duplicates.

**Acceptance criteria:**
- C1. `export --format json` writes the full store to a path; `export --format md` writes one markdown file per note (title, tags, body, created/updated).
- C2. `import <file>` reads JSON or a directory of markdown files; dedups by note id; on id collision, keeps the newer `updated_at` (last-write-wins, consistent with AC7).
- C3. Round-trip test: export → import on a fresh store yields identical note set (ids, titles, bodies, tags, timestamps).
- C4. Web UI exposes Export/Import buttons (download + file picker); no auth required (local-only per TRD).
- C5. Import reports counts: added / updated / skipped, printed to stdout (CLI) and shown in UI.
- C6. Malformed import file → clean error, no partial write, no traceback (mirrors CLI exit-1 / API clean-error contract).

**Out of scope:** cloud sync, git auto-commit, conflict UI.

---

## Story B — Concurrency-safe store (flagship spike, v2 or v3)

**User story:** As a user editing notes from two terminals or two browser tabs, I never lose a note silently; conflicts surface instead of being overwritten.

**Acceptance criteria (spike-level, to be refined):**
- B1. Spike card: evaluate per-note files vs. lockfile+merge; produce a recommendation doc, no code change to v2 storage.
- B2. If adopted: atomic append with per-note files OR advisory lock + merge-on-conflict; document resolution policy.
- B3. Last-write-wins remains the v2 contract (AC7 carried over); B is the v3 upgrade path.
- B4. Concurrency smoke test (ThreadingHTTPServer + concurrent adds) stays green: valid JSON, no leftover `.tmp`, ≥1 note (carried from task-05).

**Out of scope for v2:** full merge UI, three-way conflict resolution.

---

## Story D — Richer note content (deferred to v3)

Markdown body, attachments, reminders. Held until A–C land; content features on a fragile store is how data loss happens. No ACs this round.

---

## Cross-cutting (web pivot)

- W1. Empty store → "No notes found" equivalent in web UI (no 500, no traceback).
- W2. Malformed store → clean error payload in API, mirrors CLI exit-1 contract.
- W3. Port 8000 default, `NOTES_PORT` env override, bind `127.0.0.1` only.
- W4. Tag hygiene (A) ships in web v2 — not deferred.
- W5. QA gate: ≥80% branch coverage on `src/server.py` (18 test cases per TRD §11.1) — owned by @qa-safety.

## Handoff

@project-manager — please cut cards from TRD §15 + these stories, with allowed/DO-NOT-touch boundaries and AC→test matrix as usual. Suggested card order: storage normalization (A2) → web server (TRD §15) → static frontend (tag chips gated on A) → web tests (QA) → export/import (C) → concurrency spike (B).

No v2 card is cut before the TRD — now landed. Standing by for card scoping.

— @product-discovery
