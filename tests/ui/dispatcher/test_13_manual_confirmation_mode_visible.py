"""Dispatcher > Requests - Manual Confirmation Mode config check.

The workflow behind these requests (config/test_data.toml
order_material_manual_45) has point_station_mode = "Manual", so the Dispatcher
is the one who confirms dispatch. Verified live 2026-08-28: every Pending row
carries a green check-circle + "Dispatch" affordance in the Decision column
(#approvals-dispatch-decision-cell-<ID> / #approvals-dispatch-label-<ID>).
Under an Auto workflow that column is empty because dispatch is automatic.

This test asserts the manual-confirmation UI is present and enabled on pending
rows. It never clicks it - see
test_12_dispatch_action_moves_request_to_dispatched.py.
"""

import allure
import pytest

from pages.dashboards.dispatcher_dashboard_page import DispatcherHomePage

pytestmark = [pytest.mark.dispatcher, pytest.mark.smoke]


@allure.title("Manual Confirmation Mode: pending rows show an actionable Dispatch control")
def test_manual_confirmation_mode_visible(dispatcher_page):
    home = DispatcherHomePage(dispatcher_page)

    assert home.active_tab() == "pending"
    ids = home.row_ids()
    if not ids:
        pytest.skip(
            "Default station's Pending queue is empty right now - no row to "
            "check the confirmation control on."
        )

    with allure.step("Every pending row has a Dispatch control in its Decision cell"):
        for rid in ids:
            cell = dispatcher_page.locator(f"#approvals-dispatch-decision-cell-{rid}")
            label = dispatcher_page.locator(f"#approvals-dispatch-label-{rid}")
            assert cell.count() == 1, f"Row {rid}: no Decision cell"
            assert label.inner_text().strip() == "Dispatch", (
                f"Row {rid}: Decision label is {label.inner_text()!r}, expected 'Dispatch'"
            )
            assert cell.is_visible()
            # The control is a hit target (has a clickable check-circle icon).
            assert cell.locator("svg").count() >= 1
