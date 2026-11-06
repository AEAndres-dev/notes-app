"""CLI entry point."""

import argparse
import sys

from . import storage, search


DATA_PATH = "data/notes.json"


def _fmt_tags(tags):
    return ", ".join(tags)


def _print_note(note):
    print("%s | %s | %s" % (note.id, note.title, _fmt_tags(note.tags)))


def cmd_add(args):
    tags = []
    if getattr(args, "tags", None):
        tags = [t.strip() for t in args.tags.split(",") if t.strip()]
    note = storage.add_note(args.title, args.body, tags, path=DATA_PATH)
    print("Added note %s" % note.id)
    return 0


def cmd_list(args):
    notes = storage.load_notes(DATA_PATH)
    if not notes:
        print("No notes found")
        return 0
    for note in notes:
        _print_note(note)
    return 0


def cmd_search(args):
    notes = storage.load_notes(DATA_PATH)
    if getattr(args, "tag", None) is not None:
        matches = search.search_tag(notes, args.tag)
    else:
        query = args.query if getattr(args, "query", None) is not None else ""
        matches = search.search_text(notes, query)
    for note in matches:
        _print_note(note)
    return 0


def cmd_tags(args):
    notes = storage.load_notes(DATA_PATH)
    for tag, count in search.all_tags(notes).items():
        print("%s: %s" % (tag, count))
    return 0


def build_parser():
    parser = argparse.ArgumentParser(prog="notes", description="Simple notes app")
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add", help="Add a note")
    p_add.add_argument("title")
    p_add.add_argument("body")
    p_add.add_argument("--tags", default=None)
    p_add.set_defaults(func=cmd_add)

    p_list = sub.add_parser("list", help="List notes")
    p_list.set_defaults(func=cmd_list)

    p_search = sub.add_parser("search", help="Search notes")
    p_search.add_argument("query", nargs="?")
    p_search.add_argument("--tag", default=None)
    p_search.set_defaults(func=cmd_search)

    p_tags = sub.add_parser("tags", help="List tags")
    p_tags.set_defaults(func=cmd_tags)

    return parser


def main(argv=None):
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        code = exc.code
        return int(code) if code is not None else 0
    func = getattr(args, "func", None)
    if func is None:
        parser.print_help()
        return 0
    try:
        result = func(args)
        return int(result) if result is not None else 0
    except Exception as exc:  # noqa: BLE001
        print("Error: %s" % exc, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
