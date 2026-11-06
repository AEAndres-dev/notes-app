"""Tests for Note model (AC8)."""
import pytest

from src.models import Note


def test_note_to_dict_roundtrip():  # AC8
    note = Note(
        id="abc",
        title="t",
        body="b",
        tags=["x", "y"],
        created_at="2024-01-01T00:00:00",
        updated_at="2024-01-01T00:00:00",
    )
    d = note.to_dict()
    restored = Note.from_dict(d)
    assert restored == note
    assert restored.tags == ["x", "y"]


def test_from_dict_rejects_bad_tags():  # AC8
    data = {
        "id": "abc",
        "title": "t",
        "body": "b",
        "tags": "not-a-list",
        "created_at": "ts",
        "updated_at": "ts",
    }
    with pytest.raises(ValueError):
        Note.from_dict(data)


def test_from_dict_rejects_empty_id():
    data = {
        "id": "",
        "title": "t",
        "body": "b",
        "tags": [],
        "created_at": "ts",
        "updated_at": "ts",
    }
    with pytest.raises(ValueError):
        Note.from_dict(data)


def test_from_dict_rejects_bad_timestamps():
    data = {
        "id": "abc",
        "title": "t",
        "body": "b",
        "tags": [],
        "created_at": 123,
        "updated_at": "ts",
    }
    with pytest.raises(ValueError):
        Note.from_dict(data)
    data2 = {
        "id": "abc",
        "title": "t",
        "body": "b",
        "tags": [],
        "created_at": "ts",
        "updated_at": None,
    }
    with pytest.raises(ValueError):
        Note.from_dict(data2)


def test_note_tags_none_defaults_empty():
    note = Note(id="abc", title="t", body="b", tags=None)
    assert note.tags == []


def test_validate_bad_id():
    with pytest.raises(ValueError):
        Note(id="", title="t", body="b")
    with pytest.raises(ValueError):
        Note(id=123, title="t", body="b")


def test_validate_bad_title():
    with pytest.raises(ValueError):
        Note(id="abc", title=123, body="b")


def test_validate_bad_body():
    with pytest.raises(ValueError):
        Note(id="abc", title="t", body=123)


def test_validate_bad_tags():
    with pytest.raises(ValueError):
        Note(id="abc", title="t", body="b", tags=[1, "x"])


def test_validate_bad_created_at():
    with pytest.raises(ValueError):
        Note(id="abc", title="t", body="b", created_at=123)


def test_validate_bad_updated_at():
    with pytest.raises(ValueError):
        Note(id="abc", title="t", body="b", updated_at=None)


def test_eq_with_non_note_returns_false():
    note = Note(id="abc", title="t", body="b")
    assert (note == "not a note") is False
    assert (note == 42) is False


def test_repr_format():
    note = Note(id="abc", title="t", body="b")
    r = repr(note)
    assert r.startswith("Note(")
    assert "abc" in r


def test_from_dict_missing_keys_defaults():
    data = {"id": "abc", "title": "t", "body": "b"}
    note = Note.from_dict(data)
    assert note.tags == []
    assert note.created_at == ""
    assert note.updated_at == ""
