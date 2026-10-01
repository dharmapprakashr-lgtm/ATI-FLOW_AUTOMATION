"""Requester - Machine dropdown (left sidebar)."""

import pytest

pytestmark = [pytest.mark.requester, pytest.mark.smoke]


@pytest.mark.skip(
    reason="Confirmed via config/test_data.toml: requester_bound_machines is "
           "a single scalar value ('consuption_machine_45'), not a list - "
           "the mohit_requester device is bound to exactly one machine. There "
           "is no second machine to switch to, so this scenario cannot be "
           "exercised against the current provisioning. Would need the "
           "requester device rebound to two+ machines in admin (Execution "
           "Source Config) before this test has anything real to assert."
)
def test_machine_dropdown_switches_context(requester_page):
    """Selecting a different machine in the Machine dropdown updates the
    breadcrumb and reloads the wizard scoped to that machine."""
    # requester_page.get_by_role("combobox", name="Machine").select_option(label="temp_machine2")
    # expect(requester_page.get_by_text("temp_machine2")).to_be_visible()
    pass
