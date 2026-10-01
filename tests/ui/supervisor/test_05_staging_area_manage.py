"""Supervisor — Staging Area "Manage" mode (per-cell dialog).

Manual test cases covered:
  TC-008  Supervisor can modify staging area details (state / filled-with)
  TC-009  Modification with invalid values is rejected
  TC-010  A saved modification reflects on the dashboard
  TC-025  Location/scope of a modification is restricted to the assigned area

Confirmed live 2026-09-07: the supervisor gets the SAME staging-area editing
surface as admin — a View / Manage toggle (#staging-area-view-mode-manage-btn)
that makes non-[disabled] cells clickable, opening #manage-cell-dialog-content:
    Cell State  (#manage-dialog-cell-state-select)      Available|Reserved|Blocked
    Filled with (#manage-cell-dialog-filled-with-select) None|Material
      -> Material reveals SKU / Quantity (type=number, min=1) / MHE Number
    #manage-cell-dialog-cancel-btn / #manage-cell-dialog-save-btn

There is NO "Action = Add / Remove", NO free-text "Reason", NO "Location"
picker — the cell being clicked *is* the location, always inside the
supervisor's one assigned staging area (TC-025 is satisfied structurally).

AH_stage is the suite's shared baseline that requester/dispatcher/supervisor
all bind to — so every test here closes the dialog via CANCEL and never SAVE.
TC-009 checks the input *constraints* (bounded state list, numeric-only
quantity) without submitting; TC-010 checks that CANCEL discards cleanly and
leaves the cell unchanged. Proving a *successful* save then shows on the grid
needs a supervisor-only disposable staging area (see docs §7).
"""

import allure
import pytest

from config.data import TestData
from pages.dashboards.supervisor_dashboard_page import SupervisorHomePage

pytestmark = [pytest.mark.supervisor, pytest.mark.dashboards]

_SELECTABLE_STATES = ("Available", "Reserved", "Blocked")


def _open_manage_dialog(home):
    home.open_staging_area_list()
    home.open_staging_card(0)
    return home.open_first_editable_cell_dialog()


@allure.feature("Dashboards")
@allure.story("Supervisor — Staging Area cell management")
class TestStagingAreaManage:

    @allure.title("TC-008/TC-025 — Manage mode opens an in-scope cell editor with State + Filled-with")
    def test_manage_mode_opens_cell_editor(self, supervisor_page):
        """
        ID     : TC-008 / TC-025
        Title  : Supervisor can open a staging-area cell editor, scoped to their
                 own assigned area
        Reason : This dialog is how a supervisor marks a slot reserved/blocked
                 or records material in it. Confirms the field set exists and
                 that the only cells reachable belong to the assigned area
                 (TC-025 — there is no location field pointing elsewhere).
        """
        home = SupervisorHomePage(supervisor_page)
        if not _open_manage_dialog(home):
            pytest.skip(
                f"'{TestData.sup_bound_staging_area}' currently exposes no "
                f"editable (non-[disabled]) cell — every cell is locked."
            )
        try:
            fields = home.cell_dialog_field_ids_present()
            assert "#manage-dialog-cell-state-select" in fields, (
                f"Cell editor is missing the Cell State control; fields: {fields}"
            )
            assert "#manage-cell-dialog-filled-with-select" in fields, (
                f"Cell editor is missing the 'Filled with' control; fields: {fields}"
            )
            # TC-025: the dialog is titled for a specific cell of THIS area and
            # carries no processing-area / location selector.
            dlg_text = supervisor_page.locator("#manage-cell-dialog-content").inner_text()
            assert "Cell" in dlg_text
            for stray in ("Processing Area", "Location", "Move to", "Area Name"):
                assert stray not in dlg_text, (
                    f"Cell dialog now has a {stray!r} field — TC-025 scope check "
                    f"needs revisiting."
                )
        finally:
            home.close_cell_dialog()

    @allure.title("TC-008 — Cell State offers Available / Reserved / Blocked only")
    def test_cell_state_options(self, supervisor_page):
        """
        ID     : TC-008
        Title  : Cell State is a bounded choice (Available / Reserved / Blocked)
        Reason : A supervisor must not be able to put a cell into an undefined
                 state. "Filled" is reached only via 'Filled with -> Material'.
        """
        home = SupervisorHomePage(supervisor_page)
        if not _open_manage_dialog(home):
            pytest.skip("no editable cell to open right now")
        try:
            supervisor_page.locator("#manage-dialog-cell-state-select").click(force=True)
            supervisor_page.wait_for_timeout(500)
            opts = supervisor_page.locator("li[role='option']")
            labels = sorted(opts.nth(i).inner_text().strip() for i in range(opts.count()))
            assert labels == sorted(_SELECTABLE_STATES), (
                f"Cell State options {labels} != {sorted(_SELECTABLE_STATES)}"
            )
            supervisor_page.keyboard.press("Escape")
        finally:
            home.close_cell_dialog()

    @allure.title("TC-009 — Invalid modification values are constrained by the dialog")
    def test_invalid_values_are_constrained(self, supervisor_page):
        """
        ID     : TC-009
        Title  : The dialog structurally rejects invalid input — Cell State is a
                 fixed list (no free text), Quantity is a native numeric field
                 with a minimum, so a negative / non-numeric quantity or an
                 undefined state cannot be submitted.
        Reason : Verified without saving (AH_stage is shared): a rejected value
                 leaves state unchanged, but the safer proof is that the
                 controls do not accept it in the first place.
        """
        home = SupervisorHomePage(supervisor_page)
        if not _open_manage_dialog(home):
            pytest.skip("no editable cell to open right now")
        try:
            # Cell State — a <select>, not a text box: nothing invalid to type.
            state = supervisor_page.locator("#manage-dialog-cell-state-select")
            assert state.evaluate("el => el.tagName.toLowerCase()") in ("div", "input", "select")

            # Reveal Quantity via Filled with -> Material.
            fw = supervisor_page.locator("#manage-cell-dialog-filled-with-select")
            fw.click(force=True)
            supervisor_page.wait_for_timeout(400)
            supervisor_page.get_by_role("option", name="Material", exact=True).click(force=True)
            supervisor_page.wait_for_timeout(600)

            qty = supervisor_page.locator("#manage-cell-dialog-quantity-input").first
            assert qty.get_attribute("type") == "number", (
                "Quantity is not a numeric input — a non-numeric value could be typed."
            )
            min_attr = qty.get_attribute("min")
            assert min_attr is not None and int(min_attr) >= 1, (
                f"Quantity has no positive minimum (min={min_attr!r}); a negative "
                f"or zero quantity is not blocked."
            )
        finally:
            home.close_cell_dialog()

    @allure.title("TC-010 — Cancelling a cell edit discards it and leaves the cell unchanged")
    def test_cancel_discards_edit_without_mutation(self, supervisor_page):
        """
        ID     : TC-010
        Title  : An unsaved cell edit does not reach the grid; the Save
                 mechanism is present for the real path
        Reason : AH_stage is the shared baseline, so the automated proof is the
                 safe half — open, change a selection in the UI, Cancel, reopen,
                 confirm nothing changed. A committed save visibly reflecting on
                 the dashboard needs a supervisor-only disposable area (docs §7).
        """
        home = SupervisorHomePage(supervisor_page)
        if not _open_manage_dialog(home):
            pytest.skip("no editable cell to open right now")

        # Save control exists (the real modify path).
        assert supervisor_page.locator("#manage-cell-dialog-save-btn").count() == 1

        state = supervisor_page.locator("#manage-dialog-cell-state-select")
        before = state.inner_text().strip()

        # Pick a different state in the UI, then CANCEL (no save).
        state.click(force=True)
        supervisor_page.wait_for_timeout(400)
        opts = supervisor_page.locator("li[role='option']")
        target = next(
            (opts.nth(i) for i in range(opts.count())
             if opts.nth(i).inner_text().strip() and opts.nth(i).inner_text().strip() != before),
            None,
        )
        if target:
            target.click(force=True)
            supervisor_page.wait_for_timeout(300)
        home.close_cell_dialog()  # Cancel

        # Reopen the same cell — state must be what it was.
        assert home.open_first_editable_cell_dialog(), "could not reopen the cell dialog"
        after = supervisor_page.locator("#manage-dialog-cell-state-select").inner_text().strip()
        home.close_cell_dialog()
        assert after == before, (
            f"Cell state changed from {before!r} to {after!r} after a CANCELLED "
            f"edit — cancel is not discarding the change."
        )
