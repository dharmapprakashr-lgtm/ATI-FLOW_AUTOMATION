"""
StagingAreaPage
----------------
Covers TC_PA_001 - TC_PA_012 (List View, Grid View, Cell Management).

SELECTOR STATUS (updated from playwright codegen recordings + screenshot, Aug 11):

- Confirmed: tab navigation, card heading, View/Manage buttons, Save/Cancel,
  #staging-area-fleet-select dropdown, Search box.

- SPEC MISMATCH — flag to dev/product: the actual Staging Area list view
  shows a Search box + an "All Fleets" dropdown, NOT the All/Active/
  Inactive filter tabs the ticket's Figma spec describes. No Edit (pencil)
  or overflow (⋮) icon was found on the card across three recordings —
  codegen only ever picked up the whole card as one text block
  ("Just nowAH_stage1 x 4 cells2/..."), never a separate button/icon
  element. TC_PA_002 and TC_PA_003 are skipped pending clarification.

- FIXED (Aug 11, via DevTools "Copy element"): the grid cell CSS-in-JS
  hash class was confirmed completely unusable — a real automated run
  showed `.css-11ihfi1` matching ZERO elements in that session (not just
  a different hash, genuinely absent). Replaced with a structural
  selector anchored on #staging-area-view-grid-inner, which DOES have a
  stable id. See cell() below for details. This should finally be
  durable across sessions/rebuilds since it has no dependency on any
  hash class at all.

- CONFIRMED (Aug 11, via screenshot): there are actually TWO distinct
  dialogs, and my "correction" earlier today swapped them — this is the
  corrected, actually-confirmed version:
  1. VIEW mode + click a FILLED cell → "View Trolley Details" dialog:
     read-only-looking fields Cell Location, SKU, Sub-SKU, Quantity, a
     "Filled Trolley — This cell contains material." badge, and a single
     CLOSE button (no Save/Cancel). This is what view_cell_details() /
     close_details_dialog() below target — they were right originally.
  2. MANAGE mode + click any cell → "Cell <ID>" dialog: a "Cell State *"
     combobox (current value e.g. "Available") and a "Filled with *"
     combobox (blank if unfilled, shows fill type e.g. "Material" if
     filled), with Cancel/Save buttons. This is the editable one.
  IMPORTANT LESSON FROM THIS BUG HUNT: TC_PA_006 opened dialog #1 via a
  View-mode click, asserted one thing, and never closed it — which then
  blocked every subsequent test's navigation (each timed out trying to
  click a heading covered by the still-open modal). run_automation.py
  now presses Escape after every test as a generic safety net. Any new
  test that opens a dialog should still close it explicitly when
  possible, rather than relying solely on that safety net.
- IMPORTANT: "Cell C1" in that dialog title suggests cells DO have real,
  human-readable identifiers, not just the unstable CSS class. Worth
  checking DevTools for an aria-label/accessible name on the cell element
  itself (e.g. a button with name "Cell C1") — if it exists, that would
  replace the fragile CSS class entirely with something durable.

- CONFIRMED status options (Aug 11, full recording — the status combobox
  was cycled through all values): "Available", "Reserved", "Blocked" are
  all real, confirmed option texts. Fill Type combobox also confirmed to
  have a "None" option in addition to "Material" (used to clear a fill,
  presumably) — "Trolley" as an option is still not directly confirmed
  (only "Material" and "None" have actually been seen selected).
- NOTE: the same recording showed an ALTERNATE path for selecting a
  material's category — TWO sequential "Open"-button clicks inside
  #manage-cell-dialog-sku-qty-row (selecting "Soft Filler" then
  "General"), rather than the single ID-based autocomplete
  (#manage-cell-dialog-sku-autocomplete) that fill_material() below uses
  and that a REAL PASSING AUTOMATED RUN already confirmed works. Since
  the ID-based approach has actual passing-test evidence behind it,
  fill_material() below is NOT changed to match this alternate recording
  — but if a future run fails here, this two-step "Open" button pattern
  is the first thing to investigate as a possible different UI state.
- CONFIRMED (Aug 11): staging area cards have a stable id pattern
  #staging-area-list-admin-card-top-row-{index} — see get_card_by_index()
  below. Useful when the staging area's name isn't known ahead of time.
"""

from playwright.sync_api import Page, expect
from pages.base_page import BasePage


class StagingAreaPage(BasePage):
    # Grid cell — see cell() below for the CURRENT confirmed approach.
    # This hash class is CONFIRMED UNUSABLE (see module docstring) — kept
    # only as a fallback reference, do not use directly.
    GRID_CELL_CSS = ".css-11ihfi1"  # also seen as .css-16almry, .css-1ld5t3s
    GRID_INNER_ID = "#staging-area-view-grid-inner"

    def __init__(self, page: Page, base_url: str):
        super().__init__(page, base_url)

    # ---------- List view ----------
    def open(self, processing_area: str):
        """
        Scoped to the sidebar nav specifically (#operator-sidebar-nav,
        confirmed via aria snapshot from a real run). Unscoped
        get_by_text(processing_area, exact=True) broke with a strict-mode
        violation once already on that area's page, because the breadcrumb
        ALSO shows the area name — two matches for the same text.
        """
        self.page.locator("#operator-sidebar-nav").get_by_text(processing_area, exact=True).click()
        self.page.get_by_role("tab", name="Staging Area").click()

    def get_card(self, name: str):
        return self.page.get_by_role("heading", name=name)

    def get_card_by_index(self, index: int = 0):
        """
        CONFIRMED (Aug 11, full recording): staging area cards have a
        stable id pattern #staging-area-list-admin-card-top-row-{index}.
        More reliable than get_card(name) when the staging area's name
        isn't known ahead of time — e.g. a freshly auto-provisioned one
        in a newly created area.
        """
        return self.page.locator(f"#staging-area-list-admin-card-top-row-{index}")

    def apply_filter(self, state: str):
        raise NotImplementedError(
            "No All/Active/Inactive filter found in the actual UI — "
            "confirm with dev/product before implementing. See module docstring."
        )

    def select_fleet(self, fleet_name: str):
        self.page.locator("#staging-area-fleet-select").click()
        self.page.get_by_role("option", name=fleet_name).click()

    def search(self, term: str):
        self.page.get_by_placeholder("Search").fill(term)

    def open_grid(self, staging_area_name: str):
        self.get_card(staging_area_name).click()

    def open_grid_by_index(self, index: int = 0):
        """For a staging area whose name isn't known ahead of time — see get_card_by_index()."""
        self.get_card_by_index(index).click()

    # ---------- Grid view ----------
    def switch_to_manage_mode(self):
        self.page.get_by_role("button", name="Manage").click()

    def switch_to_view_mode(self):
        self.page.get_by_role("button", name="View").click()

    def cell(self, index: int = 0, row: int = 0):
        """
        CONFIRMED via DevTools "Copy element" (Aug 11): grid cells
        themselves have no stable class/id, but they live inside
        #staging-area-view-grid-inner, whose id IS stable. Structure:
        grid-inner's children are [col-headers, row0, row1, ...], and
        each row's children are [row-number-label, cell0, cell1, ...].
        This navigates by structural position under the stable parent —
        NO dependency on any css-xxxxx hash class, which is what kept
        breaking the old approach across sessions/rebuilds.

        NOTE: one cell was observed with a literal `disabled` HTML
        attribute (likely how a Blocked cell renders) — clicking it may
        behave differently (may not register a normal click, may need
        Playwright's force=True, or may simply not be interactive by
        design). Not yet confirmed either way — worth checking if a
        block/unblock test targets that specific cell.
        """
        grid_inner = self.page.locator(self.GRID_INNER_ID)
        row_div = grid_inner.locator("> div").nth(row + 1)  # skip col-headers
        return row_div.locator("> div").nth(index + 1)  # skip row-number label

    def click_cell(self, index: int = 0, row: int = 0):
        self.cell(index, row).click()

    # ---------- Status combobox (Available/Reserved/Blocked) ----------
    # CONFIRMED IDs (Aug 11, from a real strict-mode-violation error that
    # helpfully listed every combobox in the dialog with its id/name).
    CELL_STATE_SELECT_ID = "#manage-dialog-cell-state-select"
    FILLED_WITH_SELECT_ID = "#manage-cell-dialog-filled-with-select"
    SKU_TYPE_AUTOCOMPLETE_ID = "#manage-cell-dialog-sku-autocomplete"       # "Material Type Name *"
    SKU_CODE_AUTOCOMPLETE_ID = "#manage-cell-dialog-sku-code-autocomplete"  # "Code *"
    MHE_NUMBER_AUTOCOMPLETE_ID = "#manage-cell-dialog-mhe-number-autocomplete"  # "MHE Number *"

    def open_status_dropdown(self):
        """ID-based now — no longer needs to guess the current displayed value."""
        self.page.locator(self.CELL_STATE_SELECT_ID).click()

    def select_status(self, new_state: str):
        self.page.get_by_role("option", name=new_state).click()

    def set_cell_status(self, new_state: str):
        self.open_status_dropdown()
        self.select_status(new_state)

    # ---------- Manage Cell dialog — Fill Type + Material fill ----------
    def open_fill_type_dropdown(self):
        """ID-based — works whether the dropdown is currently blank or already set."""
        self.page.locator(self.FILLED_WITH_SELECT_ID).click()

    def select_fill_type(self, new_type: str):
        """new_type: 'Material' | 'Trolley' (Trolley not yet directly confirmed as option text)"""
        self.open_fill_type_dropdown()
        self.page.get_by_role("option", name=new_type).click()

    def trolley_option_visible(self) -> bool:
        """
        Opens the Fill Type dropdown and checks whether a 'Trolley' option
        is present, then leaves the dropdown open (caller should press
        Escape or select something to close it).
        """
        self.open_fill_type_dropdown()
        return self.page.get_by_role("option", name="Trolley").is_visible()

    def fill_material(self, category: str, code: str, mhe_number: str,
                       qty: str = None, timestamp: str = None):
        """
        FIXED (Aug 11): now explicitly sets Fill Type to 'Material' first
        — this was the actual bug behind TC_PA_008/009 failing on empty
        cells. The SKU/Code/MHE fields are MUI Autocomplete inputs
        (confirmed via error message IDs) — clicking directly into the
        input by id opens its option list, same as the old "Open" button
        approach did, but without depending on a wrapper/button that
        doesn't reliably exist.
        qty and timestamp are still not wired to a confirmed selector.
        """
        self.select_fill_type("Material")

        self.page.locator(self.SKU_TYPE_AUTOCOMPLETE_ID).click()
        self.page.get_by_role("option", name=category).click()

        self.page.locator(self.SKU_CODE_AUTOCOMPLETE_ID).click()
        self.page.get_by_role("option", name=code).click()

        self.page.locator(self.MHE_NUMBER_AUTOCOMPLETE_ID).click()
        self.page.get_by_role("option", name=mhe_number).click()

        if qty is not None or timestamp is not None:
            import warnings
            warnings.warn(
                "fill_material(): qty/timestamp were passed but have no "
                "confirmed selector yet and were NOT filled.",
                stacklevel=2,
            )

    def save(self):
        self.page.get_by_role("button", name="Save").click()

    def cancel(self):
        self.page.get_by_role("button", name="CANCEL").click()

    def close_panel(self):
        self.page.get_by_role("button", name="Close").click()

    # ---------- Trolley Details view dialog (viewing a filled cell) ----------
    def view_cell_details(self):
        """
        Confirmed fields exist in this dialog: Cell Location, SKU (exact),
        Sub-SKU, Quantity — returned as locators for the caller to assert
        on. Not yet confirmed whether these are read-only or editable.
        """
        return {
            "cell_location": self.page.get_by_role("textbox", name="Cell Location"),
            "sku": self.page.get_by_role("textbox", name="SKU", exact=True),
            "sub_sku": self.page.get_by_role("textbox", name="Sub-SKU"),
            "quantity": self.page.get_by_role("textbox", name="Quantity"),
        }

    def close_details_dialog(self):
        self.page.get_by_role("button", name="Close").click()
