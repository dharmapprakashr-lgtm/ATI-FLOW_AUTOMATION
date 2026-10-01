"""Supervisor — Staging Area screen, the card list (/stagingArea).

Manual test cases covered:
  TC-001  Dropdown/list shows only assigned staging areas
  TC-002  Unassigned staging areas are excluded
  TC-011  Empty/default state is sane (no crash, no blank)
  TC-012  Switching between two assigned staging areas refreshes all data

Confirmed live 2026-09-07: the supervisor's Staging Area screen reuses the
requester's card component (#staging-area-list-admin-card-*). There is no
free-standing "staging area dropdown"; the list of cards *is* the scoped set.
The supervisor device is bound to a single staging area (AH_stage), so it
renders exactly one card and TC-012 self-skips (nothing to switch to).
"""

import allure
import pytest

from config.data import TestData
from pages.dashboards.supervisor_dashboard_page import SupervisorHomePage

pytestmark = [pytest.mark.supervisor, pytest.mark.dashboards]


def _bound_staging_areas():
    value = TestData.sup_bound_staging_area
    return list(value) if isinstance(value, (list, tuple)) else [value]


@allure.feature("Dashboards")
@allure.story("Supervisor — Staging Area monitoring")
class TestStagingAreaList:

    @allure.title("TC-001/TC-002 — Staging Area list shows only this supervisor's assigned areas")
    @pytest.mark.smoke
    def test_list_shows_only_assigned_staging_areas(self, supervisor_page):
        """
        ID     : TC-001 / TC-002
        Title  : Only assigned staging areas are listed; unassigned ones excluded
        Reason : The supervisor monitors a defined slice of the floor. An
                 unassigned area appearing here is a scope/authorisation leak;
                 a missing assigned one blinds them to their own area.
        """
        home = SupervisorHomePage(supervisor_page)
        home.open_staging_area_list()
        expected = _bound_staging_areas()

        titles = home.staging_card_titles()
        assert sorted(titles) == sorted(expected), (
            f"Staging Area cards {sorted(titles)} != assigned staging areas "
            f"{sorted(expected)}."
        )

    @allure.title("TC-001 — The assigned staging area card shows its real grid size")
    def test_assigned_card_shows_grid_size(self, supervisor_page):
        """
        ID     : TC-001
        Title  : Assigned staging area card renders with its Fleet Manager grid size
        Reason : A card that renders a name but no grid/occupancy data is not
                 usable for monitoring.
        """
        home = SupervisorHomePage(supervisor_page)
        home.open_staging_area_list()

        assert home.staging_card_count() >= 1
        assert home.staging_card_title(0) == _bound_staging_areas()[0]
        assert home.staging_card_subtitle(0) == TestData.sup_staging_grid_size
        assert "Utilised cells" in home.staging_card_utilised_text(0)

    @allure.title("TC-011 — Staging Area list renders a state, never a blank crash")
    def test_list_never_blank_or_errored(self, supervisor_page):
        """
        ID     : TC-011
        Title  : Staging Area list shows a real state (cards, or a clear empty
                 message) — never a blank page or an error
        Reason : Manual note flags the "no areas assigned" path as needing a
                 graceful empty state. This supervisor has an assignment, so we
                 assert the populated path is graceful; the zero-assignment
                 path needs a second device to prove (documented, not faked).
        """
        home = SupervisorHomePage(supervisor_page)
        home.open_staging_area_list()
        body = supervisor_page.locator("body").inner_text().lower()
        assert "staging area" in body
        assert not any(w in body for w in ("something went wrong", "unhandled", "traceback")), (
            "Staging Area screen shows an error surface."
        )

    @allure.title("TC-012 — Switching between two assigned staging areas refreshes the view")
    def test_switching_staging_areas_refreshes(self, supervisor_page):
        """
        ID     : TC-012
        Title  : Switching staging areas fully refreshes materials / reserved /
                 in-transit / notifications with no stale data
        Reason : Carrying Area A's numbers into Area B's view is a decision-
                 making hazard on the floor.
        """
        home = SupervisorHomePage(supervisor_page)
        home.open_staging_area_list()
        if home.staging_card_count() < 2:
            pytest.skip(
                f"Supervisor device '{TestData.sup_device_name}' is bound to a "
                f"single staging area ({home.staging_card_titles()}) — nothing "
                f"to switch to. Bind it to 2+ staging areas in Execution Source "
                f"Config to enable this case."
            )

        home.open_staging_card(0)
        first_title = home.staging_detail_title()
        supervisor_page.go_back()
        home.open_staging_area_list()
        home.open_staging_card(1)
        second_title = home.staging_detail_title()
        assert first_title != second_title, (
            "Opening the second staging area card still shows the first area's "
            "detail — the view did not refresh."
        )
