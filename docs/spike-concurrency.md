# Concurrency Spike — v3 Multi-Writer Storage Models

**Status:** Spike (recommendation only — no production code shipped)  
**Date:** 2026-11-10  
**Owner:** @product-discovery / @system-architect  
**Allowed paths:** `docs/spike-concurrency.md`

---

## 1. Context

The notes app (v2) stores all notes in a single JSON file, `data/notes.json`, using atomic
tmp+replace writes (`os.replace`). Writes follow last-write-wins semantics (AC7), which is
acceptable for a single-user local tool but becomes risky when the same store is edited
concurrently from multiple terminals, browser tabs, or devices:

```
Writer A: load()  [reads notes.json: 3 notes]
Writer B: load()  [reads notes.json: 3 notes]
Writer A: append note A, save()  [writes 4 notes]
Writer B: append note B, save()  [writes 4 notes — note A is silently lost]
```

This is a classic TOCTOU (time-of-check-to-time-of-use) race. v2 explicitly defers concurrency
safety to v3 (TRD-v2-web §13 / §14). This spike evaluates three candidate models for v3 and
produces a recommendation.

---

## 2. Candidate models

### A. File lockfile (advisory locking)

Serialize all read-modify-write cycles behind a lockfile (e.g. `data/notes.json.lock`).

**How it works**
1. Before `load_notes`, acquire an exclusive lock on `data/notes.json.lock`.
2. Read, mutate, write via atomic tmp+replace.
3. Release the lock.

**Trade-offs**
| Pro | Con |
|-----|-----|
| Simple to reason about — one writer at a time, no lost updates | Not portable: `fcntl.flock` (Unix) vs `msvcrt.locking` (Windows); stdlib has no cross-platform file lock |
| Works with the existing single-file storage shape | A crashed process can leave a stale lock; needs lock-stealing or TTL complexity |
| Minimal change to storage layer | Blocks concurrent readers too (advisory exclusive lock serializes everything) |
| No schema migration | Adds ~1 syscall round-trip per operation (latency) |

**Best for:** Single-machine, multi-process (CLI + web server on the same device).


### B. One-note-per-file storage

Replace `data/notes.json` with a directory of individual note files, e.g. `data/notes/<uuid>.json`.

**How it works**
- Each note is its own file: `data/notes/<note-id>.json`.
- `load_notes` reads the directory and parses each file.
- `add_note` writes one new file; `edit_note`/`delete_note` touch only the affected file.
- A separate `data/notes/index.json` (optional) can track ordering/metadata.

**Trade-offs**
| Pro | Con |
|-----|-----|
| Naturally concurrent — writers touch different files, no cross-note TOCTOU | Major storage migration; breaks the v1/v2 single-file shape and all existing tooling |
| No lost updates between different notes | Corruption of one file = loss of one note (instead of whole store) |
| Fine-grained locking (per-file) or no locking at all | Listing/search requires scanning the directory (slower for large stores) |
| Works well with sync/export tools (per-file dedup) | Atomicity across multiple notes (e.g. batch edit) becomes harder |

**Best for:** Multi-device sync, high-write workloads, or when per-note isolation is required.


### C. Merge-on-conflict (optimistic concurrency)

Keep the single-file shape, but detect concurrent writes and merge rather than overwrite.

**How it works**
1. Each write includes a version token (e.g. file mtime, hash, or a `version` counter in the store).
2. `save_notes` compares the store's current version against the version the writer read.
3. If versions match → atomic replace (last-write-wins).
4. If versions differ → attempt a field-level merge:
   - Different notes added by both writers → union of note sets.
   - Same note edited by both → last-write-wins on that note (or flag for manual resolution).
5. If merge is impossible (conflicting edits to the same field) → reject with 409 Conflict and ask the client to re-read and retry.

**Trade-offs**
| Pro | Con |
|-----|-----|
| No lost updates for the common case (different notes, different fields) | Most complex to implement correctly; merge semantics for the same note are ambiguous |
| Keeps single-file storage shape (no migration) | Requires a versioning scheme and client-side retry logic |
| Optimistic — no locking overhead when there is no contention | v2 clients (CLI + web) would need version-aware APIs; adds surface area |
| Surfaces conflicts explicitly instead of silently dropping data | Still needs a fallback for unreconcilable conflicts |

**Best for:** Collaborative editing scenarios where users edit different notes simultaneously.


## 3. Comparison matrix

| Criterion | A. Lockfile | B. One-note-per-file | C. Merge-on-conflict |
|-----------|-------------|----------------------|----------------------|
| Prevents lost updates | Yes | Yes (per file) | Yes (with merge) |
| Cross-platform (Win/macOS/Linux) | ⚠️ Partial (stdlib gap) | Yes | Yes |
| Storage migration needed | No | Yes (breaking) | No |
| Implementation complexity | Low | Medium | High |
| Client changes needed | No | No | Yes (retry / versioning) |
| Reader concurrency | Serialized | Parallel | Parallel |
| Crash safety | ⚠️ Stale lock risk | Good | Good |
| Fits v2→v3 evolution | ✅ Natural next step | ❌ Breaks v2 shape | ⚠️ API changes |

## 4. Recommendation

**Adopt Model A (file lockfile) as the v3 default, with Model C (merge-on-conflict) as a future enhancement.**

### Rationale

1. **Least disruptive path.** Model A preserves the single-file `data/notes.json` shape that v1 and v2 already use, so there is no storage migration and no breaking change to the CLI/web API surface. Models B and C both require larger changes (schema migration or versioned APIs).

2. **Matches the app's usage profile.** The notes app is a single-user local tool (TRD §2: "Single-user, no auth in v2"). Contention is expected to be rare — a second browser tab or a background CLI save, not true collaborative editing. A simple lock that serializes writes is more than sufficient and far simpler than merge logic.

3. **Stdlib feasibility.** Python's stdlib lacks a cross-platform file lock, but a small helper can branch on `os.name` (`fcntl` on POSIX, `msvcrt` on Windows) with a fallback retry loop. This is contained in `src/storage.py` and does not leak into the web or CLI layers.

4. **Defer merge complexity.** Model C adds real value only when multiple users edit the *same* note concurrently — outside v3 scope for a single-user tool. It can be revisited if sync/collaboration (product-discovery direction C) becomes a priority.

### Implementation sketch for v3

```python
# src/storage.py — v3 addition (not part of v2)
import os, contextlib

@contextlib.contextmanager
def _locked(path):
    lock_path = str(path) + ".lock"
    # Windows: msvcrt.locking; POSIX: fcntl.flock; fallback: retry loop
    lock_fd = os.open(lock_path, os.O_RDWR | os.O_CREAT, 0o644)
    try:
        _acquire(lock_fd)   # blocking/exclusive
        yield
    finally:
        _release(lock_fd)
        os.close(lock_fd)

def add_note(title, body, tags=None, *args, path=None, **kwargs):
    resolved = _resolve_path_arg(path, args, kwargs)
    with _locked(resolved):
        notes = load_notes(resolved)
        note = Note(...)
        notes.append(note)
        save_notes(notes, resolved)
        return note
```

### Open questions for v3 planning

- Should the lock be blocking (wait) or fail-fast (423 Locked / retry)? Recommendation: blocking with a short timeout, then a clear user-facing error.
- How to handle stale locks from crashed processes? Recommendation: lock TTL based on file mtime, or `O_EXCL` lockfile with PID stamping.
- Does the lock need to cover reads too? Recommendation: no — reads are safe; only write cycles need exclusion.

---

## 5. What is NOT in scope (this spike)

- No code changes to `src/`, `tests/`, or `static/`.
- No implementation of file locking, per-file storage, or merge logic.
- No client-side retry or versioning logic.
- No multi-device sync or cloud storage.

This document is the deliverable. The actual v3 implementation would be a separate effort scoped by @project-manager.