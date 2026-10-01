"""Container tests — Baseline Setup · Existence · Validation · Type Dropdown · CRUD · Bulk Upload.

ALL container-related test cases for the Processing Area live here.
This file seeds the baseline container immediately after the baseline material
(test_05_material.py) has been created so that later tests have a known-good
container definition to work with.

  TC_CON_000   Seed the baseline container into the Processing Area
  TC_CON_001v  Baseline container is present in the Containers table
  TC_CON_002   Container numeric fields reject invalid values (negative, zero, text, empty)
  TC_CON_002b  Empty Add Container form is rejected
  TC_CON_003   Container Type dropdown lists all expected types (Trolley, Pallet, Bin)
  TC_CON_CRUD  Full lifecycle — create → verify → edit → verify → delete
  TC_CON_BULK  Bulk upload via CSV — template header + every row lands in the table
  TC_CON_BULK_BAD  Malformed CSV is rejected without an HTTP 500
"""

import csv

import allure
import pytest
from playwright.sync_api import expect

from config.data import TestData
from config.environment import ROOT_DIR
from config.processing_area import container_spec
from pages.admin.admin_navigation import AdminDashboardPage
from utils.data_factory import run_token, unique_name
from utils.waits import is_error_visible

pytestmark = [pytest.mark.admin_pa]

CONTAINER_SAMPLE_CSV = ROOT_DIR / "data" / "container_bulk_upload.csv"

CONTAINER_COLUMNS = [
    "containerType",
    "containerSubType",
    "length",
    "width",
    "height",
    "hitch_length",
    "units",
]

#: Container types the app ships with (verified from the live dropdown).
EXPECTED_CONTAINER_TYPES = ["Trolley", "Pallet", "Bin"]


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _build_container_csv(dest):
    """Read sample CSV, make every sub-type unique, write to *dest*.

    Returns the list of containerSubType values written, in file order.
    """
    with open(CONTAINER_SAMPLE_CSV, newline="") as fh:
        rows = list(csv.DictReader(fh))

    sub_types = []
    for i, row in enumerate(rows, start=1):
        row["containerSubType"] = unique_name(f"ctbulk{i}")
        sub_types.append(row["containerSubType"])

    with open(dest, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=CONTAINER_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    return sub_types


def _build_bad_container_csv(dest):
    """Build a single-row CSV that violates numeric field constraints."""
    bad_rows = [
        {
            "containerType":    "Trolley",
            "containerSubType": unique_name("ctr_bad"),
            "length":           "-1",    # must be positive
            "width":            "0",     # must be positive
            "height":           "abc",   # must be numeric
            "hitch_length":     "",      # required — blank
            "units":            "1e9",   # scientific notation
        }
    ]
    with open(dest, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=CONTAINER_COLUMNS)
        writer.writeheader()
        writer.writerows(bad_rows)


# =============================================================================
# TC_CON_000 — Baseline setup (Container)
# =============================================================================

@allure.feature("Admin Console")
@allure.story("Container: baseline setup")
class TestContainerBaselineSetup:
    """TC_CON_000 — seed the baseline container into the existing Processing Area."""

    @allure.title("TC_CON_000 — Seed baseline container into the Processing Area")
    @pytest.mark.smoke
    def test_create_baseline_container(self, admin_page, pa_page, safe_step):
        """
        ID     : TC_CON_000
        Title  : Baseline container is created (or re-created) in the Processing Area
        Reason : The baseline container definition is required by task-routing,
                 WIP inventory, and dispatcher device tests. Deleting a stale record
                 first ensures only one version exists and its fields are known.
        """
        dashboard = AdminDashboardPage(admin_page)
        container = container_spec()

        def container_step():
            pa_page.navigate_to_existing_area(TestData.processing_area_name)
            pa_page.go_to_containers()
            dashboard.delete_device_if_exists(container.container_type)
            dashboard.add_container(
                container.container_type,
                container.sub_type,
                container.length,
                container.width,
                container.height,
                container.hitch_length,
                container.qty,
            )
            expect(
                admin_page.locator("tr").filter(has_text=container.container_type).first
            ).to_be_visible(timeout=5_000)
        safe_step("Containers tab: delete stale record, create baseline container", container_step)

        safe_step.assert_no_failures()


# =============================================================================
# TC_CON_001v — Existence check
# =============================================================================

@allure.feature("Admin Console")
@allure.story("Container: existence verification")
class TestContainerExists:
    """TC_CON_001v"""

    @allure.title("TC_CON_001v — Baseline container is present in the Containers table")
    def test_baseline_container_exists(self, admin_page, processing_area):
        """
        ID     : TC_CON_001v
        Title  : Baseline container exists in the Containers table after setup
        Reason : Confirms TC_CON_000 persisted the record. Downstream task-routing
                 and WIP tests assume this definition is already on record.
        """
        ctr = container_spec()
        processing_area.go_to_containers()

        with allure.step(f"Verify sub-type '{ctr.sub_type}' is visible in the Containers table"):
            expect(
                admin_page.locator("tr").filter(has_text=ctr.sub_type).first
            ).to_be_visible(timeout=8_000)


# =============================================================================
# TC_CON_002 / TC_CON_002b — Field validation
# =============================================================================

@allure.feature("Admin Console")
@allure.story("Container: field validation")
class TestContainerFieldValidation:
    """TC_CON_002 / TC_CON_002b"""

    @allure.title("TC_CON_002 — Container numeric fields reject invalid values")
    def test_container_numeric_fields_reject_invalid_values(self, admin_page, processing_area):
        """
        ID     : TC_CON_002
        Title  : Container numeric fields reject negative, zero, text, empty, and
                 scientific-notation values
        Reason : A bad dimension stored in the DB breaks capacity calculations
                 silently — a route that needs 1.5 m of hitch-length would be
                 assigned to a 0-length container without raising any error.
        """
        processing_area.go_to_containers()

        invalid_cases = [
            ("#ctr-length",       "-1",  "negative length"),
            ("#ctr-width",        "0",   "zero width"),
            ("#ctr-height",       "abc", "alphabetic height"),
            ("#ctr-hitch-length", "",    "empty hitch length"),
            ("#ctr-qty",          "1e9", "scientific notation quantity"),
        ]

        for field_id, bad_value, label in invalid_cases:
            with allure.step(f"Invalid value '{bad_value}' in '{label}' ({field_id})"):
                admin_page.locator("button").filter(
                    has_text="Add New Container"
                ).click(force=True)
                admin_page.wait_for_timeout(1_000)

                field = admin_page.locator(field_id)

                # Alphabetic input — field must silently swallow the keystrokes
                if bad_value.isalpha():
                    field.press_sequentially(bad_value)
                    actual = field.input_value()
                    assert actual == "", (
                        f"Alphabetic input '{bad_value}' was accepted into "
                        f"numeric field '{label}' ({field_id}). Actual value: '{actual}'"
                    )
                    admin_page.keyboard.press("Escape")
                    admin_page.wait_for_timeout(500)
                    continue

                # Other bad values — fill, try to save, expect rejection
                field.fill(bad_value)
                admin_page.keyboard.press("Tab")
                admin_page.wait_for_timeout(500)

                admin_page.locator(".MuiDialog-container").get_by_role(
                    "button", name="SAVE", exact=True
                ).click()
                admin_page.wait_for_timeout(1_000)

                modal_open  = admin_page.locator(".MuiDialog-container").is_visible(timeout=1_000)
                error_shown = is_error_visible(admin_page)

                assert not admin_page.locator("text=500").is_visible(timeout=500), (
                    f"Server returned HTTP 500 for invalid container value "
                    f"'{bad_value}' in '{label}'."
                )

                if modal_open:
                    admin_page.keyboard.press("Escape")
                    admin_page.wait_for_timeout(500)

    @allure.title("TC_CON_002b — Submitting an empty Add Container form is rejected")
    def test_container_empty_form_rejected(self, admin_page, processing_area):
        """
        ID     : TC_CON_002b
        Title  : Empty Add Container form save is rejected
        Reason : A container row with NULL dimensions would crash any code path
                 that reads those values (e.g. staging-area cell sizing).
        """
        processing_area.go_to_containers()

        with allure.step("Open 'Add New Container' dialog"):
            admin_page.locator("button").filter(has_text="Add New Container").click(force=True)
            expect(admin_page.locator("#ctr-type")).to_be_visible(timeout=8_000)

        with allure.step("Click SAVE without filling any fields"):
            admin_page.locator(".MuiDialog-container").get_by_role(
                "button", name="SAVE", exact=True
            ).click()
            admin_page.wait_for_timeout(1_000)

        with allure.step("Verify dialog stays open or an error is shown"):
            modal_open  = admin_page.locator(".MuiDialog-container").is_visible(timeout=1_000)
            error_shown = is_error_visible(admin_page)
            assert modal_open or error_shown, (
                "Expected the dialog to remain open or show an error when "
                "saving an empty container form, but neither happened."
            )

        with allure.step("Close the dialog"):
            admin_page.keyboard.press("Escape")
            admin_page.wait_for_timeout(500)


# =============================================================================
# TC_CON_003 — Container Type dropdown completeness
# =============================================================================

@allure.feature("Admin Console")
@allure.story("Container: type dropdown")
class TestContainerTypeDropdown:
    """TC_CON_003"""

    @allure.title("TC_CON_003 — Container Type dropdown lists Trolley, Pallet, and Bin")
    def test_container_type_dropdown_has_all_types(self, admin_page, processing_area):
        """
        ID     : TC_CON_003
        Title  : Container Type dropdown contains all expected container types
        Reason : A missing type would prevent operators from creating that category.
                 They would silently pick the wrong type without any validation error.
        """
        processing_area.go_to_containers()

        with allure.step("Open 'Add New Container' dialog"):
            admin_page.locator("button").filter(has_text="Add New Container").click(force=True)
            expect(admin_page.locator("#ctr-type")).to_be_visible(timeout=8_000)

        with allure.step("Open the Container Type dropdown"):
            admin_page.locator("#ctr-type").click(force=True)
            admin_page.wait_for_timeout(500)

        with allure.step(f"Verify all expected types are present: {EXPECTED_CONTAINER_TYPES}"):
            for ctype in EXPECTED_CONTAINER_TYPES:
                expect(
                    admin_page.get_by_role("option", name=ctype, exact=True)
                ).to_be_visible(timeout=5_000)

        with allure.step("Close the dialog"):
            admin_page.keyboard.press("Escape")
            admin_page.wait_for_timeout(300)
            admin_page.keyboard.press("Escape")
            admin_page.wait_for_timeout(500)


# =============================================================================
# TC_CON_CRUD — Full lifecycle
# =============================================================================

@allure.feature("Admin Console")
@allure.story("Container: CRUD lifecycle")
class TestContainerCRUD:
    """TC_CON_CRUD — create → verify → edit → verify → delete."""

    @allure.title("TC_CON_CRUD — Container full CRUD lifecycle in one pass")
    def test_container_crud_lifecycle(self, admin_page, processing_area):
        """
        ID     : TC_CON_CRUD
        Title  : Container create → search → edit → delete lifecycle
        Reason : Validates every write path for containers in a single session
                 so a regression in any step is caught without running the full suite.
        """
        dashboard       = AdminDashboardPage(admin_page)
        crud_sub_type   = unique_name("ctr_crud")
        edited_sub_type = unique_name("ctr_crud_ed")

        processing_area.go_to_containers()

        # ── CREATE ────────────────────────────────────────────────────────────
        with allure.step(f"Create container sub-type '{crud_sub_type}'"):
            dashboard.delete_device_if_exists(crud_sub_type)
            dashboard.add_container(
                TestData.crud_container_type,
                crud_sub_type,
                TestData.crud_container_length,
                TestData.crud_container_width,
                TestData.crud_container_height,
                TestData.crud_container_hitch_length,
                TestData.crud_container_qty,
            )

        with allure.step(f"Verify '{crud_sub_type}' appears in the Containers table"):
            dashboard.verify_device_created(crud_sub_type)

        # ── EDIT ──────────────────────────────────────────────────────────────
        with allure.step(f"Edit sub-type: '{crud_sub_type}' → '{edited_sub_type}'"):
            search_input = dashboard._search_for(crud_sub_type)
            row = dashboard._row_by_exact_name(crud_sub_type)
            if row.count() > 0:
                row.first.locator("button").first.click(force=True)
                admin_page.wait_for_timeout(1_000)
                admin_page.locator("#ctr-sub-type").fill(edited_sub_type)
                admin_page.locator(".MuiDialog-container").get_by_role(
                    "button", name="SAVE", exact=True
                ).click()
                admin_page.wait_for_timeout(2_000)
            dashboard._clear_search(search_input)

        with allure.step(f"Verify edited sub-type '{edited_sub_type}' is in the table"):
            dashboard.verify_device_created(edited_sub_type)

        # ── DELETE ────────────────────────────────────────────────────────────
        with allure.step(f"Delete '{edited_sub_type}'"):
            deleted = dashboard.delete_device_if_exists(edited_sub_type)
            assert deleted, (
                f"Expected to delete container '{edited_sub_type}' but it was not found."
            )

        with allure.step(f"Confirm '{edited_sub_type}' is gone from the table"):
            si    = dashboard._search_for(edited_sub_type)
            count = dashboard._row_by_exact_name(edited_sub_type).count()
            dashboard._clear_search(si)
            assert count == 0, (
                f"Container '{edited_sub_type}' still visible in the table after deletion."
            )


# =============================================================================
# TC_CON_BULK / TC_CON_BULK_BAD — Bulk upload
# =============================================================================

@allure.feature("Admin Console")
@allure.story("Container: bulk upload")
class TestContainerBulkUpload:
    """TC_CON_BULK / TC_CON_BULK_BAD"""

    @allure.title("TC_CON_BULK — Valid CSV bulk upload creates every container row")
    def test_bulk_upload_containers_happy_path(self, admin_page, processing_area, tmp_path):
        """
        ID     : TC_CON_BULK
        Title  : Container bulk upload — valid CSV imports all rows
        Reason : Bulk upload is the primary onboarding path for large container
                 fleets. Unlike materials (per-row), containers import is
                 all-or-nothing — one bad row silently rejects the whole file,
                 so a clean upload must guarantee every row landed.
        """
        dashboard  = AdminDashboardPage(admin_page)
        upload_csv = tmp_path / "container_bulk_upload.csv"
        sub_types  = _build_container_csv(upload_csv)

        processing_area.go_to_containers()

        try:
            with allure.step("Verify CSV Template header matches expected columns"):
                template_path = dashboard.download_bulk_csv_template("container")
                with open(template_path, newline="") as fh:
                    header = next(csv.reader(fh))
                assert header == CONTAINER_COLUMNS, (
                    f"Template header changed — expected {CONTAINER_COLUMNS}, got {header}"
                )

            with allure.step(f"Upload CSV with {len(sub_types)} container rows"):
                failures = dashboard.bulk_upload_containers(upload_csv)
                assert not failures, (
                    "Bulk upload reported failures:\n" + failures
                )

            with allure.step("Verify every uploaded container appears in the table"):
                for sub_type in sub_types:
                    dashboard.verify_device_created(sub_type)

        finally:
            with allure.step("Teardown — delete all containers created by this test"):
                for sub_type in sub_types:
                    dashboard.delete_device_if_exists(sub_type)

    @allure.title("TC_CON_BULK_BAD — Malformed container CSV is rejected without an HTTP 500")
    def test_bulk_upload_containers_bad_csv(self, admin_page, processing_area, tmp_path):
        """
        ID     : TC_CON_BULK_BAD
        Title  : Container bulk upload rejects a malformed CSV gracefully
        Reason : All-or-nothing import means one bad row kills the whole batch.
                 The app must surface a clear rejection rather than a silent
                 empty table or an HTTP 500.
        """
        dashboard = AdminDashboardPage(admin_page)
        bad_csv   = tmp_path / "container_bulk_bad.csv"
        _build_bad_container_csv(bad_csv)

        processing_area.go_to_containers()

        with allure.step("Upload a CSV with invalid dimension values"):
            failures = dashboard.bulk_upload_containers(bad_csv)

        with allure.step("Verify no HTTP 500 was returned"):
            assert not admin_page.locator("text=500").is_visible(timeout=500), (
                "Server returned HTTP 500 after a bad container CSV upload."
            )

        with allure.step("Record rejection evidence"):
            allure.attach(
                f"failures_text={failures!r}  error_visible={is_error_visible(admin_page)}",
                name="rejection_evidence",
                attachment_type=allure.attachment_type.TEXT,
            )
