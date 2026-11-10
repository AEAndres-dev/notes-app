"""Storage layer for notes.json."""

import json
import os
import uuid
from datetime import datetime
from pathlib import Path

from .models import Note


DEFAULT_PATH = "data/notes.json"


def _now():
    return datetime.now().isoformat()


def _resolve_path(path):
    if path is None:
        return DEFAULT_PATH
    return str(path)


def _coerce_tags(tags):
    if tags is None:
        return []
    if isinstance(tags, str):
        if tags == "":
            return []
        return [t.strip() for t in tags.split(",") if t.strip() != ""]
    if isinstance(tags, (list, tuple)):
        out = []
        for t in tags:
            if isinstance(t, str) and "," in t:
                out.extend([x.strip() for x in t.split(",") if x.strip() != ""])
            else:
                val = str(t).strip()
                if val != "":
                    out.append(val)
        return out
    return [str(tags)]


def load_notes(path=DEFAULT_PATH):
    p = Path(_resolve_path(path))
    if not p.exists():
        return []
    try:
        with p.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        raise ValueError("Malformed notes file: %s" % exc)
    if not isinstance(data, list):
        raise ValueError("notes file must contain a JSON array")
    notes = []
    for item in data:
        try:
            note = Note.from_dict(item)
            note.tags = _coerce_tags(note.tags)
            notes.append(note)
        except ValueError as exc:
            raise ValueError("Malformed note entry: %s" % exc)
    return notes


def save_notes(notes, path=DEFAULT_PATH):
    target = Path(_resolve_path(path))
    target.parent.mkdir(parents=True, exist_ok=True)
    # create a tmp file (prefer the canonical name; fall back if locked/busy)
    tmp = Path(str(target) + ".tmp")
    try:
        fd = os.open(str(tmp), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    except FileExistsError:
        tmp = Path(str(target) + ".tmp." + uuid.uuid4().hex)
        fd = os.open(str(tmp), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump([n.to_dict() for n in notes], fh, indent=2)
            fh.flush()
        last_exc = None
        for _ in range(50):
            try:
                os.replace(tmp, target)
                last_exc = None
                break
            except OSError as exc:
                last_exc = exc
        if last_exc is not None:
            raise last_exc
    except Exception:
        try:
            if tmp.exists():
                tmp.unlink()
        except OSError:
            pass
        raise


def _resolve_path_arg(path, args, kwargs):
    resolved = path
    for a in args:
        if isinstance(a, str):
            resolved = a
        elif isinstance(a, Path):
            resolved = str(a)
    if resolved is None:
        resolved = kwargs.pop("path", None)
    if resolved is None:
        resolved = kwargs.pop("file", None)
    if resolved is None:
        resolved = DEFAULT_PATH
    return resolved


def add_note(title, body, tags=None, *args, path=None, **kwargs):
    resolved_path = _resolve_path_arg(path, args, kwargs)
    if "tags" in kwargs and tags is None:
        tags = kwargs.pop("tags")
    coerced = _coerce_tags(tags)
    note = Note(
        id=str(uuid.uuid4()),
        title=title,
        body=body,
        tags=coerced,
        created_at=_now(),
        updated_at=_now(),
    )
    notes = load_notes(resolved_path)
    notes.append(note)
    save_notes(notes, resolved_path)
    return note


def delete_note(note_id, *args, path=None, **kwargs):
    resolved_path = _resolve_path_arg(path, args, kwargs)
    notes = load_notes(resolved_path)
    new_notes = [n for n in notes if n.id != note_id]
    if len(new_notes) == len(notes):
        return False
    save_notes(new_notes, resolved_path)
    return True


def edit_note(note_id, *args, path=None, **fields):
    updates = {}
    resolved_path = path
    for a in args:
        if isinstance(a, dict):
            updates.update(a)
        elif isinstance(a, str):
            resolved_path = a
        elif isinstance(a, Path):
            resolved_path = str(a)
    if resolved_path is None:
        resolved_path = fields.pop("path", None)
    if resolved_path is None:
        resolved_path = fields.pop("file", None)
    if resolved_path is None:
        resolved_path = DEFAULT_PATH
    updates.update({k: v for k, v in fields.items() if k not in ("path", "file")})
    notes = load_notes(resolved_path)
    for note in notes:
        if note.id == note_id:
            if "title" in updates:
                note.title = updates["title"]
            if "body" in updates:
                note.body = updates["body"]
            if "tags" in updates:
                note.tags = _coerce_tags(updates["tags"])
            note.updated_at = _now()
            save_notes(notes, resolved_path)
            return note
    return None
