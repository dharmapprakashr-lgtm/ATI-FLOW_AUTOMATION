"""
Staging Area tests — TC_PA_001 to TC_PA_012.

STATUS: updated to match selectors confirmed via playwright codegen +
screenshot (Aug 11). See staging_area_page.py docstring for a SPEC MISMATCH
note — the actual build's list view uses a Search box + "All Fleets"
dropdown, not the All/Active/Inactive filter tabs the ticket describes, and
no Edit/overflow icon was visible on the card. TC_PA_002 and TC_PA_003 are
skipped pending clarification from dev/product rather than assumed broken.

Update TEST_PROC_AREA and TEST_SA_NAME to real values from your environment.
"""

import pytest
from playwright.sync_api import expect

TEST_PROC_AREA = "august"   # sidebar processing area name, from recording
TEST_SA_NAME = "AH_stage"   # staging area card name, from recording


@pytest.mark.staging_area
@pytest.mark.p0
def test_tc_pa_001_card_displays_correct_details(staging_area_page):
    """
    Verify staging area cards display correct details.
    Confirmed via screenshot: name, dimensions ("1 x 4 cells"), utilised
    count ("2/4 Utilised cells") with progress bar, relative timestamp
    ("Just now").
    """
    card = staging_area_page.get_card(TEST_SA_NAME)
    expect(card).to_be_visible()
    # NOTE: dimensions/progress/timestamp text is visually confirmed but
    # not yet tied to a specific selector — they render as plain text near
    # the card heading, not in a separately labeled element. A recording
    # that inspects the card's DOM structure (not just clicks) would help
    # pin these down precisely.


@pytest.mark.staging_area
@pytest.mark.p0
@pytest.mark.skip(
    reason="SPEC MISMATCH: ticket describes Active(green)/Inactive(red) "
           "card border, but only one card observed so far (pink/magenta "
           "border) — need a second card in a different status to confirm "
           "the actual color rule, or confirm with dev/product whether "
           "this exists at all"
)
def test_tc_pa_002_active_inactive_border_indicator(staging_area_page):
    """Verify Active/Inactive status border on cards."""
    pass


@pytest.mark.staging_area
@pytest.mark.p1
@pytest.mark.skip(
    reason="SPEC MISMATCH: ticket describes All/Active/Inactive filter "
           "tabs, but actual build shows a Search box + 'All Fleets' "
           "dropdown instead (confirmed via screenshot). Needs "
           "clarification from dev/product before this test can be "
           "written meaningfully."
)
def test_tc_pa_003_filter_tabs_scope_correctly(staging_area_page):
    """Verify All/Active/Inactive filter tabs."""
    pass


@pytest.mark.staging_area
@pytest.mark.p0
def test_tc_pa_004_card_click_navigates_to_grid_view(staging_area_page):
    """Verify clicking a staging area card navigates to Grid View."""
    staging_area_page.open_grid(TEST_SA_NAME)
    expect(staging_area_page.page.get_by_role("button", name="View")).to_be_visible()
    expect(staging_area_page.page.get_by_role("button", name="Manage")).to_be_visible()


@pytest.mark.staging_area
@pytest.mark.p0
def test_tc_pa_006_view_mode_is_read_only(staging_area_page):
    """Verify View mode is read-only — no combobox should open on cell click."""
    staging_area_page.open_grid(TEST_SA_NAME)
    staging_area_page.switch_to_view_mode()
    staging_area_page.click_cell(0)
    expect(staging_area_page.page.get_by_role("combobox")).not_to_be_visible()


@pytest.mark.staging_area
@pytest.mark.p0
def test_tc_pa_007_manage_mode_allows_interaction(staging_area_page):
    """Verify Manage mode allows cell interaction — combobox opens on click."""
    staging_area_page.open_grid(TEST_SA_NAME)
    staging_area_page.switch_to_manage_mode()
    staging_area_page.click_cell(0)
    expect(staging_area_page.page.get_by_role("combobox")).to_be_visible()


@pytest.mark.staging_area
@pytest.mark.p0
def test_tc_pa_008_fill_available_cell_with_material(staging_area_page):
    """
    Verify filling an Available cell with Material details.
    Confirmed flow: category -> code -> MHE number -> Save.
    Qty/Timestamp not yet confirmed — see staging_area_page.py docstring.
    Update category/code/mhe_number to real values available in your
    environment (these were: "General", "DTE18C0253", "LT-47").
    """
    staging_area_page.open_grid(TEST_SA_NAME)
    staging_area_page.switch_to_manage_mode()
    staging_area_page.click_cell(0)
    staging_area_page.fill_material(
        category="General", code="DTE18C0253", mhe_number="LT-47"
    )
    staging_area_page.save()


@pytest.mark.staging_area
@pytest.mark.p0
def test_tc_pa_009_trolley_option_skipped_for_yokohama_dahej(staging_area_page):
    """
    Verify Trolley fill option is skipped for Yokohama Dahej project.
    NOTE: run against an environment/tenant configured as Yokohama Dahej
    for this to be meaningful. 'Trolley' as exact option text is not yet
    directly confirmed — if this fails on the text match itself (not the
    presence/absence), check the real option label first.
    """
    staging_area_page.open_grid(TEST_SA_NAME)
    staging_area_page.switch_to_manage_mode()
    staging_area_page.click_cell(0)
    assert not staging_area_page.trolley_option_visible(), (
        "Trolley fill option should not be shown for the Yokohama Dahej project"
    )


@pytest.mark.staging_area
@pytest.mark.p0
def test_tc_pa_010_block_cell(staging_area_page):
    """Verify setting a cell to Blocked state via the status combobox."""
    staging_area_page.open_grid(TEST_SA_NAME)
    staging_area_page.switch_to_manage_mode()
    staging_area_page.click_cell(0)
    staging_area_page.set_cell_status(new_state="Blocked")
    staging_area_page.save()


@pytest.mark.staging_area
@pytest.mark.p0
def test_tc_pa_011_unblock_cell(staging_area_page):
    """Verify unblocking a Blocked cell via the status combobox."""
    staging_area_page.open_grid(TEST_SA_NAME)
    staging_area_page.switch_to_manage_mode()
    staging_area_page.click_cell(0)
    staging_area_page.set_cell_status(new_state="Available")
    staging_area_page.save()


@pytest.mark.staging_area
@pytest.mark.p1
def test_tc_pa_012_utilised_count_updates_in_real_time(staging_area_page):
    """
    Verify real-time update of utilised cell count on the card.
    Confirmed real text format: "2/4 Utilised cells".
    """
    card = staging_area_page.get_card(TEST_SA_NAME)
    before = card.locator("xpath=..").inner_text()
    staging_area_page.open_grid(TEST_SA_NAME)
    staging_area_page.switch_to_manage_mode()
    staging_area_page.click_cell(0)
    staging_area_page.set_cell_status(new_state="Blocked")
    staging_area_page.save()
    staging_area_page.page.go_back()
    after = staging_area_page.get_card(TEST_SA_NAME).locator("xpath=..").inner_text()
    assert before != after, "Utilised cell count did not change after cell state update"


@pytest.mark.staging_area
@pytest.mark.p1
def test_tc_pa_013_view_filled_cell_details(staging_area_page):
    """
    Verify clicking a filled cell shows current Material/Trolley details.
    Confirmed dialog fields: Cell Location, SKU, Sub-SKU, Quantity.
    Assumes cell index 0 is already filled — adjust index/setup as needed
    for your environment (e.g. run after test_tc_pa_008).
    """
    staging_area_page.open_grid(TEST_SA_NAME)
    staging_area_page.click_cell(0)
    details = staging_area_page.view_cell_details()
    expect(details["cell_location"]).to_be_visible()
    expect(details["sku"]).to_be_visible()
    expect(details["sub_sku"]).to_be_visible()
    expect(details["quantity"]).to_be_visible()
    staging_area_page.close_details_dialog()
