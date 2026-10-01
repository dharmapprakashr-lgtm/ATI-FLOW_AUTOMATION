"""Dispatcher > Requests - ALL tab.

The original scaffold expected ALL count == Pending count + Dispatched count.
Verified live 2026-08-28 that is too narrow: the ALL tab is a superset of
*every* status - Pending, Dispatched **and** Cancelled (33 rows total vs. 3
pending + 1 dispatched on that day). So this test asserts the containment that
actually holds: every Pending id and every Dispatched id appears under ALL,
and ALL's total is at least their combined count.
"""

import allure
import pytest

from pages.dashboards.dispatcher_dashboard_page import DispatcherHomePage

pytestmark = [pytest.mark.dispatcher, pytest.mark.smoke]


def _all_ids_across_pages(home):
    """Collect every row id on the current tab, walking the full pagination.

    The live "All" tab holds every status (Pending + Dispatched + Cancelled +
    completed), which on a busy production queue is hundreds of rows. Bump the
    page size to the maximum first so the walk actually reaches the last page
    within the guard - at 10/page the old 25-page cap only covered 250 rows and
    silently missed anything past that.
    """
    page_sizes = home.rows_per_page_select.locator("option").evaluate_all(
        "options => options.map(option => option.value)"
    )
    supported_sizes = [int(value) for value in page_sizes if value.isdigit()]
    assert supported_sizes, "Dispatcher pagination has no numeric page-size options"
    home.set_rows_per_page(max(supported_sizes))
    seen = set(home.row_ids())
    guard = 0
    while not home.next_disabled() and guard < 60:
        home.pagination_next.click()
        home.page.wait_for_timeout(900)
        seen |= set(home.row_ids())
        guard += 1
    return seen


@allure.title("ALL tab contains every Pending and Dispatched request (plus other statuses)")
def test_all_tab_shows_union_of_both(dispatcher_page):
    home = DispatcherHomePage(dispatcher_page)

    with allure.step("Collect Pending ids"):
        home.select_tab("Pending")
        pending_ids = set(_all_ids_across_pages(home))

    with allure.step("Collect Dispatched ids"):
        home.select_tab("Dispatched")
        dispatched_ids = set(_all_ids_across_pages(home))

    if not pending_ids and not dispatched_ids:
        pytest.skip("Default station has neither pending nor dispatched requests right now.")

    with allure.step("Collect ALL ids"):
        home.select_tab("All")
        assert home.active_tab() == "all"
        all_total = home.pagination_total()
        all_ids = set(_all_ids_across_pages(home))

    with allure.step("Every Pending and Dispatched id is present under ALL"):
        missing = (pending_ids | dispatched_ids) - all_ids
        if missing:
            # This runs against the live production queue: a request can be
            # dispatched / cancelled / completed *during* the multi-page walk
            # above, so an id read on Pending/Dispatched may legitimately have
            # moved before the ALL scan reached its page. Re-scan all three
            # tabs once and only fail on an id that is STILL in Pending or
            # Dispatched and STILL absent from ALL.
            home.select_tab("Pending")
            pending_now = set(_all_ids_across_pages(home))
            home.select_tab("Dispatched")
            dispatched_now = set(_all_ids_across_pages(home))
            home.select_tab("All")
            all_now = set(_all_ids_across_pages(home))
            missing = (pending_now | dispatched_now) - all_now
            assert not missing, (
                f"ALL tab is still missing ids present in Pending/Dispatched "
                f"after a re-scan: {sorted(missing)}"
            )

    with allure.step("ALL is at least as large as Pending + Dispatched combined"):
        # Re-read on the All tab (the id walk above left us on its last page).
        home.select_tab("All")
        all_total = home.pagination_total()
        combined = len(pending_ids | dispatched_ids)
        assert all_total is None or all_total >= combined, (
            f"ALL total {all_total} < Pending+Dispatched combined {combined}"
        )
