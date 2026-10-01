"""Dispatcher > Requests - sort control ("Newest First" / "Oldest First").

Verified live 2026-08-28: the sort control is a button whose label is the
*current* state. Clicking it opens a two-item menu; choosing the other option
re-orders the table by Request Time. Row "ID No." values increment with
request-creation time, so "Newest First" == IDs descending and "Oldest First"
== IDs ascending - that is what this test asserts (robust to the live queue
gaining or losing rows between reads).
"""

import allure
import pytest

from pages.dashboards.dispatcher_dashboard_page import DispatcherHomePage

pytestmark = [pytest.mark.dispatcher, pytest.mark.smoke]


@allure.title("The sort control actually re-orders the queue by Request Time")
def test_sort_dropdown_toggles_newest_oldest(dispatcher_page):
    home = DispatcherHomePage(dispatcher_page)

    if home.row_count() < 2:
        pytest.skip(
            "Default bound station has fewer than 2 pending requests right now "
            "- nothing to prove an ordering with. This is live production data."
        )

    with allure.step("Oldest First -> IDs ascending"):
        home.set_sort("Oldest First")
        assert home.current_sort() == "Oldest First"
        oldest_first = home.row_ids()
        assert len(oldest_first) >= 2
        assert oldest_first == sorted(oldest_first), (
            f"'Oldest First' did not sort ascending by ID/time: {oldest_first}"
        )

    with allure.step("Newest First -> IDs descending"):
        home.set_sort("Newest First")
        assert home.current_sort() == "Newest First"
        newest_first = home.row_ids()
        assert newest_first == sorted(newest_first, reverse=True), (
            f"'Newest First' did not sort descending by ID/time: {newest_first}"
        )

    with allure.step("The two orders are genuinely reversed, not a no-op"):
        assert newest_first == list(reversed(oldest_first)) or set(newest_first) != set(oldest_first)
