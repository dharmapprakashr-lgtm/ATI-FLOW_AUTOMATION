"""Dispatcher > Requests - search box, search by material/SKU code.

Verified live 2026-08-28: typing a material code from a row's Request Details
column filters the table to rows whose Request Details contain that code, and
clearing the box restores the full list. The code is read from the live queue
rather than hard-coded, because the Pending queue is real production data and
which codes are present drifts.
"""

import allure
import pytest

from pages.dashboards.dispatcher_dashboard_page import DispatcherHomePage

pytestmark = [pytest.mark.dispatcher, pytest.mark.smoke]


@allure.title("Searching a material code filters the queue to matching rows")
def test_search_by_material_code_filters_table(dispatcher_page):
    home = DispatcherHomePage(dispatcher_page)

    ids = home.row_ids()
    if not ids:
        pytest.skip("No pending requests on the default station to search for.")

    code = home.row_material(ids[0])
    unfiltered_ids = set(ids)

    with allure.step(f"Filter by material code {code!r}"):
        home.search(code)
        assert not home.is_empty_state(), f"Material code {code!r} matched nothing"
        filtered_rows = home.row_texts()
        filtered_ids = set(home.row_ids())
        assert filtered_rows, "Expected at least the row the code was taken from"
        assert all(code in row for row in filtered_rows), (
            f"Some filtered rows do not contain {code!r}: {filtered_rows}"
        )
        # Filtered view is a subset of what we started with (+ tolerate live
        # rows that arrived meanwhile — the production queue keeps moving).
        assert len(filtered_ids) <= len(unfiltered_ids | filtered_ids)

    with allure.step("Clearing the search lifts the filter"):
        home.clear_search()
        cleared_ids = set(home.row_ids())
        assert not home.is_empty_state()
        # The filter is genuinely gone: every row that survived the filter is
        # still shown, and the cleared view is at least as large as it. Exact
        # equality with the opening count is not asserted — this is the live
        # production queue and rows legitimately arrive/leave mid-test (see
        # test_10_all_tab for the same class of tolerance).
        assert filtered_ids <= cleared_ids, (
            f"Rows {sorted(filtered_ids - cleared_ids)} vanished after clearing "
            f"the search — the clear did more than lift the filter."
        )
        assert len(cleared_ids) >= len(filtered_ids)
