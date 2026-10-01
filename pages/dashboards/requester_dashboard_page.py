"""Requester dashboard - the "Make New Request" flow (manual test plan step 5).

Locators verified live against the running app (2026-08-21): the old stub
(``h1.welcome-requester``) matched nothing real. The actual shell shows the
device's bound Machine and Workflow in the top sidebar, a "Request History"
table with five status tabs, and a "Make New Request" button that opens a
3-step wizard (Request Material -> Request Summary -> Confirmation).

Request Material search is scoped to the device's bound Machine/Workflow and
only returns a SKU that has real, physical WIP inventory behind it - a
throwaway admin-created material has none, so ``search_material`` legitimately
returns zero options against this suite's own test data. See
tests/ui/requester/test_requester_dashboard.py for how callers are expected to
handle that.

Sub-SKU selection flow re-verified live (2026-08-26) against a real SKU with
real stock (``DGT15A0666-01`` -> sub-SKU ``DTE15A0666``, 13 Available):

- A dropdown option is an MUI ``MenuItem`` (``role="menuitem"``), not
  ``role="option"`` as originally guessed - ``search_material``'s old
  ``li[role='option']`` selector matched nothing real.
- Each Sub-SKU row is a plain ``div`` (no table, no ``data-testid``), holding
  the code, description, "N Available" text, a disabled "-" button, an
  "Add Items" placeholder, and a "+" button - in that DOM order. All of MUI's
  own classes on this page are emotion-generated (``css-xxxxx``) and change
  across builds, so every locator here is structural/role-based instead.
- Clicking "+" replaces the "Add Items" placeholder with the running count and
  enables both "-" and "+"; the footer switches from "Please add items to
  proceed" to "N Units of <code> added" and "Next" becomes enabled.
"""

import re


class RequesterHomePage:
    def __init__(self, page):
        self.page = page

        # Stable ids from the sidebar shell - confirmed live (2026-08-21).
        self.bound_machine_select = page.locator("#operator-sidebar-machine-select")
        self.bound_workflow_select = page.locator("#operator-sidebar-workflow-select")
        self.request_history_nav = page.locator("#operator-sidebar-nav-item-requesthistory")
        self.staging_area_nav = page.locator("#operator-sidebar-nav-item-stagingArea")

        self.requested_tab = page.get_by_text("Requested", exact=True).first
        self.in_progress_tab = page.get_by_text("In Progress", exact=True).first
        self.completed_tab = page.get_by_text("Completed", exact=True).first
        self.cancelled_tab = page.get_by_text("Cancelled", exact=True).first
        self.all_tab = page.get_by_text("All", exact=True).first

        self.make_new_request_btn = page.get_by_text("Make New Request", exact=False).first

        # Wizard (open after make_new_request_btn is clicked)
        self.sku_search_input = page.get_by_placeholder("Search by material code...")
        self.step_request_material = page.get_by_text("Request Material", exact=True)
        self.step_request_summary = page.get_by_text("Request Summary", exact=True)
        self.step_confirmation = page.get_by_text("Confirmation", exact=True)
        self.next_btn = page.get_by_role("button", name="Next")
        self.back_btn = page.get_by_role("button", name="Back")
        self.confirm_btn = page.get_by_role("button", name="Confirm", exact=False)
        self.footer_summary = page.get_by_text("Units of", exact=False).first
        self.empty_items_message = page.get_by_text("Please add items to proceed", exact=True)

        # Step 3 - Confirmation screen (confirmed live 2026-08-26 from screenshot).
        # The page renders a teal checkmark circle, a heading, a sub-line and a
        # Summary accordion with a Materials sub-heading and one row per item.
        self.confirmation_heading = page.get_by_text("Request confirmed!", exact=True)
        self.confirmation_amr_text = page.get_by_text(
            "AMR will be assigned shortly to fulfill your request", exact=True
        )
        self.confirmation_summary_heading = page.get_by_text("Summary", exact=True).first
        self.confirmation_materials_heading = page.get_by_text("Materials", exact=True).first
        self.home_btn = page.get_by_role("button", name="Home", exact=False)

        # Staging Area page - confirmed live 2026-08-26. Unlike the wizard,
        # this page uses real stable ids, not just structural markup.
        self.staging_search_input = page.locator("#staging-area-search-input")
        self.staging_fleet_select = page.locator("#staging-area-fleet-select")
        self.staging_card_grid = page.locator("#staging-area-list-admin-card-grid")

        # Request History landing page (default after login) - confirmed live
        # 2026-08-26. The sort control is a plain button + plain divs (no
        # MUI Select, no ARIA role), always reading either "Newest First" or
        # "Oldest First" - "First" is unique to it on this page.
        self.history_sort_button = page.get_by_role("button").filter(has_text="First")
        self.history_search_input = page.get_by_placeholder("Search component ID...")

    def bound_machine_text(self):
        """Currently selected value in the sidebar "Machine" dropdown."""
        return self.bound_machine_select.inner_text()

    def bound_workflow_text(self):
        """Currently selected value in the sidebar "Workflow" dropdown."""
        return self.bound_workflow_select.inner_text()

    def open_make_new_request(self):
        self.make_new_request_btn.click()
        self.sku_search_input.wait_for(state="visible", timeout=10000)

    def search_material(self, code):
        """Type a material code into the SKU search and return the option texts offered.

        Empty list is a legitimate result: it means no material code matching
        ``code`` currently has available stock for this device's bound
        Machine/Workflow, not that the search itself is broken - so a bounded
        poll (not a hard failure) is used to find out which case this is.
        """
        self.sku_search_input.fill(code)
        options = self.page.get_by_role("menuitem")
        try:
            options.first.wait_for(state="visible", timeout=5000)
        except Exception:
            pass
        return [o.strip() for o in options.all_text_contents() if o.strip()]

    def select_sku(self, code):
        """Search for ``code`` and click the matching dropdown option.

        Loads that SKU's Sub-SKU rows below the search field.
        """
        self.search_material(code)
        self.page.get_by_role("menuitem", name=code, exact=False).first.click()
        self.page.wait_for_timeout(500)

    def _sub_sku_row(self, sub_sku_code):
        """The Sub-SKU row containing ``sub_sku_code`` (e.g. "DTE15A0666").

        Rows are plain ``div``s with no ``data-testid``; ``.last`` picks the
        innermost element matching both filters, since an ancestor container
        also contains this text.
        """
        return (
            self.page.locator("div")
            .filter(has_text=sub_sku_code)
            .filter(has_text="Available")
            .last
        )

    def sub_sku_row_count(self):
        """Number of Sub-SKU rows currently rendered for the selected SKU.

        Every untouched row shows the "Add Items" placeholder exactly once,
        so this must be read before any "+" click replaces that placeholder
        with a running count on the row(s) touched.
        """
        return self.page.get_by_text("Add Items", exact=True).count()

    def sub_sku_row_text(self, sub_sku_code):
        """Full text of a Sub-SKU row (code, description, Available, controls)."""
        return self._sub_sku_row(sub_sku_code).inner_text()

    def sub_sku_available_text(self, sub_sku_code):
        """The "N Available" text shown on a Sub-SKU row."""
        return self._sub_sku_row(sub_sku_code).get_by_text("Available", exact=False).inner_text()

    def sub_sku_available_count(self, sub_sku_code):
        """The "N Available" figure on a Sub-SKU row, as an int."""
        return int(self.sub_sku_available_text(sub_sku_code).split()[0])

    def sub_sku_add_button_disabled(self, sub_sku_code):
        """Whether a Sub-SKU row's "+" button is currently disabled."""
        return self._sub_sku_row(sub_sku_code).get_by_role("button").last.is_disabled()

    def sub_sku_remove_button_disabled(self, sub_sku_code):
        """Whether a Sub-SKU row's "-" button is currently disabled (true at qty 0)."""
        return self._sub_sku_row(sub_sku_code).get_by_role("button").first.is_disabled()

    def sub_sku_quantity(self, sub_sku_code):
        """Current Add Items count for a Sub-SKU row (0 if untouched)."""
        row = self._sub_sku_row(sub_sku_code)
        minus_btn = row.get_by_role("button").first
        text = minus_btn.locator("xpath=following-sibling::div[1]").inner_text().strip()
        return int(text) if text.isdigit() else 0

    def add_sub_sku_item(self, sub_sku_code, count=1):
        """Click "+" on a Sub-SKU row ``count`` times (default 1).

        Stops early if "+" becomes disabled - a real HTML `disabled` button
        cannot be clicked, so retrying would hang instead of no-op.
        """
        row = self._sub_sku_row(sub_sku_code)
        plus_btn = row.get_by_role("button").last
        for _ in range(count):
            if plus_btn.is_disabled():
                break
            plus_btn.click()
            self.page.wait_for_timeout(300)

    def remove_sub_sku_item(self, sub_sku_code, count=1):
        """Click "-" on a Sub-SKU row ``count`` times (default 1); never below 0.

        Stops early once "-" is disabled (quantity already 0), for the same
        reason as ``add_sub_sku_item``.
        """
        row = self._sub_sku_row(sub_sku_code)
        minus_btn = row.get_by_role("button").first
        for _ in range(count):
            if minus_btn.is_disabled():
                break
            minus_btn.click()
            self.page.wait_for_timeout(300)

    def footer_summary_text(self):
        """Footer text once at least one item is added (e.g. "1 Units of DTE15A0666 added")."""
        return self.footer_summary.inner_text()

    def click_next(self):
        self.next_btn.click()
        self.page.wait_for_timeout(500)

    def click_back(self):
        self.back_btn.click()
        self.page.wait_for_timeout(500)

    def summary_row(self, sub_sku_code):
        """The Request Summary (Step 2) row for ``sub_sku_code``.

        Same structural-filter approach as ``_sub_sku_row``: no
        ``data-testid`` on Step 2 either.
        """
        return (
            self.page.locator("div")
            .filter(has_text=sub_sku_code)
            .filter(has_text="Units")
            .last
        )

    def set_history_sort(self, label):
        """label: "Newest First" or "Oldest First". No-op if already set.

        Confirmed live 2026-08-28: calling this when ``label`` is already the
        current sort opens the menu and leaves *two* elements with that exact
        text on screen (the button itself + the now-open menu option),
        which is a Playwright strict-mode violation - hence the guard and
        the ``.last`` (the menu option is always the later match, same fix
        as DispatcherHomePage.set_sort)."""
        if self.history_sort_button.inner_text().strip() == label:
            return
        self.history_sort_button.click()
        self.page.get_by_text(label, exact=True).last.click()
        self.page.wait_for_timeout(800)

    def search_by_material_code(self, text):
        self.history_search_input.fill(text)
        self.page.wait_for_timeout(800)

    def request_history_row_ids(self):
        """"Req-NNN" id text for every currently-visible Request History row.

        Searches each row's full text rather than a specific nested element -
        confirmed live some rows (e.g. still-populating ones) render their
        other cells differently, but the "Req-NNN" id itself is always there.
        """
        rows = self.page.locator("tbody tr")
        ids = []
        for i in range(rows.count()):
            match = re.search(r"Req-\d+", rows.nth(i).inner_text())
            if match:
                ids.append(match.group(0))
        return ids

    def request_history_row_texts(self):
        """Full text of every currently-visible Request History **data** row.

        Confirmed live 2026-09-07: the table interleaves zero-height spacer
        ``<tr>`` elements between real rows (they render as an empty string via
        ``inner_text``). Those are not rows any caller wants, so they are
        filtered out here rather than in each caller.
        """
        rows = self.page.locator("tbody tr")
        texts = (rows.nth(i).inner_text().strip() for i in range(rows.count()))
        return [t for t in texts if t]

    def open_staging_area(self):
        self.staging_area_nav.click()
        # The grid container renders before its card children (async fetch),
        # so wait for an actual card, not just the empty grid.
        self.page.locator("#staging-area-list-admin-card-0").wait_for(state="visible", timeout=10000)

    def staging_area_card_count(self):
        """Number of Staging Area cards currently rendered (post-filter)."""
        return self.staging_card_grid.locator("> div").count()

    def staging_area_card_title(self, index=0):
        return self.page.locator(f"#staging-area-list-admin-card-title-{index}").inner_text()

    def staging_area_card_subtitle(self, index=0):
        return self.page.locator(f"#staging-area-list-admin-card-subtitle-{index}").inner_text()

    def staging_area_utilised_text(self, index=0):
        return self.page.locator(f"#staging-area-list-admin-card-utilised-label-{index}").inner_text()

    def staging_area_progress_value(self, index=0):
        """The progress bar's own declared percentage (aria-valuenow, 0-100)."""
        bar = self.page.locator(f"#staging-area-list-admin-card-progress-section-{index} [role='progressbar']")
        return int(bar.get_attribute("aria-valuenow"))

    def staging_area_search(self, text):
        self.staging_search_input.fill(text)
        self.page.wait_for_timeout(600)

    def staging_area_select_fleet(self, name):
        self.staging_fleet_select.click()
        self.page.get_by_role("option", name=name, exact=True).click()
        self.page.wait_for_timeout(600)

    def summary_quantity(self, sub_sku_code):
        """Quantity shown for ``sub_sku_code`` on the Request Summary step.

        DOM: a "Units" label div sits next to a quantity div, both children
        of the same row container - go up to the label's parent before
        looking sideways for its preceding sibling.
        """
        row = self.summary_row(sub_sku_code)
        units_label = row.get_by_text("Units", exact=True)
        qty_container = units_label.locator("xpath=../preceding-sibling::div[1]")
        text = qty_container.inner_text().strip()
        return int(text) if text.isdigit() else None

    # ── Step 3 Confirmation screen helpers ────────────────────────────────────

    def click_confirm_and_wait(self, timeout=15000):
        """Click the Confirm button on Step 2 and wait for the Step 3
        Confirmation screen to appear.

        Waits for the "Request confirmed!" heading rather than a fixed sleep,
        so the test fails fast if the app never transitions.
        """
        self.confirm_btn.click()
        self.confirmation_heading.wait_for(state="visible", timeout=timeout)

    def click_home(self):
        """Click the Home button on the Confirmation screen to return to the
        Request History landing page.
        """
        self.home_btn.click()
        self.page.wait_for_timeout(800)

    def confirmation_summary_row(self, sub_sku_code):
        """The row in the Step 3 Summary section for ``sub_sku_code``.

        The Confirmation screen re-uses the same structural markup as
        Request Summary: a plain div containing the code, description and
        a unit count — no data-testid here either.
        """
        return (
            self.page.locator("div")
            .filter(has_text=sub_sku_code)
            .filter(has_text="unit")  # "1 unit" label on confirmation screen
            .last
        )

    # ── Request History - cancel a request ────────────────────────────────────

    def get_first_requested_row(self):
        """Return (req_id, row_locator) for the topmost row on the Requested tab.

        Does NOT click the row body — the ⊗ icon in the ACTIONS column is
        always inline and never needs a row expansion to become reachable.
        """
        self.request_history_nav.click()
        self.requested_tab.click()
        self.page.wait_for_timeout(800)
        rows = self.page.locator("tbody tr")
        rows.first.wait_for(state="visible", timeout=15000)
        first_row = rows.first
        req_id_match = re.search(r"Req-\d+", first_row.inner_text())
        req_id = req_id_match.group(0) if req_id_match else None
        return req_id, first_row

    # Backwards-compat alias used by test_13 before the rename.
    def open_newest_requested_order(self):
        """Deprecated alias for get_first_requested_row(); returns only req_id."""
        req_id, _ = self.get_first_requested_row()
        return req_id

    def click_cancel_icon_on_row(self, row, timeout=10000):
        """Click the red ⊗ cancel icon in the row's ACTIONS column.

        The ACTIONS cell holds icon-only MUI IconButtons with no accessible
        name. As of 2026-09-03 there are **two**: the ⊗ cancel (first) and an
        expand-details chevron (second). So target the FIRST button in the
        last <td> — a whole-cell match is a strict-mode violation on two
        elements, and ``.last`` clicks the chevron (which is why the old
        code silently stopped cancelling anything).
        """
        cancel_btn = row.locator("td").last.get_by_role("button").first
        try:
            cancel_btn.wait_for(state="visible", timeout=timeout // 2)
            cancel_btn.click()
        except Exception:
            # Fallback: first icon button anywhere in the row.
            row.get_by_role("button").first.click()
        self.page.wait_for_timeout(800)

    def click_cancel_request(self, timeout=10000):
        """Backwards-compat entry point used by test_13.

        Finds the first Requested row (already navigated to the Requested tab)
        and clicks its ACTIONS-column cancel icon.
        """
        rows = self.page.locator("tbody tr")
        rows.first.wait_for(state="visible", timeout=timeout)
        self.click_cancel_icon_on_row(rows.first, timeout=timeout)

    def confirm_cancel_dialog(self, timeout=8000):
        """Confirm the "Cancel Request — Are you sure…?" dialog.

        Live 2026-09-03 the confirming button is labelled **"Yes, Cancel"**
        (with a "No" beside it). Tolerates the app cancelling inline with no
        dialog, but raises if a dialog is open and no affirmative button
        matches — the old silent no-op is what let a broken cancel pass as a
        success right up to the "did not appear in Cancelled" assertion.
        """
        dialog = self.page.locator(".MuiDialog-container, [role='dialog']").first
        try:
            dialog.wait_for(state="visible", timeout=timeout // 2)
        except Exception:
            return  # cancelled inline, no dialog

        for label in ("Yes, Cancel", "Yes", "Confirm", "OK"):
            btn = dialog.get_by_role("button", name=label, exact=False)
            if btn.count() and btn.first.is_visible():
                btn.first.click()
                self.page.wait_for_timeout(1000)
                return

        raise AssertionError(
            "Cancel confirmation dialog is open but no affirmative button "
            f"matched. Buttons present: {dialog.get_by_role('button').all_text_contents()}"
        )

    def request_id_in_tab(self, req_id, tab_label, timeout=10000):
        """Return True if ``req_id`` (e.g. "Req-472") appears in ``tab_label``'s
        rows within ``timeout`` ms.  Polls until found or timeout.
        """
        tab = self.page.get_by_text(tab_label, exact=True).first
        tab.click()
        self.page.wait_for_timeout(800)
        deadline = timeout
        interval = 1000
        while deadline > 0:
            rows = self.page.locator("tbody tr")
            for i in range(rows.count()):
                if req_id in rows.nth(i).inner_text():
                    return True
            self.page.wait_for_timeout(interval)
            deadline -= interval
        return False
