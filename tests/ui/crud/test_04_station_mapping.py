"""Station Mapping CRUD lifecycle test — Part 3d (CRUD).

Uses a dedicated throwaway record from [station_mapping_crud] in test_data.toml —
never touches the shared baseline mappings (pick / drop).

TC_STM_CRUD  Station mapping create → verify → delete lifecycle
"""

import allure
import pytest

from config.processing_area import station_mapping_crud_spec

pytestmark = [pytest.mark.admin, pytest.mark.admin_pa, pytest.mark.crud]


@allure.feature("Admin Console")
@allure.story("Processing Area: station mapping CRUD lifecycle")
class TestStationMappingCrud:
    """TC_STM_CRUD"""

    @allure.title("TC_STM_CRUD — Station mapping create and delete lifecycle")
    def test_station_mapping_create_and_delete(self, admin_page, processing_area, safe_step):
        """
        ID     : TC_STM_CRUD
        Title  : Station mapping create → verify → delete lifecycle
        Reason : Confirms the full lifecycle works end-to-end using a dedicated
                 throwaway record from [station_mapping_crud] in test_data.toml.
                 The shared baseline mappings (pick/drop) are never touched.

        Uses ProcessingAreaPage's column-based delete/verify helpers, not
        AdminDashboardPage.delete_device_if_exists - Station Mapping renders
        as a column header (Type | Production Unit | <mapping name>), not a
        table row, so the row-based helper both targets the wrong element and
        can false-positive on an unrelated row whose Station ID value happens
        to contain this mapping's name as a substring (see the note in
        create_new_area_page.py's Station Mapping CRUD section - this is what
        left a "crud_pick" column stuck live until it was found and fixed).
        """
        name, _ = station_mapping_crud_spec()

        safe_step("Open Station Mapping tab", processing_area.go_to_station_mapping)

        def create():
            processing_area.delete_station_mapping_if_exists(name)
            # No station_id pinned: this throwaway mapping doesn't need to
            # avoid colliding with another mapping's station (unlike test_03's
            # pickup/drop pair), so the first offered Station ID is fine and
            # avoids depending on a guessed value actually existing live.
            processing_area.add_station_mapping(name)
        safe_step(f"Create station mapping '{name}'", create)

        def verify_exists():
            processing_area.verify_station_mapping_exists(name)
        safe_step(f"Verify station mapping '{name}' is present in the table", verify_exists)

        def delete_it():
            result = processing_area.delete_station_mapping_if_exists(name)
            assert result, f"Expected to delete '{name}' but it was not found."
        safe_step(f"Delete station mapping '{name}'", delete_it)

        safe_step.assert_no_failures()
