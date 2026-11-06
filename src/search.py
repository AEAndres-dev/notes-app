"""Search helpers."""
from .models import Note


def search_text(notes: list[Note], query: str) -> list[Note]:
    if query is None or query == "":
        return list(notes)
    q = query.lower()
    result: list[Note] = []
    for note in notes:
        if q in (note.title or "").lower() or q in (note.body or "").lower():
            result.append(note)
    return result


def search_tag(notes: list[Note], tag: str) -> list[Note]:
    return [n for n in notes if tag in (n.tags or [])]


def all_tags(notes: list[Note]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for note in notes:
        for tag in note.tags or []:
            counts[tag] = counts.get(tag, 0) + 1
    # sort by count desc then name asc
    ordered = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return {k: v for k, v in ordered}
