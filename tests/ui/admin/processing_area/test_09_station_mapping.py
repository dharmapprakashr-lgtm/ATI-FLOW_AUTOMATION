"""Station Mapping tab: the pickup and drop stations the workflow needs.

Each mapping row takes the first available Material Type, so this module depends
on ``test_01`` (material) and ``test_06`` (machines) having run.

The two mappings are given **different Station IDs**. The workflow wizard
rejects a workflow whose pickup and drop resolve to the same physical station,
so mapping both to the first station in the list makes test_12 (workflow) unfixable.
"""

import allure
import pytest

from config.data import TestData
from config.processing_area import station_names

pytestmark = [pytest.mark.admin, pytest.mark.smoke]


@allure.feature("Admin Console")
@allure.story("Processing Area: station mapping")
class TestStationMapping:

    @allure.title("Create pickup and drop station mappings on different stations")
    def test_create_station_mappings(self, admin_page, processing_area, safe_step):
        pickup_name, drop_name = station_names()

        safe_step("Open the Station Mapping tab", processing_area.go_to_station_mapping)

        # station_id pins an exact Station ID when test_data.toml supplies one;
        # otherwise position 0 and 1 in the dropdown keep them distinct.
        for mapping_name, station_id, index in (
            (pickup_name, TestData.station_id, 0),
            (drop_name, TestData.station_id_2, 1),
        ):
            def create(n=mapping_name, sid=station_id, i=index):
                # Station Mapping is column-based (see the note in
                # create_new_area_page.py), so it needs its own delete
                # method, not AdminDashboardPage.delete_device_if_exists.
                processing_area.delete_station_mapping_if_exists(n)
                processing_area.add_station_mapping(n, station_id=sid, station_index=i)
            safe_step(f"Create station mapping '{mapping_name}'", create)

        def verify_distinct():
            chosen = processing_area.selected_station_ids
            assert chosen.get(pickup_name) != chosen.get(drop_name), (
                f"Both mappings were given the same Station ID "
                f"({chosen.get(pickup_name)!r}). The workflow wizard rejects a "
                f"workflow that picks up and drops at the same station."
            )
        safe_step("Pickup and drop mappings use different stations", verify_distinct)

        safe_step.assert_no_failures()
