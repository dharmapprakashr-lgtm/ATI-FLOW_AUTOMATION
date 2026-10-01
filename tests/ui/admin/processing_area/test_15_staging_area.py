"""Staging Area — Part 3e.

TC_STG_001  Staging Area renders as a colour-coded cell grid with a legend
TC_STG_003  Managing a cell: Cell State, and "Filled with -> Material" fields

TC_STG_002 (reassign a Staging Area to a different Processing Area) was deleted
2026-09-04: re-confirmed live there is no reassignment control in the product —
the Manage-cell dialog is the only editable surface and has no Processing Area /
move-to field. Staging areas are FM-provisioned and appear scoped to one
Processing Area for their lifetime.

Staging Areas are provisioned from Fleet Manager (FM) - there is no "Add
Staging Area" form on this tab. The only way this app itself builds one is
the "Staging Area" toggle on Material creation (see ``add_material`` in
``pages/admin/admin_navigation.py``), which is how the suite's baseline
staging area - ``TestData.staging_area_name`` ("AH_stage") - comes to exist.

Confirmed layout (re-verified live against AH_stage, a 1x4 grid, 2026-09-04
via DOM probe — the grid cells carry no visible text, so the earlier version
of this file could not find them and TC_STG_003 always runtime-skipped):

- ``#staging-area-view-grid-inner`` wraps a column-header row
  (``#staging-area-view-col-headers``) and one row per grid row. Each cell is
  a ``<div>`` holding an inner colour swatch ``<div color="#RRGGBB">``:
  Available #009688 (teal), Reserved #FFB300, Blocked #FF726A, Filled #4FC3F7
  — matching the legend (``#staging-area-view-legend``). A cell the app
  disallows editing carries ``[disabled]`` and ``cursor: not-allowed``.
- Top-right View / Manage toggle: ``#staging-area-view-mode-manage-btn`` is
  what makes the (non-disabled) cells clickable.
- Clicking a cell opens the "Cell A1" dialog (``#manage-cell-dialog-content``):
    Cell State  * (#manage-dialog-cell-state-select)     Available | Reserved | Blocked
    Filled with * (#manage-cell-dialog-filled-with-select) None | Material
      -> "Material" reveals Material Type Name (#manage-cell-dialog-sku-autocomplete),
         Quantity (#manage-cell-dialog-quantity-input),
         MHE Number (#manage-cell-dialog-mhe-number-autocomplete)
    #manage-cell-dialog-cancel-btn / #manage-cell-dialog-save-btn

  Note: "Filled" is a *legend* state only — a cell becomes Filled by choosing
  "Filled with -> Material", it is NOT a selectable Cell State option. The
  selectable states are Available / Reserved / Blocked.

AH_stage is the suite's shared baseline (requester/dispatcher/supervisor all
bind to it), so nothing here may actually change a cell's state - every test
below closes via CANCEL, never SAVE.
"""

import re

import allure
import pytest
from playwright.sync_api import expect

from config.data import TestData

pytestmark = [pytest.mark.admin_pa]

# The legend below the grid shows all four states; only three of them are
# selectable Cell States (see module docstring — "Filled" is set indirectly).
_LEGEND_STATES = ("Available", "Reserved", "Blocked", "Filled")
_SELECTABLE_CELL_STATES = ("Available", "Reserved", "Blocked")
_DIMENSIONS_TEXT = re.compile(r"\d+\s*[×xX]\s*\d+\s*cells")
_CELL_DIALOG_TITLE = re.compile(r"^Cell\s+[A-Za-z]?\d+", re.IGNORECASE)

#: Stable ids from the Staging Area "view" surface (confirmed live 2026-09-04).
_GRID_INNER = "#staging-area-view-grid-inner"
_MANAGE_BTN = "#staging-area-view-mode-manage-btn"
#: A grid cell = a div wrapping a colour swatch (<div color="#...">); a cell the
#: app won't let you edit carries [disabled]. This is the locator the old
#: _click_first_cell was missing.
_EDITABLE_CELL = f"{_GRID_INNER} div:has(> div[color]):not([disabled])"
_CELL_DIALOG = "#manage-cell-dialog-content"


def _open_staging_area(page, name):
    """Click the named staging area and wait for its cell grid to render."""
    page.get_by_text(name, exact=True).first.click(force=True)
    page.locator(_GRID_INNER).wait_for(state="visible", timeout=10000)
    expect(page.get_by_text(_DIMENSIONS_TEXT).first).to_be_visible(timeout=10000)


def _open_first_cell_dialog(page):
    """Enter Manage mode, click the first editable grid cell, and wait for the
    "Cell A1" management dialog. Returns True on success, False if the grid
    exposes no editable cell (every cell [disabled]).
    """
    manage_btn = page.locator(_MANAGE_BTN)
    if manage_btn.count() and manage_btn.first.is_visible():
        manage_btn.first.click(force=True)
        page.wait_for_timeout(600)

    cells = page.locator(_EDITABLE_CELL)
    if cells.count() == 0:
        return False

    cells.first.click(force=True)
    try:
        page.locator(_CELL_DIALOG).wait_for(state="visible", timeout=5000)
    except Exception:
        return False
    return True


# =============================================================================
# Cell grid and legend
# =============================================================================

@allure.feature("Admin Console")
@allure.story("Processing Area: staging area cell grid")
class TestStagingAreaGrid:
    """TC_STG_001"""

    @allure.title("TC_STG_001 — Staging Area renders as a colour-coded cell grid with a legend")
    def test_staging_area_shows_cell_grid_and_legend(self, admin_page, processing_area):
        """
        ID     : TC_STG_001
        Title  : Staging Area renders as a colour-coded cell grid with a legend
        Reason : The grid is how an operator sees, at a glance, which
                 physical slots are free, reserved, blocked or filled - a
                 missing legend entry or a grid that fails to render leaves
                 that decision to guesswork on the shop floor.
        """
        processing_area.go_to_staging_area()

        with allure.step(f"Open staging area '{TestData.staging_area_name}'"):
            _open_staging_area(admin_page, TestData.staging_area_name)

        with allure.step("Heading and cell-count subtitle are visible"):
            expect(
                admin_page.get_by_role("heading", name=TestData.staging_area_name)
            ).to_be_visible(timeout=5000)
            expect(admin_page.get_by_text(_DIMENSIONS_TEXT).first).to_be_visible(timeout=5000)

        with allure.step("Legend shows all four cell states"):
            for state in _LEGEND_STATES:
                expect(admin_page.get_by_text(state, exact=True).first).to_be_visible(timeout=5000)


# =============================================================================
# Managing a cell
# =============================================================================

@allure.feature("Admin Console")
@allure.story("Processing Area: staging area cell management")
class TestStagingAreaCellManagement:
    """TC_STG_003"""

    @allure.title("TC_STG_003 — Managing a cell exposes Cell State and Filled-with-Material fields")
    def test_manage_cell_fields(self, admin_page, processing_area):
        """
        ID     : TC_STG_003
        Title  : Managing a cell exposes Cell State and a conditional Material section
        Reason : This dialog is how an operator marks a physical slot occupied
                 or free. Confirms the field set matches the app rather than
                 the earlier (fictional) staging-area rename form this test
                 used to assume - and never saves, since AH_stage is the
                 suite's shared baseline every device role binds to.

        Ran green after 2026-09-04: the grid cell has no visible text, so the
        old locator-guessing helper never opened the dialog and this test
        silently skipped every run. It now uses the confirmed stable ids
        (see module docstring).
        """
        processing_area.go_to_staging_area()

        with allure.step(f"Open staging area '{TestData.staging_area_name}'"):
            _open_staging_area(admin_page, TestData.staging_area_name)

        with allure.step("Enter Manage mode and open a cell's management dialog"):
            if not _open_first_cell_dialog(admin_page):
                pytest.skip(
                    f"Staging area '{TestData.staging_area_name}' currently "
                    "exposes no editable (non-[disabled]) grid cell — every "
                    "cell is locked. Nothing to open a manage dialog on."
                )

        try:
            with allure.step("Cell State offers Available / Reserved / Blocked"):
                cell_state = admin_page.locator("#manage-dialog-cell-state-select")
                expect(cell_state).to_be_visible(timeout=5000)
                cell_state.click(force=True)
                admin_page.wait_for_timeout(500)
                for state in _SELECTABLE_CELL_STATES:
                    expect(
                        admin_page.get_by_role("option", name=state, exact=True)
                    ).to_be_visible(timeout=3000)
                # "Filled" is a legend-only state, NOT a selectable option.
                assert (
                    admin_page.get_by_role("option", name="Filled", exact=True).count() == 0
                ), "Cell State now offers 'Filled' as a direct option — the app changed."
                admin_page.keyboard.press("Escape")
                admin_page.wait_for_timeout(300)

            with allure.step("'Filled with' -> Material reveals Material Type Name, Quantity, MHE Number"):
                filled_with = admin_page.locator("#manage-cell-dialog-filled-with-select")
                expect(filled_with).to_be_visible(timeout=5000)
                filled_with.click(force=True)
                admin_page.wait_for_timeout(500)
                admin_page.get_by_role("option", name="Material", exact=True).click(force=True)
                admin_page.wait_for_timeout(700)

                for field_id in (
                    "#manage-cell-dialog-sku-autocomplete",       # Material Type Name
                    "#manage-cell-dialog-quantity-input",         # Quantity
                    "#manage-cell-dialog-mhe-number-autocomplete",  # MHE Number
                ):
                    expect(admin_page.locator(field_id)).to_be_visible(timeout=5000)
        finally:
            # Never SAVE — AH_stage is shared, and this test only verifies
            # the dialog's fields, not a real state change.
            cancel_btn = admin_page.locator("#manage-cell-dialog-cancel-btn")
            if cancel_btn.count() > 0 and cancel_btn.first.is_visible(timeout=1000):
                cancel_btn.first.click(force=True)
            else:
                admin_page.keyboard.press("Escape")
            admin_page.wait_for_timeout(500)
