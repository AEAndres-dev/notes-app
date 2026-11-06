"""Tests for search (AC3, AC4, AC5, AC8)."""
from src.models import Note
from src import search


def _notes():
    return [
        Note(id="1", title="Hello", body="world", tags=["work", "x"], created_at="ts", updated_at="ts"),
        Note(id="2", title="Foo", body="bar baz", tags=["personal"], created_at="ts", updated_at="ts"),
        Note(id="3", title="Tagged", body="body", tags=["work"], created_at="ts", updated_at="ts"),
    ]


def test_search_text_case_insensitive():
    res = search.search_text(_notes(), "HELLO")
    assert [n.id for n in res] == ["1"]
    res2 = search.search_text(_notes(), "BaZ")
    assert [n.id for n in res2] == ["2"]


def test_search_text_empty_query_returns_all():
    assert len(search.search_text(_notes(), "")) == 3
    assert len(search.search_text(_notes(), None)) == 3


def test_search_text_no_match_returns_empty():
    assert search.search_text(_notes(), "zzzz") == []


def test_search_tag_filters_correctly():
    res = search.search_tag(_notes(), "work")
    assert {n.id for n in res} == {"1", "3"}


def test_search_tag_no_match():
    assert search.search_tag(_notes(), "nope") == []


def test_all_tags_counts_and_sorting():
    result = search.all_tags(_notes())
    # work:2, personal:1, x:1 -> work first; personal/x tie count 1 sorted by name asc: personal then x
    assert list(result.keys()) == ["work", "personal", "x"] or list(result.keys()) == ["work", "personal", "x"]
    assert result["work"] == 2
    assert result["personal"] == 1
    assert result["x"] == 1


def test_all_tags_empty_store():
    assert search.all_tags([]) == {}
