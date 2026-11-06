"""Tests for CLI (AC1-AC6, AC8)."""
import json
from pathlib import Path

import pytest

from src import cli


def test_add_creates_and_persists(tmp_path, monkeypatch, capsys):
    p = tmp_path / "notes.json"
    monkeypatch.setattr(cli, "DATA_PATH", str(p))
    rc = cli.main(["add", "title", "body", "--tags", "work,shopping"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "Added note" in out
    data = json.loads(p.read_text(encoding="utf-8"))
    assert len(data) == 1
    assert data[0]["tags"] == ["work", "shopping"]


def test_list_empty_prints_no_notes(tmp_path, monkeypatch, capsys):
    p = tmp_path / "notes.json"
    monkeypatch.setattr(cli, "DATA_PATH", str(p))
    rc = cli.main(["list"])
    assert rc == 0
    assert "No notes found" in capsys.readouterr().out


def test_list_populated(tmp_path, monkeypatch, capsys):
    p = tmp_path / "notes.json"
    monkeypatch.setattr(cli, "DATA_PATH", str(p))
    cli.main(["add", "title", "body", "--tags", "work"])
    capsys.readouterr()
    rc = cli.main(["list"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "title" in out
    assert "work" in out


def test_search_text(tmp_path, monkeypatch, capsys):
    p = tmp_path / "notes.json"
    monkeypatch.setattr(cli, "DATA_PATH", str(p))
    cli.main(["add", "Hello", "world body", "--tags", "work"])
    capsys.readouterr()
    rc = cli.main(["search", "world"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "Hello" in out


def test_search_tag(tmp_path, monkeypatch, capsys):
    p = tmp_path / "notes.json"
    monkeypatch.setattr(cli, "DATA_PATH", str(p))
    cli.main(["add", "Hello", "body", "--tags", "work"])
    capsys.readouterr()
    rc = cli.main(["search", "--tag", "work"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "Hello" in out


def test_search_no_match_prints_nothing(tmp_path, monkeypatch, capsys):
    p = tmp_path / "notes.json"
    monkeypatch.setattr(cli, "DATA_PATH", str(p))
    cli.main(["add", "Hello", "world body", "--tags", "work"])
    capsys.readouterr()
    rc = cli.main(["search", "zzzz-no-such-note"])
    assert rc == 0
    out, err = capsys.readouterr()
    assert out == ""
    assert err == ""


def test_tags_output(tmp_path, monkeypatch, capsys):
    p = tmp_path / "notes.json"
    monkeypatch.setattr(cli, "DATA_PATH", str(p))
    cli.main(["add", "Hello", "body", "--tags", "work,work"])
    capsys.readouterr()
    rc = cli.main(["tags"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "work: 2" in out


def test_malformed_store_clean_exit(tmp_path, monkeypatch, capsys):
    p = tmp_path / "notes.json"
    p.write_text("{bad json", encoding="utf-8")
    monkeypatch.setattr(cli, "DATA_PATH", str(p))
    rc = cli.main(["list"])
    assert rc == 1
    captured = capsys.readouterr()
    assert "Traceback" not in captured.err
    assert "Traceback" not in captured.out
    assert captured.err.strip() != ""


def test_cli_exit_codes(tmp_path, monkeypatch):
    p = tmp_path / "notes.json"
    monkeypatch.setattr(cli, "DATA_PATH", str(p))
    assert cli.main(["add", "t", "b"]) == 0
    assert cli.main(["list"]) == 0
    # unknown subcommand -> argparse exits 2
    assert cli.main(["frobnicate"]) == 2
    # --help returns 0
    assert cli.main(["--help"]) == 0
