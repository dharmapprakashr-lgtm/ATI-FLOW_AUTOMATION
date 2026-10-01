"""Supervisor dashboard page object.

Locators verified live against the running app on 2026-09-07 (the old
``h1.welcome-supervisor`` stub matched nothing real). After login the
supervisor device lands on ``/stagingArea``. The shell is the same
``#operator-sidebar-*`` component the requester and dispatcher use, plus a
Processing Area selector unique to this role.

Screens reachable from the sidebar (three nav items only):

    #operator-sidebar-nav-item-stagingArea    "Staging Area"   -> /stagingArea
    #operator-sidebar-nav-item-opsinventory    "WIP Inventory"  -> /opsinventory
    #operator-sidebar-nav-item-auto-trips      "Auto Trips"     -> /auto-trips

Plus:

    #operator-sidebar-supervisor-area-select   Processing Area switcher (MUI Select).
        Its popup <li role="option"> list is EXACTLY the device's bound
        processing area(s) - not every area in the system.
    #operator-sidebar-notif-row                Notifications drawer trigger (count badge)

What this build's Supervisor does NOT have (confirmed live, not guessed):

  * No "Inventory Adjustment" surface - Action Add/Remove, Sub-SKU Type,
    Quantity, Location, Reason. WIP Inventory (/opsinventory) is a read-only
    aggregated table whose only control is a Refresh button
    (#wip-refresh-btn). Same read-only projection as the admin WIP tab.
  * No live/websocket push on any screen - WIP and Auto Trips both use a
    manual "Refresh" + "Updated just now" model.
  * Notifications are connectivity alerts only (FM/MES unreachable). No
    Retry, no "Handle Manually", no History tab - just per-card dismiss and
    a "Clear all" button.

Staging Area detail (``/operator/stagingArea/view/<id>``) is the same
component the admin Staging Area tab renders: a colour-coded cell grid
(#staging-area-view-grid-inner) with a legend (#staging-area-view-legend):
Available #009688 (teal), Reserved #FFB300 (amber), Blocked #FF726A,
Filled #4FC3F7. The View / Manage toggle
(#staging-area-view-mode-view-btn / -manage-btn) makes non-[disabled] cells
clickable; a cell opens #manage-cell-dialog-content. AH_stage is the suite's
shared baseline every device role binds to, so nothing here may ever SAVE a
cell change - callers close the dialog via CANCEL.
"""

import re


class SupervisorHomePage:
    def __init__(self, page):
        self.page = page

        # ── Sidebar shell ────────────────────────────────────────────────────
        self.pa_select = page.locator("#operator-sidebar-supervisor-area-select")
        self.pa_selector_wrap = page.locator("#operator-sidebar-supervisor-area-selector")
        self.pa_label = page.locator("#operator-sidebar-supervisor-area-label")

        self.staging_area_nav = page.locator("#operator-sidebar-nav-item-stagingArea")
        self.wip_inventory_nav = page.locator("#operator-sidebar-nav-item-opsinventory")
        self.auto_trips_nav = page.locator("#operator-sidebar-nav-item-auto-trips")

        self.notif_row = page.locator("#operator-sidebar-notif-row")
        self.notif_text = page.locator("#operator-sidebar-notif-text")
        self.profile_name = page.locator("#operator-sidebar-profile-name")
        self.profile_role = page.locator("#operator-sidebar-profile-role")
        self.logout_row = page.locator("#operator-sidebar-logout-row")

        # ── Staging Area list (same component as the requester's) ────────────
        self.staging_search_input = page.locator("#staging-area-search-input")
        self.staging_fleet_select = page.locator("#staging-area-fleet-select")
        self.staging_card_grid = page.locator("#staging-area-list-admin-card-grid")

        # ── Staging Area detail ─────────────────────────────────────────────
        self.staging_view_root = page.locator("#staging-area-view-root")
        self.staging_view_title = page.locator("#staging-area-view-title")
        self.staging_view_subtitle = page.locator("#staging-area-view-subtitle")
        self.staging_view_grid = page.locator("#staging-area-view-grid-inner")
        self.staging_view_legend = page.locator("#staging-area-view-legend")
        self.staging_view_btn = page.locator("#staging-area-view-mode-view-btn")
        self.staging_manage_btn = page.locator("#staging-area-view-mode-manage-btn")
        self.cell_dialog = page.locator("#manage-cell-dialog-content")
        self.cell_dialog_cancel = page.locator("#manage-cell-dialog-cancel-btn")

        # ── WIP Inventory (/opsinventory) ──────────────────────────────────
        self.wip_refresh_btn = page.locator("#wip-refresh-btn")
        self.wip_search_input = page.locator("#wip-search")
        self.wip_table = page.locator("table").first

        # ── Auto Trips (/auto-trips) ──────────────────────────────────────
        self.trips_refresh_btn = page.get_by_role("button", name="Refresh")

    # ── Sidebar / Processing Area selector ───────────────────────────────────

    def bound_processing_area_text(self):
        """Currently-selected value in the sidebar Processing Area dropdown."""
        return self.pa_select.inner_text().strip()

    current_processing_area = bound_processing_area_text  # readable alias

    def _pa_options(self):
        return self.page.locator(
            "ul[role='listbox'] li[role='option'], .MuiMenu-list li[role='option']"
        )

    def open_processing_area_dropdown(self):
        """Open the PA switcher; return the option labels it offers."""
        self.pa_select.click()
        self.page.wait_for_timeout(600)
        options = self._pa_options()
        try:
            options.first.wait_for(state="visible", timeout=5000)
        except Exception:
            return []
        return [o.strip() for o in options.all_text_contents() if o.strip()]

    def close_dropdown(self):
        self.page.keyboard.press("Escape")
        self.page.wait_for_timeout(300)

    def select_processing_area(self, name):
        self.pa_select.click()
        self.page.wait_for_timeout(400)
        self._pa_options().filter(
            has_text=re.compile(rf"^{re.escape(name)}$")
        ).first.click()
        self.page.wait_for_timeout(1500)

    # ── Navigation ──────────────────────────────────────────────────────────

    def go_to_staging_area(self):
        self.staging_area_nav.click()
        self.page.wait_for_url(re.compile(r"/stagingArea"), timeout=10000)
        self.page.wait_for_timeout(800)

    def go_to_wip_inventory(self):
        self.wip_inventory_nav.click()
        self.page.wait_for_url(re.compile(r"/opsinventory"), timeout=10000)
        self.page.wait_for_timeout(800)

    def go_to_auto_trips(self):
        self.auto_trips_nav.click()
        self.page.wait_for_url(re.compile(r"/auto-trips"), timeout=10000)
        self.page.wait_for_timeout(800)

    def sidebar_nav_labels(self):
        """Visible text of every sidebar nav item, in order."""
        items = self.page.locator(
            "[id^='operator-sidebar-nav-item-text-']"
        )
        return [items.nth(i).inner_text().strip() for i in range(items.count())]

    # ── Staging Area list ──────────────────────────────────────────────────

    def open_staging_area_list(self):
        self.go_to_staging_area()
        try:
            self.page.locator("#staging-area-list-admin-card-0").wait_for(
                state="visible", timeout=10000
            )
        except Exception:
            pass  # a legitimately empty list is a valid state

    def staging_card_count(self):
        return self.staging_card_grid.locator("> div").count()

    def staging_card_title(self, index=0):
        return self.page.locator(
            f"#staging-area-list-admin-card-title-{index}"
        ).inner_text().strip()

    def staging_card_subtitle(self, index=0):
        return self.page.locator(
            f"#staging-area-list-admin-card-subtitle-{index}"
        ).inner_text().strip()

    def staging_card_utilised_text(self, index=0):
        return self.page.locator(
            f"#staging-area-list-admin-card-utilised-label-{index}"
        ).inner_text().strip()

    def staging_card_titles(self):
        """Title text of every staging area card currently rendered."""
        out = []
        for i in range(self.staging_card_count()):
            loc = self.page.locator(f"#staging-area-list-admin-card-title-{i}")
            if loc.count():
                out.append(loc.inner_text().strip())
        return out

    def search_staging_area(self, text):
        self.staging_search_input.fill(text)
        self.page.wait_for_timeout(700)

    def open_staging_card(self, index=0):
        self.page.locator(f"#staging-area-list-admin-card-{index}").click()
        self.staging_view_grid.wait_for(state="visible", timeout=10000)
        self.page.wait_for_timeout(600)

    def open_staging_area_by_name(self, name):
        self.page.get_by_text(name, exact=True).first.click(force=True)
        self.staging_view_grid.wait_for(state="visible", timeout=10000)
        self.page.wait_for_timeout(600)

    # ── Staging Area detail ───────────────────────────────────────────────

    def staging_detail_title(self):
        return self.staging_view_title.inner_text().strip()

    def staging_detail_subtitle(self):
        return self.staging_view_subtitle.inner_text().strip()

    def legend_state_labels(self):
        """The state names shown in the cell-grid legend."""
        items = self.staging_view_legend.locator(
            "[id^='staging-area-view-legend-item-']"
        )
        return [items.nth(i).inner_text().strip() for i in range(items.count())]

    def legend_swatch_colour(self, state):
        """The ``color="#RRGGBB"`` attribute on the legend swatch for ``state``
        ("Available" | "Reserved" | "Blocked" | "Filled"). Upper-cased hex."""
        item = self.page.locator(
            f"#staging-area-view-legend-item-legend{state}"
        )
        swatch = item.locator("div[color]").first
        value = swatch.get_attribute("color") or ""
        return value.upper()

    def cell_colours_in_grid(self):
        """Every cell swatch colour currently painted in the grid (upper hex)."""
        swatches = self.staging_view_grid.locator("div[color]")
        out = []
        for i in range(swatches.count()):
            c = swatches.nth(i).get_attribute("color")
            if c:
                out.append(c.upper())
        return out

    def enter_manage_mode(self):
        if self.staging_manage_btn.count() and self.staging_manage_btn.is_visible():
            self.staging_manage_btn.click(force=True)
            self.page.wait_for_timeout(600)

    def open_first_editable_cell_dialog(self):
        """Enter Manage mode and open the first non-[disabled] cell's dialog.

        Returns True on success, False when every cell is locked ([disabled]).
        Never saves - AH_stage is the shared baseline.
        """
        self.enter_manage_mode()
        cells = self.staging_view_grid.locator(
            "div:has(> div[color]):not([disabled])"
        )
        if cells.count() == 0:
            return False
        cells.first.click(force=True)
        try:
            self.cell_dialog.wait_for(state="visible", timeout=5000)
        except Exception:
            return False
        return True

    def cell_dialog_field_ids_present(self):
        """Which of the known manage-cell field ids are visible right now."""
        ids = (
            "#manage-dialog-cell-state-select",
            "#manage-cell-dialog-filled-with-select",
            "#manage-cell-dialog-sku-autocomplete",
            "#manage-cell-dialog-quantity-input",
            "#manage-cell-dialog-mhe-number-autocomplete",
        )
        return [i for i in ids if self.page.locator(i).count()
                and self.page.locator(i).first.is_visible()]

    def close_cell_dialog(self):
        if self.cell_dialog_cancel.count() and self.cell_dialog_cancel.first.is_visible():
            self.cell_dialog_cancel.first.click(force=True)
        else:
            self.page.keyboard.press("Escape")
        self.page.wait_for_timeout(500)

    # ── WIP Inventory ─────────────────────────────────────────────────────

    def wip_column_headers(self):
        headers = self.wip_table.locator("thead th, thead td")
        return [headers.nth(i).inner_text().strip()
                for i in range(headers.count())
                if headers.nth(i).inner_text().strip()]

    def wip_row_texts(self):
        rows = self.wip_table.locator("tbody tr")
        return [rows.nth(i).inner_text().strip() for i in range(rows.count())]

    #: WIP column order — the shared aggregated-inventory contract (admin WIP
    #: tab + requester view use the same one). ``total_qty`` is the computed
    #: rollup of the four quantity columns before it.
    WIP_COLUMN_KEYS = (
        "material_type_name", "code", "production_unit", "in_transit",
        "processed", "pre_processed", "requested", "total_qty", "uom",
    )
    _WIP_ROLLUP_PARTS = ("in_transit", "processed", "pre_processed", "requested")

    def wip_row_records(self):
        """Every WIP data row as a dict keyed by :data:`WIP_COLUMN_KEYS`."""
        records = []
        rows = self.wip_table.locator("tbody tr")
        for i in range(rows.count()):
            cells = rows.nth(i).locator("td")
            values = [cells.nth(j).inner_text().strip() for j in range(cells.count())]
            if not values or "no inventory data" in values[0].lower():
                continue
            records.append(dict(zip(self.WIP_COLUMN_KEYS, values)))
        return records

    @classmethod
    def wip_rollup_ok(cls, record):
        """True when total_qty == in_transit + processed + pre_processed + requested."""
        try:
            return sum(int(record[k]) for k in cls._WIP_ROLLUP_PARTS) == int(record["total_qty"])
        except (ValueError, KeyError):
            return False

    def wip_is_empty_state(self):
        body = self.wip_table.locator("tbody").inner_text().lower()
        return "no inventory data" in body or "no data" in body

    def wip_pagination_total(self):
        """The "z" in "x-y of z" on the WIP table's pagination footer."""
        text = self.page.locator(".MuiTablePagination-displayedRows").inner_text()
        m = re.search(r"of\s+([\d,]+)", text)
        return int(m.group(1).replace(",", "")) if m else None

    def wip_updated_label(self):
        loc = self.page.get_by_text(re.compile(r"Updated .*", re.IGNORECASE)).first
        return loc.inner_text().strip() if loc.count() else ""

    def wip_refresh(self):
        self.wip_refresh_btn.click()
        self.page.wait_for_timeout(1200)

    def wip_search(self, text):
        self.wip_search_input.fill(text)
        self.page.wait_for_timeout(1000)

    # ── Auto Trips ───────────────────────────────────────────────────────

    def trips_row_texts(self):
        rows = self.page.locator("table tbody tr")
        return [rows.nth(i).inner_text().strip() for i in range(rows.count())]

    def trips_column_headers(self):
        headers = self.page.locator("table thead th, table thead td")
        return [headers.nth(i).inner_text().strip()
                for i in range(headers.count())
                if headers.nth(i).inner_text().strip()]

    # ── Notifications drawer ────────────────────────────────────────────

    def open_notifications(self):
        self.notif_row.click()
        self.page.wait_for_timeout(1200)

    def notifications_panel(self):
        return self.page.locator(
            ".MuiDrawer-paper, .MuiPopover-paper, [role='dialog']"
        ).first

    def notifications_panel_text(self):
        return self.notifications_panel().inner_text()

    def notification_titles(self):
        """The chip label on every notification card (e.g. "MES Unreachable")."""
        chips = self.notifications_panel().locator(".MuiChip-label")
        return [chips.nth(i).inner_text().strip() for i in range(chips.count())]

    def notification_bodies(self):
        """The body line under every notification card."""
        paras = self.notifications_panel().locator("p.MuiTypography-body2")
        return [paras.nth(i).inner_text().strip() for i in range(paras.count())]

    def notification_action_labels(self):
        """Text of every button inside the notifications drawer (dismiss
        buttons are icon-only and come back as '')."""
        btns = self.notifications_panel().locator("button")
        return [btns.nth(i).inner_text().strip() for i in range(btns.count())]

    def has_clear_all(self):
        return self.page.get_by_role("button", name="Clear all").is_visible()

    def close_notifications(self):
        backdrop = self.page.locator(".MuiBackdrop-root").first
        if backdrop.count() and backdrop.is_visible():
            backdrop.click(force=True)
        else:
            self.page.keyboard.press("Escape")
        try:
            self.page.locator(".MuiDrawer-modal, .MuiBackdrop-root").first.wait_for(
                state="hidden", timeout=5000
            )
        except Exception:
            pass
        self.page.wait_for_timeout(300)

    # ── Misc ────────────────────────────────────────────────────────────

    def get_welcome_message(self):
        """Backwards-compat shim for the old stub's only method."""
        return self.profile_role.inner_text().strip() if self.profile_role.count() else ""
