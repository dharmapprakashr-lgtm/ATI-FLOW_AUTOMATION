"""Requester Device page object.

Encapsulates all CRUD interactions with the Requester Device tab inside
Execution Source Config. The ``AdminDashboardPage`` (admin_navigation.py)
still owns navigation to the tab; this class takes over once the tab is
active.
"""

import re

from playwright.sync_api import expect


class RequesterDevicePage:
    """Interactions with the Requester Device tab in Execution Source Config."""

    def __init__(self, page):
        self.page = page

    # ── Internal helpers ───────────────────────────────────────────────────────

    def _search_for(self, text):
        search_input = self.page.get_by_placeholder(re.compile("Search", re.IGNORECASE)).first
        if search_input.is_visible():
            search_input.fill(text)
            self.page.wait_for_timeout(1000)
        return search_input

    def _clear_search(self, search_input):
        if search_input.is_visible():
            search_input.fill("")
            self.page.wait_for_timeout(500)

    def _row_by_exact_name(self, name):
        return self.page.locator("tr").filter(has=self.page.get_by_text(name, exact=True))

    def _select_options(self, label, values):
        if not values:
            return
        field = self.page.get_by_label(label, exact=False).first
        for value in ([values] if isinstance(values, str) else values):
            field.fill(value)
            self.page.wait_for_timeout(500)
            self.page.get_by_role("option", name=value, exact=False).first.click(force=True)
            self.page.wait_for_timeout(500)
        self.page.keyboard.press("Escape")
        self.page.wait_for_timeout(500)

    def _open_add_modal(self, button_text, first_field, attempts=3):
        button = self.page.locator("button").filter(has_text=button_text)
        for attempt in range(attempts):
            button.click(force=True)
            try:
                first_field.wait_for(state="visible", timeout=4000)
                return
            except Exception:
                if attempt == attempts - 1:
                    raise

    def _open_row_editor(self, name):
        search_input = self._search_for(name)
        row = self._row_by_exact_name(name)
        if row.count() > 0:
            row.first.locator("button").first.click(force=True)
            self.page.wait_for_timeout(1000)
        return search_input, row

    def _verify_device_save(self):
        """Wait for the modal to close, raising if it doesn't."""
        try:
            self.page.locator(".MuiDialog-container").wait_for(state="hidden", timeout=1500)
        except Exception:
            self.page.keyboard.press("Escape")
            self.page.wait_for_timeout(500)
            self.page.keyboard.press("Escape")
            self.page.wait_for_timeout(1000)
            raise AssertionError("Requester device save failed: modal did not close.")

    # ── Public API ─────────────────────────────────────────────────────────────

    def add(self, name, device_id, password, bound_machines, bound_workflows, staging_areas):
        """Create a Requester device record."""
        name_field = self.page.get_by_placeholder("Requester Name")
        self._open_add_modal("ADD NEW", name_field)
        name_field.fill(name)
        self.page.get_by_placeholder("Device ID").fill(device_id)
        self.page.get_by_placeholder("Password").fill(password)
        self._select_options("Bound Machines", bound_machines)
        self._select_options("Bound Workflows", bound_workflows)
        self._select_options("Visible Staging Areas", staging_areas)
        self.page.get_by_role("button", name="SAVE").click(force=True)
        self.page.wait_for_timeout(1500)
        self._verify_device_save()

    def update(self, name, new_password, new_machines, new_workflows, new_staging):
        """Edit an existing Requester device record."""
        search_input, row = self._open_row_editor(name)
        if row.count() > 0:
            if new_password:
                self.page.get_by_placeholder(re.compile("Password")).fill(new_password)
                self.page.wait_for_timeout(500)
            self._select_options("Bound Machines", new_machines)
            self._select_options("Bound Workflows", new_workflows)
            self._select_options("Visible Staging Areas", new_staging)
            self.page.get_by_role("button", name="SAVE").click(force=True)
            self.page.wait_for_timeout(1500)
            self._verify_device_save()
        self._clear_search(search_input)

    def delete_if_exists(self, name):
        """Delete the named device if it exists. Returns True when deleted."""
        search_input = self._search_for(name)
        row = self._row_by_exact_name(name)
        if row.count() == 0:
            self._clear_search(search_input)
            return False
        row.first.locator("button").last.click(force=True)
        self.page.wait_for_timeout(500)
        self.page.get_by_role("button", name="DELETE").click(force=True)
        self.page.wait_for_timeout(1500)
        try:
            self.page.locator(".MuiDialog-container").wait_for(state="hidden", timeout=2000)
        except Exception:
            pass
        try:
            expect(row.first).not_to_be_visible(timeout=5000)
        except AssertionError:
            pass
        self._clear_search(search_input)
        return True

    def verify_exists(self, name):
        """Assert the named device row is visible in the table."""
        search_input = self._search_for(name)
        expect(self._row_by_exact_name(name).first).to_be_visible(timeout=5000)
        self._clear_search(search_input)
