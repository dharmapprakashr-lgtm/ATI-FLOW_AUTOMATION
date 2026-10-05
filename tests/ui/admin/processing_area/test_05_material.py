"""Material tests — Baseline Setup · Existence · Validation · Scoping · Bulk Upload.

ALL material-related test cases for the Processing Area live here.
This file owns the delete-and-recreate of the baseline Processing Area and
its material so every run starts from a clean, known state.

  TC_MAT_000   Recreate the baseline Processing Area and seed the baseline material
  TC_MAT_001v  Baseline material is present in the Materials table
  TC_MAT_002   Add Material dialog enforces required fields
  TC_MAT_002b  Numeric fields (pre-proc time, max qty) reject alphabetic input
  TC_MAT_003   Material is scoped to its own Processing Area (isolation)
  TC_MAT_BULK  Bulk upload via CSV — template header + every row lands in table
  TC_MAT_BULK_BAD  Malformed CSV is rejected gracefully (no HTTP 500)
"""

import csv

import allure
import pytest
from playwright.sync_api import expect

from config.data import TestData
from config.environment import ROOT_DIR
from config.processing_area import material_spec
from pages.admin.admin_navigation import AdminDashboardPage
from utils.data_factory import run_token, unique_name
from utils.waits import is_error_visible

pytestmark = [pytest.mark.admin_pa]

MATERIAL_SAMPLE_CSV = ROOT_DIR / "data" / "material_bulk_upload.csv"

MATERIAL_COLUMNS = [
    "production_unit",
    "prefix_associated",
    "material_type_name",
    "process_name",
    "quarantine_time",
    "staging_area",
    "max_quantity",
]


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _build_material_csv(dest):
    """Read sample CSV, make every row unique, write to *dest*.

    Returns the list of material_type_name values written, in file order.
    """
    with open(MATERIAL_SAMPLE_CSV, newline="") as fh:
        rows = list(csv.DictReader(fh))

    token = run_token()
    names = []
    for i, row in enumerate(rows, start=1):
        row["material_type_name"] = unique_name(f"matbulk{i}")
        row["prefix_associated"] = f"MBP{i}{token}".upper()[:12]
        row["process_name"] = TestData.processing_area_name
        names.append(row["material_type_name"])

    with open(dest, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=MATERIAL_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    return names


def _build_bad_material_csv(dest):
    """Build a CSV with one intentionally invalid row."""
    bad_rows = [
        {
            "production_unit":   "",       # required — blank
            "prefix_associated": "",
            "material_type_name": "",      # required — blank
            "process_name":      "",
            "quarantine_time":   "abc",    # must be numeric
            "staging_area":      "false",
            "max_quantity":      "-99",    # must be positive
        }
    ]
    with open(dest, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=MATERIAL_COLUMNS)
        writer.writeheader()
        writer.writerows(bad_rows)


# =============================================================================
# TC_MAT_000 — Baseline setup (Processing Area + Material)
# =============================================================================

@allure.feature("Admin Console")
@allure.story("Material: baseline setup")
class TestMaterialBaselineSetup:
    """TC_MAT_000 — delete-and-recreate the baseline PA + seed the baseline material."""

    @allure.title("TC_MAT_000 — Recreate baseline Processing Area and seed baseline material")
    @pytest.mark.smoke
    def test_create_baseline_processing_area_and_material(self, admin_page, pa_page, safe_step):
        """
        ID     : TC_MAT_000
        Title  : Fresh Processing Area is created and baseline material is seeded
        Reason : Deleting and recreating the PA ensures no leftover data from a
                 previous run can mask a real failure in this or any downstream test.
                 The baseline material is required by workflow, WIP inventory, and
                 device-record tests.
        """
        dashboard = AdminDashboardPage(admin_page)
        material = material_spec()

        def area_step():
            pa_page.delete_processing_area(TestData.processing_area_name)
            pa_page.create_processing_area(
                TestData.processing_area_name,
                TestData.processing_area_description,
            )
        safe_step("Delete-and-recreate the baseline Processing Area", area_step)

        def material_step():
            pa_page.go_to_materials()
            dashboard.delete_device_if_exists(material.type_name)
            dashboard.add_material(
                material.type_name,
                material.production_unit,
                material.pre_proc_time,
                material.max_qty,
                material.prefix,
            )
            expect(
                admin_page.locator("tr").filter(has_text=material.type_name).first
            ).to_be_visible(timeout=5_000)
        safe_step("Materials tab: delete stale record, create baseline material", material_step)

        safe_step.assert_no_failures()


# =============================================================================
# TC_MAT_001v — Existence check
# =============================================================================

@allure.feature("Admin Console")
@allure.story("Material: existence verification")
class TestMaterialExists:
    """TC_MAT_001v"""

    @allure.title("TC_MAT_001v — Baseline material is present in the Materials table")
    def test_baseline_material_exists(self, admin_page, processing_area):
        """
        ID     : TC_MAT_001v
        Title  : Baseline material is present in the Materials table after setup
        Reason : Confirms TC_MAT_000 actually persisted the record. Downstream
                 tests (workflow, WIP inventory, requester device) all require it.
        """
        material = material_spec()
        processing_area.go_to_materials()

        with allure.step(f"Verify '{material.type_name}' is visible in the Materials table"):
            expect(
                admin_page.locator("tr").filter(has_text=material.type_name).first
            ).to_be_visible(timeout=8_000)


# =============================================================================
# TC_MAT_002 / TC_MAT_002b — Field validation
# =============================================================================

@allure.feature("Admin Console")
@allure.story("Material: field validation")
class TestMaterialFieldValidation:
    """TC_MAT_002 / TC_MAT_002b"""

    @allure.title("TC_MAT_002 — 'Add New Material' dialog rejects a completely empty form")
    def test_material_required_fields_enforced(self, admin_page, processing_area):
        """
        ID     : TC_MAT_002
        Title  : Add Material dialog rejects save when required fields are blank
        Reason : Submitting an empty form must not create a phantom material row
                 that downstream tests then stumble on.
        """
        processing_area.go_to_materials()

        with allure.step("Open 'Add New Material' dialog"):
            admin_page.locator("button").filter(has_text="Add New Material").click(force=True)
            expect(admin_page.locator("#mat-type-name")).to_be_visible(timeout=8_000)

        with allure.step("Click 'Add Material' without filling any fields"):
            admin_page.get_by_role("button", name="Add Material").click(force=True)
            admin_page.wait_for_timeout(1_000)

        with allure.step("Verify dialog stays open or an error is shown"):
            modal_open  = admin_page.locator(".MuiDialog-container").is_visible(timeout=1_000)
            error_shown = is_error_visible(admin_page)
            assert modal_open or error_shown, (
                "Expected the dialog to remain open or show an error when "
                "submitting an empty material form, but neither happened."
            )

        with allure.step("Close the dialog"):
            admin_page.keyboard.press("Escape")
            admin_page.wait_for_timeout(500)

    @allure.title("TC_MAT_002b — Numeric fields reject alphabetic input")
    def test_material_numeric_fields_reject_text(self, admin_page, processing_area):
        """
        ID     : TC_MAT_002b
        Title  : Material numeric fields (#mat-pre-proc-time, #mat-max-qty) reject text
        Reason : Alpha chars stored in a numeric field would produce NaN / zero
                 at the DB level, silently breaking capacity and pre-processing
                 calculations.
        """
        processing_area.go_to_materials()

        cases = [
            ("#mat-pre-proc-time", "abc", "pre-processing time"),
            ("#mat-max-qty",       "xyz", "max quantity"),
        ]

        for field_id, bad_value, label in cases:
            with allure.step(f"Type '{bad_value}' into '{label}' ({field_id})"):
                admin_page.locator("button").filter(has_text="Add New Material").click(force=True)
                expect(admin_page.locator("#mat-type-name")).to_be_visible(timeout=8_000)

                field = admin_page.locator(field_id)
                field.press_sequentially(bad_value)
                admin_page.wait_for_timeout(300)
                actual = field.input_value()
                assert not any(char.isalpha() for char in actual), (
                    f"Numeric field '{label}' accepted alphabetic input '{bad_value}'. "
                    f"Stored value: '{actual}'"
                )

                admin_page.keyboard.press("Escape")
                admin_page.wait_for_timeout(500)


# =============================================================================
# TC_MAT_003 — Area scoping / isolation
# =============================================================================

@allure.feature("Admin Console")
@allure.story("Material: area scoping")
class TestMaterialScoping:
    """TC_MAT_003"""

    @allure.title("TC_MAT_003 — Material created in Area A is absent from Area B")
    def test_material_scoped_to_its_processing_area(self, admin_page, pa_page):
        """
        ID     : TC_MAT_003
        Title  : Material is scoped to its own Processing Area (no cross-area leakage)
        Reason : Cross-area material leakage lets a Requester request a material
                 from the wrong area, sending the wrong stock to the wrong line.
        """
        material = material_spec()
        area_a = TestData.processing_area_name
        area_b = unique_name("pa_mat_scope")

        with allure.step(f"Open Area A '{area_a}' — confirm '{material.type_name}' is present"):
            pa_page.navigate_to_existing_area(area_a)
            pa_page.go_to_materials()
            expect(
                admin_page.locator("tr").filter(has_text=material.type_name).first
            ).to_be_visible(timeout=8_000)

        with allure.step(f"Create Area B '{area_b}' — confirm '{material.type_name}' is absent"):
            pa_page.create_processing_area(area_b, "Scope isolation test area")
            pa_page.go_to_materials()
            count = admin_page.locator("tr").filter(has_text=material.type_name).count()
            assert count == 0, (
                f"Material '{material.type_name}' from Area A leaked into Area B."
            )

        with allure.step(f"Teardown — delete Area B '{area_b}'"):
            pa_page.delete_processing_area(area_b)


# =============================================================================
# TC_MAT_BULK / TC_MAT_BULK_BAD — Bulk upload
# =============================================================================

@allure.feature("Admin Console")
@allure.story("Material: bulk upload")
class TestMaterialBulkUpload:
    """TC_MAT_BULK / TC_MAT_BULK_BAD"""

    @allure.title("TC_MAT_BULK — Valid CSV bulk upload creates every material row")
    def test_bulk_upload_materials_happy_path(self, admin_page, processing_area, tmp_path):
        """
        ID     : TC_MAT_BULK
        Title  : Material bulk upload — valid CSV imports all rows
        Reason : Bulk upload is the primary onboarding path for large areas.
                 A silently-dropped row means missing stock definitions that
                 only surface as a failed task at runtime.
        """
        dashboard  = AdminDashboardPage(admin_page)
        upload_csv = tmp_path / "material_bulk_upload.csv"
        names      = _build_material_csv(upload_csv)

        processing_area.go_to_materials()

        try:
            with allure.step("Verify CSV Template header matches expected columns"):
                template_path = dashboard.download_bulk_csv_template("material")
                with open(template_path, newline="") as fh:
                    header = next(csv.reader(fh))
                assert header == MATERIAL_COLUMNS, (
                    f"Template header changed — expected {MATERIAL_COLUMNS}, got {header}"
                )

            with allure.step(f"Upload CSV with {len(names)} material rows"):
                failures = dashboard.bulk_upload_materials(upload_csv)
                assert not failures, (
                    "Bulk upload rejected one or more rows:\n" + failures
                )

            with allure.step("Verify every uploaded material is visible in the table"):
                for name in names:
                    dashboard.verify_device_created(name)

        finally:
            with allure.step("Teardown — delete all materials created by this test"):
                for name in names:
                    dashboard.delete_device_if_exists(name)

    @allure.title("TC_MAT_BULK_BAD — Malformed CSV is rejected without an HTTP 500")
    def test_bulk_upload_materials_bad_csv(self, admin_page, processing_area, tmp_path):
        """
        ID     : TC_MAT_BULK_BAD
        Title  : Malformed material CSV is rejected gracefully
        Reason : An operator who pastes the wrong file must see a clear failure
                 (error toast / failures CSV), not a server 500 or a silent
                 empty-string row in the materials table.
        """
        dashboard = AdminDashboardPage(admin_page)
        bad_csv   = tmp_path / "material_bulk_bad.csv"
        _build_bad_material_csv(bad_csv)

        processing_area.go_to_materials()

        with allure.step("Upload a CSV that contains only invalid rows"):
            failures = dashboard.bulk_upload_materials(bad_csv)

        with allure.step("Verify no HTTP 500 is shown"):
            assert not admin_page.locator("text=500").is_visible(timeout=500), (
                "Server returned HTTP 500 after a bad material CSV upload."
            )

        with allure.step("Verify the app reported failures OR surfaced an error"):
            error_reported = bool(failures) or is_error_visible(admin_page)
            assert error_reported, (
                "Expected a failures text or error toast after uploading an "
                "all-bad-rows material CSV, but neither appeared."
            )
