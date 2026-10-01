"""Supervisor — sidebar Processing Area selector (#operator-sidebar-supervisor-area-select).

Manual test cases covered:
  TC-013  Dropdown shows only assigned processing areas
  TC-014  Dropdown excludes unassigned processing areas
  TC-011  When nothing is explicitly chosen the supervisor's scope is their
          assigned area(s), not "everything" and not an error state

Confirmed live 2026-09-07: the selector opens to a <li role="option"> list
that is EXACTLY the processing area(s) bound to this supervisor device in
Execution Source Config — config/test_data.toml [devices]
supervisor_processing_areas — and nothing else. The device is currently bound
to a single area. WIP table switching is deferred to
docs/WIP_INVENTORY_TEST_CASES.md.
"""

import allure
import pytest

from config.data import TestData
from pages.dashboards.supervisor_dashboard_page import SupervisorHomePage

pytestmark = [pytest.mark.supervisor, pytest.mark.dashboards]


def _bound_areas():
    value = TestData.sup_bound_processing_area
    return list(value) if isinstance(value, (list, tuple)) else [value]


@allure.feature("Dashboards")
@allure.story("Supervisor — Processing Area scope")
class TestProcessingAreaSelector:

    @allure.title("TC-013/TC-014 — PA selector lists only this supervisor's assigned areas")
    def test_dropdown_lists_only_assigned_processing_areas(self, supervisor_page):
        """
        ID     : TC-013 / TC-014
        Title  : Processing Area dropdown shows only assigned areas, excludes
                 every unassigned one
        Reason : The supervisor's whole view is scoped by this selector. If it
                 offered an area they are not responsible for, they could read
                 (and, on the staging screen, alter) another team's floor.
        """
        home = SupervisorHomePage(supervisor_page)
        expected = _bound_areas()

        options = home.open_processing_area_dropdown()
        home.close_dropdown()

        assert sorted(options) == sorted(expected), (
            f"PA selector options {sorted(options)} != configured bound areas "
            f"{sorted(expected)} — the selector is not scoped to this device."
        )

    @allure.title("TC-011 — With no explicit choice the selector still shows the assigned area")
    def test_default_selection_is_the_assigned_area(self, supervisor_page):
        """
        ID     : TC-011
        Title  : Default Processing Area scope is the assigned area, not blank
                 and not an error
        Reason : Manual observation: "When no staging area is selected we
                 consider it all, and show all the staging areas. But if a
                 particular area is selected we show only the selected ones."
                 For a supervisor bound to exactly one area, that resolves to
                 that one area being pre-selected — never an empty/error state.
        """
        home = SupervisorHomePage(supervisor_page)
        shown = home.bound_processing_area_text()
        assert shown in _bound_areas(), (
            f"PA selector shows {shown!r} by default, which is not one of the "
            f"assigned areas {_bound_areas()}."
        )
        assert shown and shown.lower() not in ("", "select", "none"), (
            "PA selector rendered a blank / placeholder default instead of the "
            "supervisor's assigned area."
        )
