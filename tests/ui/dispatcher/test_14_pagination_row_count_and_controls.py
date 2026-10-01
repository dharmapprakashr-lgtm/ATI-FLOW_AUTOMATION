"""Dispatcher > Requests - pagination footer (#approvals-request-grid-pagination).

Verified live 2026-08-28: a custom footer with a Rows-per-page <select>
(5 / 10 / 20 / 50), a "x-y of z" range label
(#approvals-request-grid-pagination-range), and Prev / Next icon buttons
(#...-prev / #...-next) that carry the real `disabled` attribute on the first
/ last page. Exercised on the ALL tab, which has the most rows.

Note: the "of z" total settles a beat after a tab switch / page-size change
(it was briefly "of 20" before resolving to "of 33"), so this test waits for
it to stabilise and never asserts the total is constant across reads - only
that the window moves correctly and the edges disable the right arrow.
"""

import re

import allure
import pytest

from pages.dashboards.dispatcher_dashboard_page import DispatcherHomePage

pytestmark = [pytest.mark.dispatcher, pytest.mark.smoke]

RANGE_RE = re.compile(r"(\d+)\s*[–-]\s*(\d+)\s+of\s+(\d+)")


def _range(home):
    text = home.pagination_range_text()
    m = RANGE_RE.search(text)
    assert m, f"Unparseable pagination range: {text!r}"
    return int(m.group(1)), int(m.group(2)), int(m.group(3))


def _settled_range(home, tries=8):
    """Read the range once it stops changing between polls."""
    prev = None
    for _ in range(tries):
        cur = _range(home)
        if cur == prev:
            return cur
        prev = cur
        home.page.wait_for_timeout(600)
    return prev


@allure.title("Pagination range label and Prev/Next enabled-state are accurate")
def test_pagination_row_count_and_controls(dispatcher_page):
    home = DispatcherHomePage(dispatcher_page)
    home.select_tab("All")

    with allure.step("Page 1 at 10 rows/page: range and row count agree, Prev disabled"):
        home.set_rows_per_page(10)
        x, y, z = _settled_range(home)
        if z == 0:
            pytest.skip("ALL tab is empty on the default station right now.")
        assert x == 1
        assert y == min(10, z)
        assert home.row_count() == y - x + 1
        assert home.prev_disabled(), "Prev should be disabled on the first page"
        assert home.next_disabled() == (z <= y)

    if z > 10:
        with allure.step("Next advances the 10-row window; Prev becomes enabled"):
            home.pagination_next.click()
            dispatcher_page.wait_for_timeout(900)
            x2, y2, _z2 = _range(home)
            assert x2 == 11
            assert y2 >= x2
            assert home.row_count() == y2 - x2 + 1
            assert not home.prev_disabled()

        with allure.step("Paging to the end lands on a full-to-total last page, Next disabled"):
            guard = 0
            while not home.next_disabled() and guard < 30:
                home.pagination_next.click()
                dispatcher_page.wait_for_timeout(700)
                guard += 1
            xl, yl, zl = _settled_range(home)
            assert yl == zl, f"Last page should end at the total: {xl}-{yl} of {zl}"
            assert home.row_count() == yl - xl + 1
            assert home.next_disabled()

    with allure.step("A page size that covers everything disables both arrows"):
        home.set_rows_per_page(50)
        x3, y3, z3 = _settled_range(home)
        if z3 <= 50:
            assert x3 == 1 and y3 == z3
            assert home.prev_disabled() and home.next_disabled()
