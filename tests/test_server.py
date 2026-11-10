"""Web layer tests for the notes app v2 REST API.

Covers TRD-v2-web §11.1 (18 cases) plus @qa-safety's additional
security/validation cases. No production code changes.
"""

import json
import socket
import threading
import time
import urllib.error
import urllib.request

import pytest

import src.server as server_mod
from src.server import ThreadingHTTPServer, NotesHandler


def _free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


class LiveServer:
    """Starts NotesHandler on 127.0.0.1:<port> in a daemon thread."""

    def __init__(self, port=None):
        self.port = port or _free_port()
        self.httpd = ThreadingHTTPServer(("127.0.0.1", self.port), NotesHandler)
        self.thread = None

    def __enter__(self):
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()
        deadline = time.time() + 5
        while time.time() < deadline:
            try:
                s = socket.create_connection(("127.0.0.1", self.port), timeout=0.2)
                s.close()
                break
            except OSError:
                time.sleep(0.05)
        return "http://127.0.0.1:%d" % self.port

    def __exit__(self, *exc):
        try:
            self.httpd.shutdown()
        finally:
            self.httpd.server_close()
        if self.thread:
            self.thread.join(timeout=3)


def _request(base_url, method, path, body=None):
    data = json.dumps(body).encode("utf-8") if body is not None else None
    headers = {"Content-Type": "application/json"} if data else {}
    req = urllib.request.Request(base_url + path, method=method, data=data, headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read().decode("utf-8")
            return resp.status, raw, dict(resp.headers)
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        return exc.code, raw, dict(exc.headers)


def _json(base_url, method, path, body=None):
    status, raw, headers = _request(base_url, method, path, body)
    try:
        payload = json.loads(raw) if raw else None
    except ValueError:
        payload = None
    return status, payload, headers


@pytest.fixture
def temp_store(tmp_path, monkeypatch):
    """Point server.DATA_PATH at a temp JSON file (fresh per test)."""
    store = tmp_path / "notes.json"
    monkeypatch.setattr(server_mod, "DATA_PATH", str(store))
    yield str(store)


@pytest.fixture
def live(temp_store):
    """A live server on a free port with a temp data store."""
    with LiveServer() as base_url:
        yield base_url


# ---- TRD §11.1 cases ----


def test_get_index(live):
    status, raw, headers = _request(live, "GET", "/")
    assert status == 200
    assert "text/html" in headers.get("Content-Type", "")
    assert "<h1>Notes</h1>" in raw


def test_get_notes_empty(live):
    status, payload, _ = _json(live, "GET", "/api/notes")
    assert status == 200
    assert payload == []


def test_get_notes_populated(live):
    _json(live, "POST", "/api/notes", {"title": "T", "body": "B"})
    status, payload, _ = _json(live, "GET", "/api/notes")
    assert status == 200
    assert len(payload) == 1
    assert payload[0]["title"] == "T"


def test_get_notes_filter_tag(live):
    _json(live, "POST", "/api/notes", {"title": "T1", "body": "B", "tags": "work"})
    _json(live, "POST", "/api/notes", {"title": "T2", "body": "B", "tags": "personal"})
    status, payload, _ = _json(live, "GET", "/api/notes?tag=work")
    assert status == 200
    assert len(payload) == 1
    assert payload[0]["title"] == "T1"


def test_get_notes_search(live):
    _json(live, "POST", "/api/notes", {"title": "Milk run", "body": "Buy milk"})
    _json(live, "POST", "/api/notes", {"title": "Work", "body": "Finish report"})
    status, payload, _ = _json(live, "GET", "/api/notes?q=milk")
    assert status == 200
    assert len(payload) == 1
    assert payload[0]["title"] == "Milk run"


def test_get_note_by_id(live):
    _, created, _ = _json(live, "POST", "/api/notes", {"title": "T", "body": "B"})
    assert created is not None and "id" in created
    status, payload, _ = _json(live, "GET", "/api/notes/%s" % created["id"])
    assert status == 200
    assert payload["id"] == created["id"]
    assert payload["title"] == "T"


def test_get_note_not_found(live):
    status, payload, _ = _json(live, "GET",
                               "/api/notes/00000000-0000-0000-0000-000000000000")
    assert status == 404
    assert "error" in payload


def test_create_note(live):
    status, payload, _ = _json(live, "POST", "/api/notes",
                               {"title": "T", "body": "B", "tags": ["a", "b"]})
    assert status == 201
    assert "id" in payload
    assert payload["title"] == "T"
    assert payload["body"] == "B"
    assert payload["tags"] == ["a", "b"]


def test_create_note_missing_title(live):
    status, payload, _ = _json(live, "POST", "/api/notes", {"body": "B"})
    assert status == 400
    assert "error" in payload


def test_create_note_tags_normalized(live):
    status, payload, _ = _json(live, "POST", "/api/notes",
                               {"title": "T", "body": "B", "tags": " a , , b "})
    assert status == 201
    assert payload["tags"] == ["a", "b"]


def test_update_note(live):
    _, created, _ = _json(live, "POST", "/api/notes", {"title": "T", "body": "B"})
    status, payload, _ = _json(live, "PUT", "/api/notes/%s" % created["id"],
                               {"title": "Updated"})
    assert status == 200
    assert payload["title"] == "Updated"
    assert payload["body"] == "B"


def test_update_note_not_found(live):
    status, payload, _ = _json(live, "PUT",
                               "/api/notes/00000000-0000-0000-0000-000000000000",
                               {"title": "T"})
    assert status == 404


def test_delete_note(live):
    _, created, _ = _json(live, "POST", "/api/notes", {"title": "T", "body": "B"})
    status, _, _ = _request(live, "DELETE", "/api/notes/%s" % created["id"])
    assert status == 204
    status, payload, _ = _json(live, "GET", "/api/notes")
    assert status == 200
    assert payload == []


def test_delete_note_not_found(live):
    status, payload, _ = _json(live, "DELETE",
                               "/api/notes/00000000-0000-0000-0000-000000000000")
    assert status == 404
    assert "error" in payload


def test_malformed_store(live, temp_store):
    with open(temp_store, "w") as fh:
        fh.write("{not valid json")
    status, payload, _ = _json(live, "GET", "/api/notes")
    assert status == 500
    assert "error" in payload


def test_static_file_serving(live):
    status, raw, headers = _request(live, "GET", "/static/style.css")
    assert status == 200
    assert "text/css" in headers.get("Content-Type", "")
    assert len(raw) > 0


def test_path_traversal_blocked(live):
    status, _, _ = _request(live, "GET", "/static/../src/models.py")
    assert status in (403, 404)


def test_bind_localhost_only():
    port = _free_port()
    httpd = ThreadingHTTPServer(("127.0.0.1", port), NotesHandler)
    try:
        host, _bound_port = httpd.socket.getsockname()
        assert host == "127.0.0.1"
    finally:
        httpd.server_close()


# ---- Additional QA cases ----


def test_malformed_json_body(live):
    req = urllib.request.Request(live + "/api/notes", method="POST",
                                 data=b"{not json",
                                 headers={"Content-Type": "application/json",
                                          "Content-Length": "9"})
    try:
        urllib.request.urlopen(req)
        assert False, "expected HTTPError"
    except urllib.error.HTTPError as exc:
        assert exc.code == 400
        body = json.loads(exc.read().decode())
        assert "error" in body


def test_create_note_missing_body(live):
    status, payload, _ = _json(live, "POST", "/api/notes", {"title": "T"})
    assert status == 400


def test_create_note_body_too_long(live):
    status, payload, _ = _json(live, "POST", "/api/notes",
                               {"title": "T", "body": "x" * 10001})
    assert status == 400


def test_create_note_title_too_long(live):
    status, payload, _ = _json(live, "POST", "/api/notes",
                               {"title": "x" * 201, "body": "B"})
    assert status == 400


def test_unknown_fields_ignored(live):
    status, payload, _ = _json(live, "POST", "/api/notes",
                               {"title": "T", "body": "B", "extra": "ignored"})
    assert status == 201
    assert "extra" not in payload


def test_create_note_empty_body(live):
    req = urllib.request.Request(live + "/api/notes", method="POST",
                                 data=b"",
                                 headers={"Content-Type": "application/json",
                                          "Content-Length": "0"})
    try:
        urllib.request.urlopen(req)
        assert False, "expected HTTPError"
    except urllib.error.HTTPError as exc:
        assert exc.code == 400


def test_update_note_invalid_uuid(live):
    status, payload, _ = _json(live, "PUT", "/api/notes/not-a-uuid", {"title": "T"})
    assert status == 400


def test_delete_note_invalid_uuid(live):
    status, payload, _ = _json(live, "DELETE", "/api/notes/not-a-uuid")
    assert status == 400


def test_post_wrong_path(live):
    status, _, _ = _request(live, "POST", "/api/nope", {"title": "T"})
    assert status == 404


def test_put_wrong_path(live):
    status, _, _ = _request(live, "PUT", "/api/nope", {"title": "T"})
    assert status == 404


def test_delete_wrong_path(live):
    status, _, _ = _request(live, "DELETE", "/api/nope")
    assert status == 404


def test_oversized_body_rejected_413(live):
    big_body = "x" * (1024 * 1024 + 1)
    req = urllib.request.Request(live + "/api/notes", method="POST",
                                 data=json.dumps({"title": "T", "body": big_body}).encode(),
                                 headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req)
        assert False, "expected HTTPError"
    except urllib.error.HTTPError as exc:
        assert exc.code == 413


def test_disallowed_static_extension(live):
    status, _, _ = _request(live, "GET", "/static/secret.exe")
    assert status in (403, 404)


def test_server_starts_and_binds():
    port = _free_port()
    httpd = ThreadingHTTPServer(("127.0.0.1", port), NotesHandler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        status, _, _ = _request("http://127.0.0.1:%d" % port, "GET", "/api/notes")
        assert status == 200
    finally:
        httpd.shutdown()
        httpd.server_close()
        thread.join(timeout=3)