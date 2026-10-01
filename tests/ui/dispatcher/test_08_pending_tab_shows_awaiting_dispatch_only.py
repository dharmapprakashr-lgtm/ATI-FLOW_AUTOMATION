"""Dispatcher > Requests - PENDING tab (default).

Verified live 2026-08-28: on load the PENDING tab is the selected tab and
every visible row has Status = "Awaiting Dispatch". (If the station's queue is
momentarily empty the test still confirms the tab is active and the empty
state - not stale Dispatched/Cancelled rows - is shown.)
"""

import allure
import pytest

from pages.dashboards.dispatcher_dashboard_page import DispatcherHomePage

pytestmark = [pytest.mark.dispatcher, pytest.mark.smoke]


@allure.title("PENDING tab is active on load and only shows 'Awaiting Dispatch' rows")
def test_pending_tab_shows_awaiting_dispatch_only(dispatcher_page):
    home = DispatcherHomePage(dispatcher_page)

    with allure.step("PENDING is the active tab"):
        assert home.active_tab() == "pending"

    statuses = home.all_row_statuses()
    if not statuses:
        assert home.is_empty_state()
        pytest.skip("Default station's Pending queue is empty right now.")

    with allure.step("Every row is 'Awaiting Dispatch'"):
        assert set(statuses) == {"Awaiting Dispatch"}, (
            f"PENDING tab shows non-pending statuses: {sorted(set(statuses))}"
        )

    with allure.step("Every pending row also carries an actionable Dispatch control"):
        for rid in home.row_ids():
            assert home.has_dispatch_action(rid), (
                f"Pending row {rid} has no Dispatch control in its Decision cell"
            )
