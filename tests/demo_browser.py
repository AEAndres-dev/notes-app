"""Demonstration script: Playwright driving a VISIBLE browser with cursor behavior.

Run:  python tests/demo_browser.py

This opens a real Chromium window (headed mode) with slow motion so you can
watch the cursor click, type, and interact with the notes app GUI.
"""

import json
import os
import sys
import time
import urllib.request

from playwright.sync_api import sync_playwright

BASE_URL = "http://127.0.0.1:8000"
DATA_PATH = "data/notes.json"
SLOW_MO = 800  # milliseconds between actions — slow enough to see cursor


def api_post(path, payload):
    req = urllib.request.Request(
        BASE_URL + path,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())


def main():
    # Ensure a clean store
    if os.path.exists(DATA_PATH):
        os.remove(DATA_PATH)

    # Seed a couple of notes via API so we have something to filter/edit/delete
    api_post("/api/notes", {"title": "Buy milk", "body": "From the grocery store", "tags": "shopping"})
    api_post("/api/notes", {"title": "Finish report", "body": "Work task", "tags": "work"})

    with sync_playwright() as p:
        # headless=False = VISIBLE browser window
        browser = p.chromium.launch(headless=False, slow_mo=SLOW_MO)
        page = browser.new_page()
        page.set_viewport_size({"width": 900, "height": 700})

        print("=" * 60)
        print("BROWSER OPEN — watching cursor behavior...")
        print("=" * 60)

        # 1. Navigate to the app
        print("\n[1] Navigating to http://127.0.0.1:8000")
        page.goto(BASE_URL)
        page.wait_for_timeout(1000)

        # 2. Take a screenshot of the empty state
        page.screenshot(path="tests/demo_01_empty_state.png")
        print("    -> Screenshot: demo_01_empty_state.png")

        # 3. Click the title input and type
        print("\n[2] Clicking title input and typing 'Demo Note'")
        page.click("#titleInput")
        page.wait_for_timeout(300)
        page.fill("#titleInput", "Demo Note")
        page.wait_for_timeout(500)

        # 4. Type in body
        print("\n[3] Clicking body input and typing 'Hello from Playwright'")
        page.click("#bodyInput")
        page.wait_for_timeout(300)
        page.fill("#bodyInput", "Hello from Playwright")
        page.wait_for_timeout(500)

        # 5. Type tags
        print("\n[4] Clicking tags input and typing 'demo, test'")
        page.click("#tagsInput")
        page.wait_for_timeout(300)
        page.fill("#tagsInput", "demo, test")
        page.wait_for_timeout(500)

        # 6. Click Add Note button
        print("\n[5] Clicking 'Add Note' button")
        page.click("button.btn-primary")
        page.wait_for_timeout(1000)

        page.screenshot(path="tests/demo_02_after_add.png")
        print("    -> Screenshot: demo_02_after_add.png")

        # 7. Click search box and type
        print("\n[6] Clicking search box and typing 'Demo'")
        page.click("#searchInput")
        page.wait_for_timeout(300)
        page.fill("#searchInput", "Demo")
        page.wait_for_timeout(1000)  # wait for debounce

        page.screenshot(path="tests/demo_03_search.png")
        print("    -> Screenshot: demo_03_search.png")

        # 8. Clear search
        print("\n[7] Clearing search box")
        page.fill("#searchInput", "")
        page.wait_for_timeout(500)

        # 9. Click tag filter and type
        print("\n[8] Clicking tag filter and typing 'demo'")
        page.click("#tagFilter")
        page.wait_for_timeout(300)
        page.fill("#tagFilter", "demo")
        page.wait_for_timeout(1000)

        page.screenshot(path="tests/demo_04_tag_filter.png")
        print("    -> Screenshot: demo_04_tag_filter.png")

        # 10. Click Edit button
        print("\n[9] Clicking 'Edit' button on the note card")
        page.click("button.btn-edit")
        page.wait_for_timeout(1000)

        page.screenshot(path="tests/demo_05_edit_open.png")
        print("    -> Screenshot: demo_05_edit_open.png")

        # 11. Change title in edit form
        print("\n[10] Changing title to 'Updated Demo Note'")
        page.fill(".edit-title", "Updated Demo Note")
        page.wait_for_timeout(500)

        # 12. Click Save
        print("\n[11] Clicking 'Save' button")
        page.click("button.btn-save")
        page.wait_for_timeout(1000)

        page.screenshot(path="tests/demo_06_after_save.png")
        print("    -> Screenshot: demo_06_after_save.png")

        # 13. Click Delete button
        print("\n[12] Clicking 'Delete' button")
        page.click("button.btn-delete")
        page.wait_for_timeout(500)

        # Accept the confirmation dialog
        page.on("dialog", lambda dialog: dialog.accept())
        page.wait_for_timeout(1000)

        page.screenshot(path="tests/demo_07_after_delete.png")
        print("    -> Screenshot: demo_07_after_delete.png")

        print("\n" + "=" * 60)
        print("DEMO COMPLETE — browser window still open for 5 seconds...")
        print("=" * 60)
        page.wait_for_timeout(5000)

        browser.close()

    print("\nBrowser closed. Demo screenshots saved in tests/demo_*.png")


if __name__ == "__main__":
    main()