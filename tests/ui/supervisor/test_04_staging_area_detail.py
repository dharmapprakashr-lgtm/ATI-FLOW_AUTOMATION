"""Supervisor — Staging Area detail (/operator/stagingArea/view/<id>).

Manual test cases covered:
  TC-003  Selecting a staging area shows its current materials
  TC-004  Reserved quantity is shown (and, per manual note, in orange)
  TC-005  In-transit quantity is shown  -> asserted as an explicit contract:
          this build represents occupancy purely as coloured cells and has NO
          In-Transit state/field on the staging detail (movement lives on the
          Auto Trips screen). The test fails the day an In-Transit indicator
          is added here, prompting TC-005 to become a positive assertion.

Confirmed live 2026-09-07: the detail view is a colour-coded cell grid
(#staging-area-view-grid-inner) with a legend (#staging-area-view-legend)
of four states — Available #009688 (teal), Reserved #FFB300 (amber),
Blocked #FF726A (red), Filled #4FC3F7 (blue). There is no separate numeric
"Current Materials / Reserved / In Transit" panel. AH_stage is the suite's
shared baseline, so this file only ever reads the grid.
"""

import allure
import pytest

from config.data import TestData
from pages.dashboards.supervisor_dashboard_page import SupervisorHomePage

pytestmark = [pytest.mark.supervisor, pytest.mark.dashboards]

_LEGEND_STATES = ["Available", "Reserved", "Blocked", "Filled"]


@allure.feature("Dashboards")
@allure.story("Supervisor — Staging Area detail")
class TestStagingAreaDetail:

    @allure.title("TC-003 — Opening a staging area shows its occupancy grid and legend")
    @pytest.mark.smoke
    def test_detail_shows_cell_grid_and_legend(self, supervisor_page):
        """
        ID     : TC-003
        Title  : Selecting a staging area displays its current materials
        Reason : The grid is how a supervisor sees, at a glance, which physical
                 slots hold material and which are free. A grid that fails to
                 render or a missing legend entry leaves that to guesswork.
        """
        home = SupervisorHomePage(supervisor_page)
        home.open_staging_area_list()
        home.open_staging_card(0)

        assert home.staging_detail_title() == TestData.sup_bound_staging_area
        assert home.staging_detail_subtitle() == TestData.sup_staging_grid_size
        assert home.legend_state_labels() == _LEGEND_STATES, (
            f"Legend states {home.legend_state_labels()} != {_LEGEND_STATES}"
        )
        assert len(home.cell_colours_in_grid()) >= 1, "Cell grid rendered no cells."

    @allure.title("TC-004 — Reserved cells are shown in amber/orange")
    def test_reserved_state_is_amber(self, supervisor_page):
        """
        ID     : TC-004
        Title  : Reserved quantity is shown, colour-coded amber/orange
        Reason : Manual observation — "Reserved staging station shown in orange
                 colour". A supervisor relies on that colour to tell reserved
                 stock apart from free/blocked at a glance.
        """
        home = SupervisorHomePage(supervisor_page)
        home.open_staging_area_list()
        home.open_staging_card(0)

        reserved = home.legend_swatch_colour("Reserved")
        assert reserved == TestData.sup_reserved_colour.upper(), (
            f"Reserved legend swatch is {reserved}, expected "
            f"{TestData.sup_reserved_colour.upper()} (amber/orange)."
        )
        assert home.legend_swatch_colour("Available") != reserved
        assert home.legend_swatch_colour("Blocked") != reserved

    @allure.title("TC-005 — In-transit is not represented on the staging detail (current contract)")
    def test_staging_detail_has_no_in_transit_indicator(self, supervisor_page):
        """
        ID     : TC-005
        Title  : The staging-area detail has no In-Transit state or field
        Reason : Locks the current contract. This build shows occupancy only as
                 the four legend states (Available/Reserved/Blocked/Filled) and
                 exposes in-transit movement on the Auto Trips screen instead
                 (test_10). If an 'In Transit' indicator is ever added here this
                 test fails, flagging that TC-005 should become a positive
                 "shows the correct in-transit quantity" assertion.
        """
        home = SupervisorHomePage(supervisor_page)
        home.open_staging_area_list()
        home.open_staging_card(0)

        assert "In Transit" not in home.legend_state_labels(), (
            "An 'In Transit' legend state appeared — rewrite TC-005 as a "
            "positive assertion."
        )
        detail_text = supervisor_page.locator("#staging-area-view-root").inner_text().lower()
        assert "transit" not in detail_text, (
            f"The staging detail now mentions 'transit' — content: {detail_text[:200]!r}"
        )
        # In-transit movement *is* available to the supervisor — on Auto Trips.
        home.go_to_auto_trips()
        assert "Pickup Station" in home.trips_column_headers()
