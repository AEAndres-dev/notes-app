"""HTTP server and REST API for the notes app (v2 web pivot).

stdlib-only wrapper over the storage/search/model layers.
Run:  python -m src.server      (port 8000, bind 127.0.0.1)
      NOTES_PORT=9000 python -m src.server
"""

import json
import os
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

from . import storage, search

DATA_PATH = "data/notes.json"
HOST = "127.0.0.1"
DEFAULT_PORT = 8000
MAX_BODY = 1 * 1024 * 1024  # 1 MB

STATIC_EXTENSIONS = {".html", ".css", ".js"}
STATIC_DIR = "static"

UUID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)


def _is_valid_uuid(value):
    return bool(UUID_RE.match(value or ""))


def _json_response(handler, status, payload):
    body = json.dumps(payload).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def _error(handler, status, message):
    _json_response(handler, status, {"error": message})


def _read_body(handler):
    """Read the request body, enforcing the 1 MB limit.

    Returns the raw bytes, or None if the body exceeds MAX_BODY.
    """
    length = handler.headers.get("Content-Length")
    if length is None:
        return b""
    try:
        length = int(length)
    except ValueError:
        return b""
    if length < 0:
        return b""
    if length > MAX_BODY:
        return None
    return handler.rfile.read(length)


def _parse_body(raw):
    """Parse raw bytes as JSON.

    Returns (data, status_code). status_code is 200 on success,
    413 if oversized, 400 if empty or malformed.
    """
    if raw is None:
        return None, 413
    if raw == b"":
        return None, 400
    try:
        return json.loads(raw.decode("utf-8")), 200
    except (ValueError, UnicodeDecodeError):
        return None, 400


def _validate_note_payload(data, partial=False):
    """Validate a create/update note payload.

    Returns (cleaned_dict, status_code). Unknown fields are ignored.
    For partial (PUT) updates, missing fields are simply omitted.
    """
    if not isinstance(data, dict):
        return None, 400

    cleaned = {}

    if "title" in data:
        title = data["title"]
        if not isinstance(title, str) or title == "":
            return None, 400
        if len(title) > 200:
            return None, 400
        cleaned["title"] = title
    elif not partial:
        return None, 400  # title required for create

    if "body" in data:
        body = data["body"]
        if not isinstance(body, str):
            return None, 400
        if len(body) > 10000:
            return None, 400
        cleaned["body"] = body
    elif not partial:
        return None, 400  # body required for create

    if "tags" in data:
        cleaned["tags"] = storage._coerce_tags(data["tags"])

    return cleaned, 200


def _load_notes_safe():
    """Load notes from the data store.

    Returns (notes, status_code). Missing store -> ([], 200).
    Corrupt store -> ([], 500).
    """
    try:
        notes = storage.load_notes(DATA_PATH)
        return notes, 200
    except ValueError:
        return [], 500


class NotesHandler(BaseHTTPRequestHandler):
    """REST + static file handler for the notes web app."""

    def log_message(self, format, *args):  # noqa: A002
        """Suppress default stderr logging."""
        return

    # ---- routing ----

    def _route(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        query = parse_qs(parsed.query, keep_blank_values=True)
        return path, query

    # ---- GET ----

    def do_GET(self):
        path, query = self._route()

        if path == "/":
            self._serve_static("index.html")
            return

        if path.startswith("/static/"):
            rel = path[len("/static/"):]
            self._serve_static(rel)
            return

        if path == "/api/notes":
            self._handle_list_notes(query)
            return

        m = re.match(r"^/api/notes/([^/]+)$", path)
        if m:
            self._handle_get_note(m.group(1))
            return

        _error(self, 404, "Not found")

    def _serve_static(self, rel):
        # Path traversal protection.
        if rel.startswith("/") or "\\" in rel or ".." in rel.split("/"):
            _error(self, 403, "Forbidden")
            return

        _, ext = os.path.splitext(rel)
        if ext.lower() not in STATIC_EXTENSIONS:
            _error(self, 403, "Forbidden")
            return

        fs_path = os.path.join(STATIC_DIR, rel)
        if not os.path.isfile(fs_path):
            _error(self, 404, "Not found")
            return

        try:
            with open(fs_path, "rb") as fh:
                content = fh.read()
        except OSError:
            _error(self, 500, "Internal server error")
            return

        content_type = {
            ".html": "text/html; charset=utf-8",
            ".css": "text/css; charset=utf-8",
            ".js": "application/javascript; charset=utf-8",
        }[ext.lower()]

        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def _handle_list_notes(self, query):
        notes, status = _load_notes_safe()
        if status == 500:
            _error(self, 500, "Malformed notes store")
            return

        tag = query.get("tag", [None])[0]
        q = query.get("q", [None])[0]

        # Case-insensitive tag filter (TRD §5.2 — divergent from CLI).
        if tag is not None:
            tag_l = tag.strip().lower()
            notes = [
                n for n in notes
                if tag_l in (t.lower() for t in (n.tags or []))
            ]

        # Case-insensitive substring text search.
        if q is not None and q != "":
            notes = search.search_text(notes, q)

        _json_response(self, 200, [n.to_dict() for n in notes])

    def _handle_get_note(self, note_id):
        if not _is_valid_uuid(note_id):
            _error(self, 400, "Invalid note id")
            return

        notes, status = _load_notes_safe()
        if status == 500:
            _error(self, 500, "Malformed notes store")
            return

        for note in notes:
            if note.id == note_id:
                _json_response(self, 200, note.to_dict())
                return
        _error(self, 404, "Note not found")

    # ---- POST ----

    def do_POST(self):
        path, _query = self._route()

        if path == "/api/notes":
            self._handle_create_note()
            return

        _error(self, 404, "Not found")

    def _handle_create_note(self):
        raw = _read_body(self)
        if raw is None:
            _error(self, 413, "Request body too large")
            return

        data, status = _parse_body(raw)
        if status != 200:
            _error(self, 400, "Malformed JSON body")
            return

        cleaned, status = _validate_note_payload(data, partial=False)
        if status != 200:
            _error(self, 400, "Validation failed")
            return

        try:
            note = storage.add_note(
                cleaned["title"],
                cleaned["body"],
                cleaned.get("tags", []),
                path=DATA_PATH,
            )
        except ValueError as exc:
            _error(self, 500, str(exc))
            return

        _json_response(self, 201, note.to_dict())

    # ---- PUT ----

    def do_PUT(self):
        path, _query = self._route()

        m = re.match(r"^/api/notes/([^/]+)$", path)
        if m:
            self._handle_update_note(m.group(1))
            return

        _error(self, 404, "Not found")

    def _handle_update_note(self, note_id):
        if not _is_valid_uuid(note_id):
            _error(self, 400, "Invalid note id")
            return

        raw = _read_body(self)
        if raw is None:
            _error(self, 413, "Request body too large")
            return

        data, status = _parse_body(raw)
        if status != 200:
            _error(self, 400, "Malformed JSON body")
            return

        cleaned, status = _validate_note_payload(data, partial=True)
        if status != 200:
            _error(self, 400, "Validation failed")
            return

        try:
            note = storage.edit_note(note_id, **cleaned, path=DATA_PATH)
        except ValueError as exc:
            _error(self, 500, str(exc))
            return

        if note is None:
            _error(self, 404, "Note not found")
            return

        _json_response(self, 200, note.to_dict())

    # ---- DELETE ----

    def do_DELETE(self):
        path, _query = self._route()

        m = re.match(r"^/api/notes/([^/]+)$", path)
        if m:
            self._handle_delete_note(m.group(1))
            return

        _error(self, 404, "Not found")

    def _handle_delete_note(self, note_id):
        if not _is_valid_uuid(note_id):
            _error(self, 400, "Invalid note id")
            return

        deleted = storage.delete_note(note_id, path=DATA_PATH)
        if not deleted:
            _error(self, 404, "Note not found")
            return

        self.send_response(204)
        self.send_header("Content-Length", "0")
        self.end_headers()


def run(host=HOST, port=DEFAULT_PORT):
    server = ThreadingHTTPServer((host, port), NotesHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def main():
    port = int(os.environ.get("NOTES_PORT", str(DEFAULT_PORT)))
    print("Serving notes on http://%s:%d" % (HOST, port))
    run(HOST, port)


if __name__ == "__main__":
    main()