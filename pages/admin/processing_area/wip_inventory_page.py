"""Admin › Processing Area › WIP Inventory tab.

Verified live against the running app on 2026-09-03.

WIP Inventory is a **read-only, system-populated projection** — there is no
Add / Edit / delete / Import control and no editable quantity anywhere on the
tab or in a row's detail panel (Materials and Containers both grew a
"Bulk Upload" + "Export CSV"; WIP has neither — only **Refresh**). The
quantity columns

    In Transit · Processed · Pre-processed · Requested · Total Qty

are system-computed rollups (``Total Qty`` == the sum of the other four), and
they only change when a real task moves stock through the system — which also
means the row set is **volatile live data**: a PA can show ten rows one hour
and "No inventory data found" the next.

Table columns (in order):
    Material Type Name, Code, Production Unit, In Transit, Processed,
    Pre-processed, Requested, Total Qty, UOM, <info-icon>

A row's info icon opens a read-only detail panel: Code, material, Unit/Section,
UOM, and an "MHE Number / Time of Production / Qty" table.
"""

import re

#: Column order of the WIP Inventory table, used to index a row's <td>s.
COLUMNS = [
    "material_type_name",
    "code",
    "production_unit",
    "in_transit",
    "processed",
    "pre_processed",
    "requested",
    "total_qty",
    "uom",
]

#: Numeric columns whose sum must equal ``total_qty``.
_ROLLUP_PARTS = ("in_transit", "processed", "pre_processed", "requested")

EMPTY_TEXT = re.compile(r"no inventory data", re.IGNORECASE)

#: Any of these on the WIP tab would mean the app grew a WIP write path —
#: the signal to build out TC_WIP_001 / TC_WIP_003 / TC_WIP_004 for real.
_WRITE_CONTROL = re.compile(
    r"add|new|create|import|bulk|upload|export", re.IGNORECASE
)


class WipInventoryPage:
    def __init__(self, page):
        self.page = page
        self.refresh_button = page.get_by_role("button", name="Refresh")
        self.rows = page.locator("tbody tr")
        self.detail_panel = page.locator(
            "[role='dialog'], .MuiDrawer-root, .MuiPopover-root"
        ).first

    # ── loading ──────────────────────────────────────────────────────────────
    def wait_until_loaded(self, timeout=12000):
        """Block until the tab has settled on either real rows or the explicit
        'No inventory data found' placeholder (the async fetch can lag the tab
        switch by several seconds)."""
        self.refresh_button.wait_for(state="visible", timeout=timeout)
        elapsed, step = 0, 500
        while elapsed < timeout:
            if self.rows.count():
                first = self.rows.first.inner_text()
                if EMPTY_TEXT.search(first) or len(first.strip()) > 5:
                    return
            self.page.wait_for_timeout(step)
            elapsed += step

    # ── state ────────────────────────────────────────────────────────────────
    def is_empty(self):
        """True when the tab shows the 'No inventory data found' placeholder."""
        return (
            self.rows.count() == 0
            or bool(EMPTY_TEXT.search(self.rows.first.inner_text()))
        )

    def column_headers(self):
        heads = self.page.locator("th")
        return [
            re.sub(r"\s+", " ", heads.nth(i).inner_text()).strip()
            for i in range(heads.count())
        ]

    def toolbar_box(self):
        """The container that wraps the Refresh button + the results table."""
        return self.refresh_button.locator("xpath=ancestor::div[.//table][1]")

    def write_control_labels(self):
        """Text/aria-labels of any create/import/export-shaped control in the
        WIP toolbar. Expected to be empty — WIP is read-only."""
        box = self.toolbar_box()
        buttons = box.get_by_role("button")
        hits = []
        for i in range(buttons.count()):
            label = (
                buttons.nth(i).inner_text().strip()
                or buttons.nth(i).get_attribute("aria-label")
                or ""
            )
            if label and _WRITE_CONTROL.search(label):
                hits.append(label)
        return hits

    def row_records(self):
        """Every data row as a dict keyed by :data:`COLUMNS`."""
        records = []
        for i in range(self.rows.count()):
            cells = self.rows.nth(i).locator("td")
            values = [
                re.sub(r"\s+", " ", cells.nth(j).inner_text()).strip()
                for j in range(cells.count())
            ]
            if values and EMPTY_TEXT.search(values[0]):
                continue
            records.append(dict(zip(COLUMNS, values)))
        return records

    @staticmethod
    def rollup_ok(record):
        """True when total_qty == in_transit + processed + pre_processed + requested."""
        try:
            parts = sum(int(record[key]) for key in _ROLLUP_PARTS)
            return parts == int(record["total_qty"])
        except (ValueError, KeyError):
            return False

    # ── actions ──────────────────────────────────────────────────────────────
    def refresh(self):
        self.refresh_button.click(force=True)
        self.page.wait_for_timeout(2000)
        self.wait_until_loaded()

    def open_row_detail(self, index=0):
        self.rows.nth(index).locator("button").last.click(force=True)
        self.page.wait_for_timeout(1000)
        return self.detail_panel

    def detail_editable_field_count(self):
        """Editable inputs inside the open detail panel (0 == read-only)."""
        return self.detail_panel.locator(
            "input:not([readonly]):not([disabled]), "
            "textarea:not([readonly]):not([disabled]), "
            "[contenteditable='true']"
        ).count()

    def close_detail(self):
        self.page.keyboard.press("Escape")
        self.page.wait_for_timeout(300)
