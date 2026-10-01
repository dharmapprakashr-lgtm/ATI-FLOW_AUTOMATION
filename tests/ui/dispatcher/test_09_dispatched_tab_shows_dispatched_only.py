"""Dispatcher > Requests - DISPATCHED tab.

Verified live 2026-08-28: the DISPATCHED tab shows only rows whose Status is
"Dispatched", and those rows have no "Dispatch" affordance in the Decision
column (the action is already done - the Decision cell is empty).
"""

import allure
import pytest

from pages.dashboards.dispatcher_dashboard_page import DispatcherHomePage

pytestmark = [pytest.mark.dispatcher, pytest.mark.smoke]


@allure.title("DISPATCHED tab shows only dispatched rows with no further Dispatch action")
def test_dispatched_tab_shows_dispatched_only(dispatcher_page):
    home = DispatcherHomePage(dispatcher_page)

    with allure.step("Switch to the DISPATCHED tab"):
        home.select_tab("Dispatched")
        assert home.active_tab() == "dispatched"

    statuses = home.all_row_statuses()
    if not statuses:
        assert home.is_empty_state()
        pytest.skip("Default station has no dispatched requests right now.")

    with allure.step("Every row is 'Dispatched'"):
        assert set(statuses) == {"Dispatched"}, (
            f"DISPATCHED tab shows other statuses: {sorted(set(statuses))}"
        )

    with allure.step("Dispatched rows expose no actionable 'Dispatch' control"):
        for rid in home.row_ids():
            assert not home.has_dispatch_action(rid), (
                f"Dispatched row {rid} still shows a 'Dispatch' control"
            )
