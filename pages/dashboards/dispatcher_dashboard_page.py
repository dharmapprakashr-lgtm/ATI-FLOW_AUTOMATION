"""Dispatcher dashboard - the Requests queue at ``/approval`` (manual test plan step 6).

Locators verified live against the running app (first 2026-08-21, extended
2026-08-28). The screen the dispatcher device lands on after login is
``/approval`` - a "Requests" table with three tabs (Pending / Dispatched /
All), a station switcher in the sidebar, a sort control, a search box and a
custom pagination footer.

Unlike the requester wizard's emotion-hash-only DOM, this screen exposes
**stable ``id`` attributes** on nearly everything:

    #operator-sidebar-dispatch-select        station switcher (MUI Select)
    #operator-sidebar-nav-item-approval       "Requests" nav item
    #operator-sidebar-notif-row               Notifications row
    #approvals-page-breadcrumb-station         breadcrumb "<station>"
    #approvals-page-breadcrumb-page            breadcrumb "Requests"
    #approvals-page-search-input               search box ("Search requests...")
    #approvals-request-grid-row-<ID>           one table row
    #approvals-row-request-id-<ID>             ID No. cell
    #approvals-row-material-name-<ID>-0        material/SKU code cell
    #approvals-request-grid-status-cell-<ID>   Status cell
    #approvals-dispatch-decision-cell-<ID>     Decision cell (Pending rows only)
    #approvals-dispatch-label-<ID>              "Dispatch" text inside it
    #approvals-request-grid-pagination-range    "1-3 of 3"
    #approvals-request-grid-pagination-prev/-next

This page object deliberately does **not** expose a "click Dispatch" action.
The Pending queue is real production data - other requesters' in-flight
material requests, not something this suite created - and dispatching one has
a physical side effect (the bound Fleet Manager assigns and moves a real
AMR). Automated tests must never click Dispatch on a row they did not
themselves create; see the module docstring in
``tests/ui/dispatcher/test_12_dispatch_action_moves_request_to_dispatched.py``.

Behaviour confirmed live 2026-08-28:

- The search box matches the **Request Details / material-code** column, not
  the "ID No." column. A bare numeric ID search returns the empty state.
- Row "ID No." values increment with request-creation time, so sort order
  (Newest / Oldest First) is equivalent to numeric ID direction.
- Clicking a row does **not** expand a detail panel - every field is already
  shown inline; the per-row ``#approvals-row-*`` ids are the "detail".
- The "All" tab is a superset of every status (Pending + Dispatched +
  Cancelled + ...), so its count is not simply Pending + Dispatched.
"""

import re
from urllib.parse import parse_qs, urlsplit

from playwright.sync_api import expect


class DispatcherHomePage:
    def __init__(self, page):
        self.page = page

        # ── Sidebar ──────────────────────────────────────────────────────────
        # Stable id from the sidebar shell - same pattern as
        # RequesterHomePage's #operator-sidebar-machine-select.
        self.bound_station_select = page.locator("#operator-sidebar-dispatch-select")
        self.station_select = self.bound_station_select  # readable alias
        self.requests_nav = page.locator("#operator-sidebar-nav-item-approval")
        self.staging_area_nav = page.locator("#operator-sidebar-nav-item-stagingArea")
        self.notif_row = page.locator("#operator-sidebar-notif-row")
        self.profile_name = page.locator("#operator-sidebar-profile-name")
        self.profile_role = page.locator("#operator-sidebar-profile-role")

        # ── Breadcrumb ───────────────────────────────────────────────────────
        self.breadcrumb = page.locator("#approvals-page-breadcrumb")
        self.breadcrumb_station = page.locator("#approvals-page-breadcrumb-station")
        self.breadcrumb_page = page.locator("#approvals-page-breadcrumb-page")

        # ── Tabs ─────────────────────────────────────────────────────────────
        # Real DOM text is title-case ("Pending"); MUI renders it visually
        # uppercase via CSS text-transform only. Role + accessible name is what
        # MUI's Tabs component exposes and is robust to that styling changing.
        self.pending_tab = page.get_by_role("tab", name="Pending")
        self.dispatched_tab = page.get_by_role("tab", name="Dispatched")
        self.all_tab = page.get_by_role("tab", name="All")

        # ── Toolbar ──────────────────────────────────────────────────────────
        self.search_input = page.locator("#approvals-page-search-input")
        # The sort control is a plain <button> whose label is the *current*
        # state - "Newest First" or "Oldest First". Clicking it opens a small
        # menu with the two options as plain text nodes.
        self.sort_button = page.get_by_role("button").filter(has_text="First")

        # ── Table + pagination ───────────────────────────────────────────────
        self.request_rows = page.locator("tbody tr")
        self.pagination_range = page.locator("#approvals-request-grid-pagination-range")
        self.pagination_prev = page.locator("#approvals-request-grid-pagination-prev")
        self.pagination_next = page.locator("#approvals-request-grid-pagination-next")
        self.rows_per_page_select = page.locator("#approvals-request-grid-pagination select")

    # ── Sidebar / station ────────────────────────────────────────────────────

    def bound_station_text(self):
        """Currently selected value in the sidebar "Station" dropdown."""
        return self.bound_station_select.inner_text().strip()

    # Backwards-compatible name used by older callers.
    current_station = bound_station_text

    def _station_options(self):
        """The <li role=option> nodes in the open MUI Select popup only.

        Scoped through the popup's listbox so it can't pick up the native
        rows-per-page <select>'s <option> elements, which also carry an
        implicit ``option`` role.
        """
        return self.page.locator(
            "ul[role='listbox'] li[role='option'], .MuiMenu-list li[role='option']"
        )

    def open_station_dropdown(self):
        """Open the station switcher and return the option labels it offers."""
        self.bound_station_select.click()
        self.page.wait_for_timeout(600)
        options = self._station_options()
        options.first.wait_for(state="visible", timeout=5000)
        return [o.strip() for o in options.all_text_contents() if o.strip()]

    def close_dropdown(self):
        self.page.keyboard.press("Escape")
        self.page.wait_for_timeout(300)

    def select_station(self, name):
        """Switch the bound-station scope to ``name`` and wait for the reload."""
        self.bound_station_select.click()
        self.page.wait_for_timeout(400)
        self._station_options().filter(has_text=re.compile(rf"^{re.escape(name)}$")).first.click()
        self.page.wait_for_timeout(1500)

    # ── Breadcrumb ───────────────────────────────────────────────────────────

    def breadcrumb_text(self):
        """"<station> Requests" - the two crumbs joined by a space."""
        return " ".join(self.breadcrumb.inner_text().split())

    # ── Tabs ─────────────────────────────────────────────────────────────────

    def active_tab(self):
        """Lower-cased label of the currently selected tab ("pending" etc.).

        ``inner_text`` reflects the CSS ``text-transform: uppercase`` so the
        raw value is "PENDING"; callers compare case-insensitively.
        """
        tab = self.page.locator("[role='tab'][aria-selected='true']")
        return tab.inner_text().strip().lower() if tab.count() else ""

    def select_tab(self, name):
        """name: "Pending" | "Dispatched" | "All"."""
        tab = self.page.get_by_role("tab", name=name, exact=True)
        if self.active_tab() == name.lower():
            return
        if name.lower() == "all":
            # The initial 20-record response is followed by the All-tab fetch.
            # Reading the footer before this finishes can falsely report the
            # second page as the last page (20 total becomes 100 total).
            with self.page.expect_response(
                lambda response: (
                    urlsplit(response.url).path.endswith("/requests_by_pickup_stations/")
                    and parse_qs(urlsplit(response.url).query).get("page_size") == ["100"]
                ),
                timeout=15000,
            ) as loaded:
                tab.click()
            response = loaded.value
            response.finished()
            assert response.ok, f"Dispatcher All requests failed: HTTP {response.status}"
        else:
            tab.click()
        expect(tab).to_have_attribute("aria-selected", "true")
        self.page.wait_for_timeout(1200)

    # ── Rows ─────────────────────────────────────────────────────────────────

    def row_ids(self):
        """Numeric "ID No." for every real row currently shown (empty-state
        placeholder row excluded)."""
        ids = []
        for text in self.page.locator("tbody tr td:first-child").all_text_contents():
            match = re.search(r"\d+", text)
            if match and text.strip().isdigit():
                ids.append(int(match.group(0)))
        return ids

    def row_count(self):
        """Number of real data rows (0 when the empty state is showing)."""
        return len(self.row_ids())

    def all_row_statuses(self):
        """Status-column text for every real row currently shown."""
        out = []
        for cell in self.page.locator("tbody tr td:nth-child(4)").all_text_contents():
            if cell.strip():
                out.append(cell.strip())
        return out

    def row_status(self, request_id):
        return self.page.locator(f"#approvals-request-grid-status-cell-{request_id}").inner_text().strip()

    def row_material(self, request_id):
        return self.page.locator(f"#approvals-row-material-name-{request_id}-0").inner_text().strip()

    def row_texts(self):
        """Full text of every currently-visible row."""
        return [self.request_rows.nth(i).inner_text() for i in range(self.request_rows.count())]

    def first_row_material_code(self):
        """Material/SKU code shown in the first data row, or None when empty."""
        ids = self.row_ids()
        return self.row_material(ids[0]) if ids else None

    def is_empty_state(self):
        """True when the table is showing its "No ... requests found." row."""
        body = self.page.locator("tbody").inner_text().lower()
        return "requests found" in body or "no pending" in body

    # ── Decision column (read-only - never clicked) ──────────────────────────

    def has_dispatch_action(self, request_id):
        """True when a Pending row still offers an actionable "Dispatch"
        control in its Decision column. Does not click it."""
        cell = self.page.locator(f"#approvals-dispatch-decision-cell-{request_id}")
        if not cell.count():
            return False
        label = self.page.locator(f"#approvals-dispatch-label-{request_id}")
        return label.count() > 0 and label.inner_text().strip().lower() == "dispatch"

    def decision_cell_text(self, request_id):
        cell = self.page.locator(f"#approvals-dispatch-decision-cell-{request_id}")
        return cell.inner_text().strip() if cell.count() else ""

    # ── Search ───────────────────────────────────────────────────────────────

    def search(self, text):
        self.search_input.fill(text)
        self.page.wait_for_timeout(1000)

    def clear_search(self):
        self.search_input.fill("")
        self.page.wait_for_timeout(800)

    # ── Sort ─────────────────────────────────────────────────────────────────

    def current_sort(self):
        """"Newest First" or "Oldest First" - whichever the button now reads."""
        return self.sort_button.first.inner_text().strip()

    def set_sort(self, label):
        """label: "Newest First" | "Oldest First". No-op if already set."""
        if self.current_sort().lower() == label.lower():
            return
        self.sort_button.first.click()
        self.page.wait_for_timeout(500)
        # When the menu is open the label text exists twice (button + option);
        # the option is the later match.
        self.page.get_by_text(label, exact=True).last.click()
        self.page.wait_for_timeout(1400)

    # ── Pagination ───────────────────────────────────────────────────────────

    def pagination_range_text(self):
        """e.g. "1-3 of 3" (the app uses an en-dash)."""
        return self.pagination_range.inner_text().strip()

    def pagination_total(self):
        """The "z" in "x-y of z"."""
        match = re.search(r"of\s+(\d+)", self.pagination_range_text())
        return int(match.group(1)) if match else None

    def set_rows_per_page(self, value):
        self.rows_per_page_select.select_option(str(value))
        self.page.wait_for_timeout(1200)

    def prev_disabled(self):
        return self.pagination_prev.is_disabled()

    def next_disabled(self):
        return self.pagination_next.is_disabled()

    # ── Notifications ────────────────────────────────────────────────────────

    def open_notifications(self):
        self.notif_row.click()
        self.page.wait_for_timeout(1000)

    def notifications_panel(self):
        return self.page.locator(".MuiDrawer-paper, .MuiPopover-paper").first

    def notifications_panel_text(self):
        return self.notifications_panel().inner_text()

    def close_notifications(self):
        """Dismiss the notifications drawer (a modal that otherwise keeps
        intercepting clicks on the sidebar behind it)."""
        backdrop = self.page.locator(".MuiBackdrop-root").first
        if backdrop.count() and backdrop.is_visible():
            backdrop.click(force=True)
        else:
            self.page.keyboard.press("Escape")
        self.page.locator(".MuiDrawer-modal, .MuiBackdrop-root").first.wait_for(
            state="hidden", timeout=5000
        )
        self.page.wait_for_timeout(300)

    # ── Legacy read-only helper (kept for existing callers) ───────────────────

    def pending_requests_awaiting_dispatch(self):
        """Read-only: full row text for every row currently in the Pending
        queue. Does not click anything."""
        self.pending_tab.click(force=True)
        self.page.wait_for_timeout(1000)
        return [row.strip() for row in self.request_rows.all_text_contents()]
