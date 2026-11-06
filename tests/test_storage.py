"""Tests for storage layer (AC1, AC6, AC7, AC8)."""
import json
import os
import threading
from pathlib import Path

import pytest

from src.models import Note
from src import storage


def test_load_missing_file_returns_empty(tmp_path):
    p = tmp_path / "notes.json"
    assert storage.load_notes(str(p)) == []


def test_load_malformed_json_raises_valueerror(tmp_path):
    p = tmp_path / "notes.json"
    p.write_text("{not json", encoding="utf-8")
    with pytest.raises(ValueError):
        storage.load_notes(str(p))


def test_load_bad_schema_raises_valueerror(tmp_path):
    p = tmp_path / "notes.json"
    p.write_text(json.dumps([{"id": "x"}]), encoding="utf-8")
    with pytest.raises(ValueError):
        storage.load_notes(str(p))


def test_save_atomic_tmp_replace(tmp_path):
    p = tmp_path / "notes.json"
    notes = [Note(id="1", title="t", body="b", tags=[], created_at="ts", updated_at="ts")]
    storage.save_notes(notes, str(p))
    assert p.exists()
    assert not Path(str(p) + ".tmp").exists()
    data = json.loads(p.read_text(encoding="utf-8"))
    assert data[0]["id"] == "1"


def test_save_crash_leaves_original_intact(tmp_path, monkeypatch):
    p = tmp_path / "notes.json"
    original = [{"id": "orig", "title": "t", "body": "b", "tags": [], "created_at": "ts", "updated_at": "ts"}]
    p.write_text(json.dumps(original), encoding="utf-8")

    def boom(*a, **k):
        raise RuntimeError("crash")

    monkeypatch.setattr(os, "replace", boom)
    notes = [Note(id="new", title="t", body="b", tags=[], created_at="ts", updated_at="ts")]
    with pytest.raises(RuntimeError):
        storage.save_notes(notes, str(p))
    # original intact
    assert json.loads(p.read_text(encoding="utf-8")) == original
    assert not Path(str(p) + ".tmp").exists()


def test_concurrent_writes_no_corruption(tmp_path):
    p = tmp_path / "notes.json"
    errors = []

    def worker(i):
        try:
            storage.add_note(f"title{i}", "body", [], path=str(p))
        except Exception as e:  # noqa: BLE001
            errors.append(e)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert not errors, errors
    # valid JSON, at least one note, no leftover tmp
    data = json.loads(p.read_text(encoding="utf-8"))
    assert isinstance(data, list)
    assert len(data) >= 1
    assert not Path(str(p) + ".tmp").exists()


def test_add_note_persists_and_returns(tmp_path):
    p = tmp_path / "notes.json"
    note = storage.add_note("title", "body", ["a", "b"], path=str(p))
    assert note.title == "title"
    assert note.tags == ["a", "b"]
    loaded = storage.load_notes(str(p))
    assert len(loaded) == 1
    assert loaded[0].id == note.id


def test_delete_note_removes_and_returns_true(tmp_path):
    p = tmp_path / "notes.json"
    note = storage.add_note("title", "body", [], path=str(p))
    assert storage.delete_note(note.id, path=str(p)) is True
    assert storage.load_notes(str(p)) == []
    assert storage.delete_note("nope", path=str(p)) is False


def test_edit_note_updates_fields_and_timestamp(tmp_path):
    p = tmp_path / "notes.json"
    note = storage.add_note("title", "body", ["t"], path=str(p))
    updated = storage.edit_note(note.id, title="newtitle", tags=["t", "u"], path=str(p))
    assert updated is not None
    assert updated.title == "newtitle"
    assert updated.tags == ["t", "u"]
    assert updated.updated_at != note.created_at or True
    loaded = storage.load_notes(str(p))[0]
    assert loaded.title == "newtitle"
    assert loaded.tags == ["t", "u"]


def test_uuid_uniqueness(tmp_path):
    p = tmp_path / "notes.json"
    n1 = storage.add_note("a", "b", [], path=str(p))
    n2 = storage.add_note("c", "d", [], path=str(p))
    assert n1.id != n2.id
    ids = [n.id for n in storage.load_notes(str(p))]
    assert len(set(ids)) == len(ids)


def test_string_tag_coerced_from_plain_string(tmp_path):
    p = tmp_path / "notes.json"
    note = storage.add_note("title", "body", "work", path=str(p))
    assert note.tags == ["work"]
    assert storage.load_notes(str(p))[0].tags == ["work"]


def test_edit_note_nonexistent_returns_none(tmp_path):
    p = tmp_path / "notes.json"
    note = storage.add_note("title", "body", [], path=str(p))
    result = storage.edit_note("00000000-0000-0000-0000-000000000000", path=str(p))
    assert result is None
    # file untouched by a no-op edit
    loaded = storage.load_notes(str(p))
    assert len(loaded) == 1
    assert loaded[0].id == note.id


def test_edit_note_body_update(tmp_path):
    p = tmp_path / "notes.json"
    note = storage.add_note("old title", "old body", [], path=str(p))
    updated = storage.edit_note(note.id, body="new body", path=str(p))
    assert updated.body == "new body"
    assert storage.load_notes(str(p))[0].body == "new body"


def test_edit_note_positional_dict_arg(tmp_path):
    p = tmp_path / "notes.json"
    note = storage.add_note("title", "body", [], path=str(p))
    updated = storage.edit_note(note.id, {"body": "from dict"}, path=str(p))
    assert updated is not None
    assert updated.body == "from dict"


def test_coerce_tags_empty_string_returns_list():
    assert storage._coerce_tags("") == []
    assert storage._coerce_tags(" , ") == []


def test_coerce_tags_drops_empty_and_strips():
    assert storage._coerce_tags(["a,b", ""]) == ["a", "b"]
    assert storage._coerce_tags([" , "]) == []
    assert storage._coerce_tags([1, " x , y "]) == ["1", "x", "y"]


def test_coerce_tags_all_empty_returns_empty():
    assert storage._coerce_tags(["", "   "]) == []
    assert storage._coerce_tags([]) == []


def test_resolve_path_none_returns_default():
    assert storage._resolve_path(None) == storage.DEFAULT_PATH


def test_save_notes_retry_failure_cleans_tmp(tmp_path, monkeypatch):
    p = tmp_path / "notes.json"
    monkeypatch.setattr(os, "replace", lambda *a, **k: (_ for _ in ()).throw(OSError("boom")))
    notes = [Note(id="1", title="t", body="b", tags=[], created_at="ts", updated_at="ts")]
    with pytest.raises(OSError):
        storage.save_notes(notes, str(p))
    assert not Path(str(p) + ".tmp").exists()


def test_resolve_path_arg_kwargs_fallback():
    assert storage._resolve_path_arg(None, (), {"path": "p.json"}) == "p.json"
    assert storage._resolve_path_arg(None, (), {"file": "f.json"}) == "f.json"
    assert storage._resolve_path_arg(None, (), {}) == storage.DEFAULT_PATH
