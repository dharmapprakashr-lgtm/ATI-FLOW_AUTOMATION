"""
Containers tests — TC_PA_017 to TC_PA_020.

STATUS (updated Aug 11, from a full Add-to-Save recording):
TC_PA_018 and TC_PA_019 are now real, confirmed tests. TC_PA_017 uses a
best-effort ARIA row role (unconfirmed). TC_PA_020 still needs a recording.
"""

import pytest
from playwright.sync_api import expect


@pytest.mark.containers
@pytest.mark.p0
@pytest.mark.skip(reason="Table row selector unconfirmed — using best-effort ARIA row role, not yet validated against real data")
def test_tc_pa_017_table_displays_correct_columns_and_data(containers_page):
    """Verify Containers tab displays correct table columns and data."""
    pass


@pytest.mark.containers
@pytest.mark.p0
def test_tc_pa_018_add_new_container(containers_page):
    """
    Verify adding a new container with required fields.
    CONFIRMED (Aug 11): full flow through Save. Note there is NO separate
    Container ID field in the actual build — SPEC MISMATCH vs the ticket,
    which lists "Container ID *" as mandatory. The "01"-placeholder field
    is confirmed to be Qty, not Container ID.
    """
    containers_page.add_container(
        c_type="Trolley",
        c_subtype="Standard",
        length="120",
        width="80",
        height="150",
        hitch_length="30",
        qty="2",
    )


@pytest.mark.containers
@pytest.mark.p0
def test_tc_pa_018b_add_container_modal_opens_with_confirmed_fields(containers_page):
    """Partial coverage: confirms the Add Container modal opens and fields are fillable, without saving."""
    containers_page.open_add_modal()
    containers_page.select_container_type("Trolley")
    containers_page.fill_subtype("Standard")
    containers_page.fill_dimensions(length="120", width="80", height="150", hitch_length="30")
    containers_page.cancel_modal()


@pytest.mark.containers
@pytest.mark.p0
def test_tc_pa_019_validation_missing_mandatory_fields(containers_page):
    """
    Verify validation when mandatory container fields are missing.
    CONFIRMED BEHAVIORALLY (Aug 11): clicking Save with everything blank
    does not close the modal. No specific error-message selector confirmed
    yet — this checks the modal staying open as the validation signal.
    """
    containers_page.attempt_save_missing_mandatory_fields()
    containers_page.assert_validation_blocked()
    containers_page.cancel_modal()


@pytest.mark.containers
@pytest.mark.p0
@pytest.mark.parametrize("c_type", ["Trolley", "Pallet", "Bin"])
def test_tc_pa_018_add_container_by_type(containers_page, c_type):
    """
    Confirms all three container types work through Save with randomized
    values, not just Trolley (which every earlier test used).
    """
    import random
    containers_page.add_container(
        c_type=c_type,
        c_subtype=f"AutoType-{c_type}-{random.randint(1000, 9999)}",
        length=str(random.randint(50, 300)),
        width=str(random.randint(20, 150)),
        height=str(random.randint(50, 250)),
        hitch_length=str(random.randint(5, 50)),
        qty=str(random.randint(1, 20)),
    )


@pytest.mark.containers
@pytest.mark.p1
@pytest.mark.skip(reason="Export CSV button interaction not yet captured in a recording")
def test_tc_pa_020_export_csv(containers_page):
    """Verify Export CSV functionality."""
    pass
