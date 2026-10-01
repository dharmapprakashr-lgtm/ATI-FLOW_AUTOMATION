"""Requester > Request History - Newest/Oldest First sort filter."""

import re

import allure
import pytest

from config.data import TestData
from pages.dashboards.requester_dashboard_page import RequesterHomePage

pytestmark = [pytest.mark.requester, pytest.mark.smoke]


def _numeric_ids(req_ids):
    """"Req-471" -> 471, for order comparison."""
    return [int(re.match(r"Req-(\d+)", r).group(1)) for r in req_ids]


@allure.title("Request History sort control actually reorders the table")
def test_request_history_sort_filter(requester_page):
    """Confirmed live 2026-08-26: the machine's Request History has real,
    pre-existing rows (25+ across this session, e.g. from prior e2e runs
    against this bound machine) - enough to verify actual reordering, not
    just that the control's label changes. This history is real and live
    (a new Req-NNN appeared mid-run during development of this test), so
    assertions check the *sort property* (monotonic id direction) rather
    than exact row identity, which can't be pinned down between two reads.

    "Newest First" is the default. Switching to "Oldest First" changes which
    page-1 rows are shown (different 10 of the total) and their Req-NNN ids
    run in the opposite numeric direction, since ids increment with request
    creation time."""
    home = RequesterHomePage(requester_page)
    home.request_history_nav.click()
    requester_page.locator("tbody tr").first.wait_for(state="visible", timeout=15000)

    with allure.step("Default is Newest First, ids strictly decreasing"):
        assert home.history_sort_button.inner_text().strip() == "Newest First"
        newest_first_ids = _numeric_ids(home.request_history_row_ids())
        assert len(newest_first_ids) > 1, "Need at least 2 rows to prove an order"
        assert newest_first_ids == sorted(newest_first_ids, reverse=True)

    with allure.step("Switching to Oldest First reverses the direction"):
        home.set_history_sort("Oldest First")
        assert home.history_sort_button.inner_text().strip() == "Oldest First"
        oldest_first_ids = _numeric_ids(home.request_history_row_ids())
        assert len(oldest_first_ids) > 1
        assert oldest_first_ids == sorted(oldest_first_ids)

    with allure.step("The two sorts actually show different rows, not a no-op"):
        assert newest_first_ids != oldest_first_ids

    with allure.step("Switching back to Newest First restores descending order"):
        # Not asserting exact row identity against the first read: this is
        # real, live history, and a new request can legitimately land
        # between the two reads (confirmed live during this test's own
        # development).
        home.set_history_sort("Newest First")
        assert home.history_sort_button.inner_text().strip() == "Newest First"
        restored_ids = _numeric_ids(home.request_history_row_ids())
        assert restored_ids == sorted(restored_ids, reverse=True)


@allure.title("Request History search box filters by component/SKU code")
def test_search_requester_history(requester_page):
    """Confirmed live 2026-08-26: despite its position next to the sort
    control, this box searches by component (SKU) code, not by the Req-NNN
    ticket id - its own placeholder says "Search component ID...", and a
    request-id search ("Req-472") legitimately returns 0 rows. A known
    live component code (DTE15A0666, the same sub-SKU used throughout the
    Make New Request wizard tests - see config/test_data.toml
    [requester_request_material]) returns every historical row containing
    it; a non-matching term returns none; clearing restores the full list."""
    home = RequesterHomePage(requester_page)
    home.request_history_nav.click()
    requester_page.locator("tbody tr").first.wait_for(state="visible", timeout=15000)

    unfiltered_ids = home.request_history_row_ids()
    assert len(unfiltered_ids) > 0

    with allure.step("Searching a request id (not a component code) matches nothing"):
        home.search_by_material_code(unfiltered_ids[0])
        assert home.request_history_row_ids() == []

    with allure.step("Searching a known live component code filters to matching rows"):
        home.search_by_material_code(TestData.req_request_sub_sku_code)
        filtered_rows = home.request_history_row_texts()
        print("FILTERED ROWS:", filtered_rows)
        assert len(filtered_rows) > 0
        assert all(TestData.req_request_sub_sku_code in row for row in filtered_rows)

    with allure.step("A non-matching term returns no rows"):
        home.search_by_material_code("zzz_definitely_no_match_zzz")
        assert home.request_history_row_ids() == []

    with allure.step("Clearing the search restores the unfiltered list"):
        home.search_by_material_code("")
        assert len(home.request_history_row_ids()) > 0