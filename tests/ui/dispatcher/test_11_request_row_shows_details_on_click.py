"""Dispatcher > Requests - row detail.

The original scaffold expected a click to expand a row into a detail view.
Verified live 2026-08-28: there is no expand interaction - every field is
already rendered inline in the row, each in its own stably-id'd element:

    #approvals-row-request-id-<ID>        ID No.
    #approvals-row-material-name-<ID>-0   material / SKU code
    #approvals-row-quantity-<ID>-0        "x N"
    #approvals-row-trip-time-<ID>         time-of-day
    #approvals-row-countdown-<ID>         full date + time
    #approvals-request-grid-status-cell-<ID>   Status
    #approvals-dispatch-decision-cell-<ID>     Decision (Pending rows)

So this test asserts the inline detail is complete for a row, and that
clicking the row body does not open a dialog or otherwise change the view.
"""

import allure
import pytest

from pages.dashboards.dispatcher_dashboard_page import DispatcherHomePage

pytestmark = [pytest.mark.dispatcher, pytest.mark.smoke]


@allure.title("Each request row renders its full detail inline (no click-to-expand)")
def test_request_row_shows_details_on_click(dispatcher_page):
    home = DispatcherHomePage(dispatcher_page)

    ids = home.row_ids()
    if not ids:
        pytest.skip("Default station's Pending queue is empty right now.")
    rid = ids[0]

    with allure.step(f"Row {rid} exposes every detail field inline"):
        for suffix in (
            f"approvals-row-request-id-{rid}",
            f"approvals-row-material-name-{rid}-0",
            f"approvals-row-quantity-{rid}-0",
            f"approvals-row-trip-time-{rid}",
            f"approvals-row-countdown-{rid}",
            f"approvals-request-grid-status-cell-{rid}",
        ):
            el = dispatcher_page.locator(f"#{suffix}")
            assert el.count() == 1 and el.first.inner_text().strip(), (
                f"Row detail element #{suffix} missing or empty"
            )
        assert home.has_dispatch_action(rid)

    with allure.step("Clicking the row body does not open a dialog / change the view"):
        rows_before = home.row_texts()
        dispatcher_page.locator(f"#approvals-request-grid-row-{rid}").click()
        dispatcher_page.wait_for_timeout(800)
        assert dispatcher_page.get_by_role("dialog").count() == 0, (
            "A dialog opened on row click - the app grew an expand interaction; "
            "update this test."
        )
        assert home.row_texts() == rows_before
