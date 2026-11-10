"""GUI tests for the notes app v2 web frontend using Playwright.

Requires: pip install playwright && python -m playwright install chromium

Run the server first:
    python -m src.server              # port 8000
    NOTES_PORT=9000 python -m src.server   # custom port

Then run:
    pytest tests/test_gui.py -v
"""

import json
import os
import urllib.request

import pytest
from playwright.sync_api import sync_playwright, expect

BASE_URL = "http://127.0.0.1:8000"
DATA_PATH = "data/notes.json"


@pytest.fixture(scope="session")
def browser():
    """Launch a headless Chromium browser for the GUI test session."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()


@pytest.fixture
def page(browser):
    """Create a new page for each test, navigating to the app home."""
    page = browser.new_page()
    page.goto(BASE_URL)
    yield page
    page.close()


@pytest.fixture(autouse=True)
def clean_store():
    """Ensure a fresh notes store before each test."""
    if os.path.exists(DATA_PATH):
        os.remove(DATA_PATH)
    yield
    if os.path.exists(DATA_PATH):
        os.remove(DATA_PATH)


def _api_post(path, payload):
    """Helper to POST JSON to the REST API."""
    req = urllib.request.Request(
        BASE_URL + path,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())


# ---- GUI journey tests ----


def test_home_page_loads(page):
    """The home page should load with the Notes heading and empty state."""
    expect(page.locator("h1")).to_have_text("Notes")
    expect(page.locator("#emptyState")).to_be_visible()
    expect(page.locator("#notesList")).to_be_hidden()


def test_add_note(page):
    """Adding a note via the form should create a note card."""
    page.fill("#titleInput", "Buy milk")
    page.fill("#bodyInput", "From the grocery store")
    page.fill("#tagsInput", "shopping, personal")
    page.click("button.btn-primary")

    # Form should reset
    expect(page.locator("#titleInput")).to_have_value("")
    expect(page.locator("#bodyInput")).to_have_value("")

    # Note card should appear
    expect(page.locator("#emptyState")).to_be_hidden()
    expect(page.locator("#notesList")).to_be_visible()
    expect(page.locator(".note-card")).to_have_count(1)
    expect(page.locator(".note-title")).to_have_text("Buy milk")


def test_list_notes(page):
    """Multiple notes should be listed as cards."""
    # Add two notes via API for speed
    _api_post("/api/notes", {"title": "Note A", "body": "Body A"})
    _api_post("/api/notes", {"title": "Note B", "body": "Body B"})

    page.reload()
    expect(page.locator("#emptyState")).to_be_hidden()
    expect(page.locator(".note-card")).to_have_count(2)
    titles = page.locator(".note-title").all_text_contents()
    assert "Note A" in titles
    assert "Note B" in titles


def test_search_filters_notes(page):
    """Typing in the search box should filter notes (debounced 300ms)."""
    _api_post("/api/notes", {"title": "Buy milk", "body": "From the grocery store"})
    _api_post("/api/notes", {"title": "Finish report", "body": "Work task"})

    page.reload()
    expect(page.locator(".note-card")).to_have_count(2)

    # Search for "milk"
    page.fill("#searchInput", "milk")
    page.wait_for_timeout(350)  # wait for debounce
    expect(page.locator(".note-card")).to_have_count(1)
    expect(page.locator(".note-title")).to_have_text("Buy milk")

    # Clear search
    page.fill("#searchInput", "")
    page.wait_for_timeout(350)
    expect(page.locator(".note-card")).to_have_count(2)


def test_tag_filter(page):
    """Filtering by tag should show only matching notes."""
    _api_post(
        "/api/notes",
        {"title": "Work task", "body": "Finish report", "tags": "work"},
    )
    _api_post(
        "/api/notes",
        {"title": "Buy milk", "body": "Grocery", "tags": "shopping"},
    )

    page.reload()
    expect(page.locator(".note-card")).to_have_count(2)

    # Filter by "work" tag
    page.fill("#tagFilter", "work")
    page.wait_for_timeout(350)
    expect(page.locator(".note-card")).to_have_count(1)
    expect(page.locator(".note-title")).to_have_text("Work task")

    # Clear filter
    page.fill("#tagFilter", "")
    page.wait_for_timeout(350)
    expect(page.locator(".note-card")).to_have_count(2)


def test_edit_note(page):
    """Clicking Edit, changing fields, and Save should update the card."""
    note = _api_post("/api/notes", {"title": "Original", "body": "Original body"})

    page.reload()
    expect(page.locator(".note-title")).to_have_text("Original")

    # Click Edit
    page.click("button.btn-edit")

    # Edit form should appear
    edit_title = page.locator(".edit-title")
    edit_body = page.locator(".edit-body")
    expect(edit_title).to_have_value("Original")
    expect(edit_body).to_have_value("Original body")
    expect(page.locator(".note-edit")).to_be_visible()

    # Change title
    edit_title.fill("Updated title")
    page.click("button.btn-save")

    # Card should reflect the update
    expect(page.locator(".note-title")).to_have_text("Updated title")
    expect(page.locator(".note-edit")).to_be_hidden()


def test_delete_note(page):
    """Clicking Delete and confirming should remove the card."""
    note = _api_post("/api/notes", {"title": "To delete", "body": "Will be removed"})

    page.reload()
    expect(page.locator(".note-card")).to_have_count(1)

    # Register dialog handler BEFORE clicking Delete
    page.on("dialog", lambda dialog: dialog.accept())

    # Click Delete
    page.click("button.btn-delete")

    # Card should be removed, empty state shown
    expect(page.locator("#emptyState")).to_be_visible()
    expect(page.locator("#notesList")).to_be_hidden()