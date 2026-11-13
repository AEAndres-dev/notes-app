"""Contract tests for GET /api/notes/suggest (v3.0.1 hotfix).

Frozen contract:
    GET /api/notes/suggest?q=<prefix> → 200 {"suggestions": [
        {"type": "tag" | "title", "value": "...", "highlight": "..."}]}
    - combined tag names + note titles
    - dedup case-insensitive
    - case-insensitive prefix match
    - sorted (case-insensitive)
    - capped at 10
    - matched prefix wrapped in <mark> (user-controlled content HTML-escaped)
    - missing / empty / whitespace-only q → 400 JSON error

Self-contained: spins a live NotesHandler on a free port with a scratch
store (monkeypatched server.DATA_PATH). Never touches repo data/notes.json.
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


def _request(base_url, method, path):
    req = urllib.request.Request(base_url + path, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read().decode("utf-8")
            return resp.status, raw, dict(resp.headers)
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        return exc.code, raw, dict(exc.headers)


def _json(base_url, path):
    status, raw, headers = _request(base_url, "GET", path)
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

def _json_post(base_url, path, body):
    import urllib.request
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        base_url + path,
        method="POST",
        data=data,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read().decode("utf-8")
            return resp.status, raw, dict(resp.headers)
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        return exc.code, raw, dict(exc.headers)


def _seed_store(base_url, notes):
    """Create notes via the live POST endpoint (scratch store only)."""
    for note in notes:
        _json_post(base_url, "/api/notes", note)

# ---- Contract: missing / empty / whitespace q → 400 JSON ----


def test_suggest_missing_q_400(live):
    status, payload, _ = _json(live, "/api/notes/suggest")
    assert status == 400
    assert isinstance(payload, dict)
    assert "error" in payload


def test_suggest_empty_q_400(live):
    status, payload, _ = _json(live, "/api/notes/suggest?q=")
    assert status == 400
    assert isinstance(payload, dict)
    assert "error" in payload


def test_suggest_whitespace_q_400(live):
    status, payload, _ = _json(live, "/api/notes/suggest?q=   ")
    assert status == 400
    assert isinstance(payload, dict)
    assert "error" in payload

# ---- Contract: 200 shape ----


def test_suggest_shape(live):
    _seed_store(live, [{"title": "Alpha", "body": "x", "tags": ["work"]}])
    status, payload, _ = _json(live, "/api/notes/suggest?q=a")
    assert status == 200
    assert isinstance(payload, dict)
    assert set(payload.keys()) == {"suggestions"}
    assert isinstance(payload["suggestions"], list)
    for item in payload["suggestions"]:
        assert set(item.keys()) == {"type", "value", "highlight"}
        assert item["type"] in ("tag", "title")
        assert isinstance(item["value"], str)
        assert isinstance(item["highlight"], str)


# ---- Contract: case-insensitive prefix + dedup (deterministic tie) ----


def test_suggest_case_insensitive_prefix(live):
    _seed_store(live, [{"title": "Work out", "body": "x", "tags": ["work"]}])
    for q in ("wo", "WO", "Wo", "WORK"):
        status, payload, _ = _json(live, "/api/notes/suggest?q=%s" % q)
        assert status == 200
        values = {item["value"].lower() for item in payload["suggestions"]}
        assert "work" in values
        assert "work out" in values


def test_suggest_dedup_case_insensitive(live):
    # title "Alpha" on note 1, tag "alpha" on note 2 -> dedups to one suggestion
    _seed_store(live, [{"title": "Alpha", "body": "x", "tags": []},
                       {"title": "Beta", "body": "x", "tags": ["alpha"]}])
    status, payload, _ = _json(live, "/api/notes/suggest?q=a")
    assert status == 200
    values = [item["value"] for item in payload["suggestions"]]
    assert values.count("Alpha") == 1
    assert all(v.lower() != "alpha" or v == "Alpha" for v in values)

# ---- Contract: sorted case-insensitive ----


def test_suggest_sorted(live):
    _seed_store(live, [{"title": "Delta", "body": "x"},
                       {"title": "alpha", "body": "x"},
                       {"title": "Bravo", "body": "x"}])
    status, payload, _ = _json(live, "/api/notes/suggest?q=a")
    assert status == 200
    values = [item["value"] for item in payload["suggestions"]]
    lowered = [v.lower() for v in values]
    assert lowered == sorted(lowered)


# ---- Contract: <= 10 cap ----


def test_suggest_cap_ten(live):
    for i in range(15):
        _seed_store(live, [{"title": "item %02d" % i, "body": "x",
                            "tags": ["t%02d" % i]}])
    status, payload, _ = _json(live, "/api/notes/suggest?q=item")
    assert status == 200
    assert len(payload["suggestions"]) <= 10


# ---- Contract: <mark> highlight preserves original casing ----


def test_suggest_highlight_mark(live):
    _seed_store(live, [{"title": "Grocery list", "body": "x"}])
    status, payload, _ = _json(live, "/api/notes/suggest?q=gro")
    assert status == 200
    titles = [item for item in payload["suggestions"] if item["value"] == "Grocery list"]
    assert titles, "expected 'Grocery list' suggestion"
    assert titles[0]["highlight"] == "<mark>Gro</mark>cery list"


# ---- Contract: stored-XSS escaping around <mark> ----


def test_suggest_highlight_escapes_user_content(live):
    _seed_store(live, [{"title": "A <script> B & C", "body": "x"}])
    status, payload, _ = _json(live, "/api/notes/suggest?q=a")
    assert status == 200
    items = [item for item in payload["suggestions"]
             if item["value"] == "A <script> B & C"]
    assert items, "expected the seeded title suggestion"
    highlight = items[0]["highlight"]
    assert highlight == "<mark>A</mark> &lt;script&gt; B &amp; C"
    assert "<script>" not in highlight
    assert "&amp;" in highlight
