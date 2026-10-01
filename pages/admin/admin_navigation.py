from utils.test_data_cleanup import track_area, track_device, track_ui_record
import re

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import expect


class AdminDashboardPage:
    def __init__(self, page):
        self.page = page

        # Execution Source Config
        self.execution_source_config_menu = self.page.locator("#operator-sidebar-nav").get_by_text("Execution Source Config")

        # Execution Source Config tabs
        self.requester_tab  = self.page.get_by_text("Requester Device", exact=True).first
        self.mes_tab        = self.page.get_by_text("MES", exact=True).first
        self.dispatcher_tab = self.page.get_by_text("Dispatcher Device", exact=True).first
        self.supervisor_tab = self.page.get_by_text("Supervisor Device", exact=True).first

        # Sidebar
        self.processing_areas_header     = self.page.get_by_text("Processing Areas", exact=True).first
        self.create_new_area_sidebar_btn = self.page.get_by_text("Create New Area", exact=True).last

        # Processing Area page sub-tabs. Only materials_tab (navigate_to_existing_area's
        # "page has loaded" signal) and workflow_tab (go_to_workflow, used by the e2e
        # suite) are read after construction - the rest of this tab strip is owned by
        # ProcessingAreaPage (pages/admin/processing_area/create_new_area_page.py).
        self.materials_tab = self.page.get_by_text("Materials", exact=True).first
        self.workflow_tab  = self.page.get_by_text("Workflow", exact=True).first

    # ── Execution Source Config ──────────────────────────────────────────────

    def navigate_to_execution_source_config(self):
        self.execution_source_config_menu.click(force=True)

    def _activate_tab(self, tab, attempts=3):
        """Switch to an Execution Source Config tab, skipping the click if
        it's already active — see ``ProcessingAreaPage._activate_tab``.

        Retries the click: against the live app a single click has been
        observed to not register at all (aria-selected staying "false" for
        the full wait) rather than just being slow, so a longer timeout on
        its own would not have helped - only clicking again did.
        """
        if tab.get_attribute("aria-selected") == "true":
            return
        for attempt in range(attempts):
            tab.click(force=True)
            try:
                expect(tab).to_have_attribute("aria-selected", "true", timeout=4000)
                return
            except AssertionError:
                if attempt == attempts - 1:
                    raise

    def click_requester_tab(self):
        self._activate_tab(self.requester_tab)

    def click_dispatcher_tab(self):
        self._activate_tab(self.dispatcher_tab)

    def click_supervisor_tab(self):
        self._activate_tab(self.supervisor_tab)

    def click_mes_tab(self):
        self._activate_tab(self.mes_tab)

    def go_to_workflow(self):
        self.workflow_tab.click(force=True)
        self.page.wait_for_timeout(500)

    # ── Processing Area creation ─────────────────────────────────────────────

    def expand_processing_areas(self):
        is_expanded = self.page.evaluate("""() => {
            for (const el of document.querySelectorAll('*')) {
                if (el.textContent.trim() === 'Create New Area' && el.offsetParent !== null)
                    return true;
            }
            return false;
        }""")
        if not is_expanded:
            self.processing_areas_header.click(force=True)
            self.page.wait_for_timeout(800)

    def _base_url(self):
        url = self.page.url
        for suffix in ["/processing_area", "/Execution_Source_Config", "/login"]:
            if suffix in url:
                url = url.split(suffix)[0]
        return url.rstrip("/")

    def navigate_to_existing_area(self, name):
        self.expand_processing_areas()
        self.page.get_by_text(name, exact=True).first.click(force=True)
        self.materials_tab.wait_for(state="visible", timeout=15000)

    def create_processing_area(self, name, description):
        self.expand_processing_areas()
        # check if it already exists
        if self.page.get_by_text(name, exact=True).count() > 0:
            self.navigate_to_existing_area(name)
            return

        track_area(name)
        self.create_new_area_sidebar_btn.click(force=True)
        name_input = self.page.get_by_placeholder("Enter area name")
        name_input.wait_for(state="visible", timeout=10000)
        name_input.fill(name)
        self.page.get_by_placeholder("Enter area description").fill(description)
        self.page.locator(".MuiDialogActions-root button").filter(has_text="SAVE").click(force=True)

        # wait for it to appear in sidebar
        self.page.get_by_text(name, exact=True).first.wait_for(state="visible", timeout=15000)
        self.navigate_to_existing_area(name)

    # ── Search bar helper ────────────────────────────────────────────────────
    #
    # Every table on this page (devices, materials, containers) shares the same
    # "fill the search box, act on the filtered row, clear the search box"
    # shape. Centralising it here is what let delete_device_if_exists,
    # verify_device_created and the three update_*_device methods below drop
    # their own copies of it.

    def _search_for(self, text):
        """Filter the current table through the search bar, if one is present."""
        search_input = self.page.get_by_placeholder(re.compile("Search", re.IGNORECASE)).first
        if search_input.is_visible():
            search_input.fill(text)
            self.page.wait_for_timeout(1000)
        return search_input

    def _clear_search(self, search_input):
        if search_input.is_visible():
            search_input.fill("")
            self.page.wait_for_timeout(500)

    # ── Multi-select autocomplete helper ─────────────────────────────────────
    #
    # Bound Workflows, Bound Stations and (verified live) most "Bound"/"Visible"
    # fields on the device forms are real multi-select MUI Autocompletes: picking
    # one option does not close the dropdown, so several can be chosen in one
    # pass. update_*_device and add_*_device below all shared a copy-pasted
    # "fill, wait, click the option, wait, Escape" block; this is that block,
    # generalised to accept either a single string or a list of them.

    def _select_options(self, label, values):
        """Type into the ``label`` combobox and select one or more options.

        The field is resolved once via ``.first`` rather than re-running
        ``get_by_label`` per value: once an option has been picked, the open
        listbox also exposes the same accessible name, so a fresh
        ``get_by_label`` call after the first pick matches both the input and
        the listbox and raises a strict-mode violation.
        """
        if not values:
            return
        field = self.page.get_by_label(label, exact=False).first
        # The chip(s) for already-picked values render inside this same
        # wrapper, before the text input - reading its text is how a pick is
        # verified below (the admin's own Workflow tab is clean - exactly 4
        # rows for this suite's area, confirmed live 2026-09-07 - so the chip
        # either shows up or the pick silently didn't take; there is nothing
        # to "clean up" upstream, the bloat is in this dropdown's own data
        # source only).
        container = field.locator(
            "xpath=ancestor::div[contains(@class,'MuiAutocomplete-inputRoot')]"
        ).first
        any_option = self.page.get_by_role("option")
        for value in ([values] if isinstance(values, str) else values):
            # Typing to filter (the old approach) does NOT actually filter
            # this list - the rendered option count *grows* while typing
            # (182 -> 229 after a 25-char query on "Bound Workflows"), so
            # every keystroke re-renders the whole unfiltered list. Clicking
            # the field open and matching against the full list (confirmed to
            # contain every real option, unfiltered) is what actually works -
            # so this never types anything.
            #
            # Confirmed live 2026-09-07: some of these lists ("Bound
            # Workflows" carries 150+ options, 67+ exact duplicates of one
            # name from earlier non-idempotent test runs) have many stale
            # duplicate DOM nodes that are NOT wired to the form's real
            # onChange state - clicking one is a silent no-op (SAVE then fails
            # with "At least one X is required" even though the click
            # "succeeded"). Also, clicking an already-open field to "make
            # sure" it's open can instead toggle it *closed*. So: only click
            # to open when nothing is rendered; try matching candidates
            # newest-first (an index heuristic, not guaranteed); verify the
            # chip actually appears after each click and move to the next
            # candidate (reopening first if the popup closed) until one
            # registers, capped at 10 tries so a pathological list fails
            # loudly instead of hanging.
            if any_option.count() == 0:
                field.click(force=True)
            matches = self.page.get_by_role("option", name=value, exact=True)
            matches.first.wait_for(state="attached", timeout=20000)
            total = matches.count()
            registered = False
            for idx in range(total - 1, max(total - 11, -1), -1):
                candidate = matches.nth(idx)
                candidate.scroll_into_view_if_needed()
                candidate.click(force=True)
                self.page.wait_for_timeout(300)
                if value in container.inner_text():
                    registered = True
                    break
                if self.page.get_by_role("option").count() == 0:
                    field.click(force=True)
                    self.page.wait_for_timeout(300)
            if not registered:
                raise AssertionError(
                    f"{label}: none of the {min(total, 10)} option(s) matching "
                    f"{value!r} registered a selection after clicking."
                )
        self.page.keyboard.press("Escape")
        self.page.wait_for_timeout(500)

    # ── Execution Source Config / Devices ──────────────────────────────────────

    def _row_by_exact_name(self, name):
        """Row(s) whose visible text exactly matches ``name`` - not a substring.

        A plain ``has_text=name`` filter matches any row whose text merely
        *contains* name. This suite's own ``crud_<name>`` naming convention
        (e.g. "crud_pick" alongside a baseline "pick") makes that collision
        likely, not hypothetical - whichever row sorts first then silently
        gets deleted/edited instead of the intended one. Scoping the match to
        a descendant with exact text avoids that ambiguity.
        """
        return self.page.locator("tr").filter(has=self.page.get_by_text(name, exact=True))

    def delete_device_if_exists(self, device_name):
        search_input = self._search_for(device_name)

        row = self._row_by_exact_name(device_name)
        if row.count() == 0:
            self._clear_search(search_input)
            return False

        row.first.locator("button").last.click(force=True)
        self.page.wait_for_timeout(500)
        self.page.get_by_role("button", name="DELETE").click(force=True)
        self.page.wait_for_timeout(1500)
        # wait for modal to close
        try:
            self.page.locator(".MuiDialog-container").wait_for(state="hidden", timeout=2000)
        except Exception:
            pass

        # Verify deletion - poll rather than a single snapshot. A fixed
        # 500ms pause here previously produced false "not deleted" warnings
        # when the table's re-render just lagged behind the delete call,
        # leaving the row (falsely believed gone) to collide with the next
        # create attempt using the same name.
        try:
            expect(row.first).not_to_be_visible(timeout=5000)
            print(f"Successfully deleted {device_name}.")
        except AssertionError:
            self._clear_search(search_input)
            raise AssertionError(f"UI record '{device_name}' was not deleted successfully")

        self._clear_search(search_input)
        return True

    def verify_device_created(self, device_name):
        search_input = self._search_for(device_name)
        expect(self._row_by_exact_name(device_name).first).to_be_visible(timeout=5000)
        self._clear_search(search_input)

    def _open_row_editor(self, name):
        """Search for ``name``, then open its row's editor. Returns the search box."""
        search_input = self._search_for(name)
        row = self._row_by_exact_name(name)
        if row.count() > 0:
            row.first.locator("button").first.click(force=True)
            self.page.wait_for_timeout(1000)
        return search_input, row

    def _save_open_editor(self):
        """Click SAVE and best-effort wait for the modal to close.

        Silent on failure by design (matches the pre-refactor behaviour of
        the three update_*_device methods): an update that doesn't close its
        modal is left for the caller's own verify_device_created check to
        catch, rather than raising here.
        """
        self.page.get_by_role("button", name="SAVE").click(force=True)
        self.page.wait_for_timeout(1500)
        try:
            self.page.locator(".MuiDialog-container").wait_for(state="hidden", timeout=2000)
        except Exception:
            pass

    def update_requester_device(self, name, new_password, new_machines, new_workflows, new_staging):
        search_input, row = self._open_row_editor(name)
        if row.count() > 0:
            if new_password:
                self.page.get_by_placeholder(re.compile("Password")).fill(new_password)
                self.page.wait_for_timeout(500)
            self._select_options("Bound Machines", new_machines)
            self._select_options("Bound Workflows", new_workflows)
            self._select_options("Visible Staging Areas", new_staging)

            self._save_open_editor()

        self._clear_search(search_input)

    def update_dispatcher_device(self, name, new_password, new_stations, new_staging):
        search_input, row = self._open_row_editor(name)
        if row.count() > 0:
            if new_password:
                self.page.get_by_placeholder(re.compile("Password")).fill(new_password)
                self.page.wait_for_timeout(500)
            self._select_options("Bound Stations", new_stations)
            self._select_options("Visible Staging Areas", new_staging)

            self._save_open_editor()

        self._clear_search(search_input)

    def update_supervisor_device(self, name, new_password, new_staging, new_processing):
        search_input, row = self._open_row_editor(name)
        if row.count() > 0:
            if new_password:
                self.page.get_by_placeholder(re.compile("Password")).fill(new_password)
                self.page.wait_for_timeout(500)
            self._select_options("Visible Staging Areas", new_staging)
            if new_processing:
                self._check_processing_area(new_processing)
                self.page.wait_for_timeout(500)

            self._save_open_editor()

        self._clear_search(search_input)

    # ── Shared "did the create-modal actually save?" check ──────────────────
    #
    # Every add_*_device / add_material / add_container method clicks SAVE and
    # then must tell a real save from a rejected one. Two variants are needed:
    #
    # - the three device methods treat "the modal closed" as authoritative and
    #   only consult the error popup to enrich the exception message, plus they
    #   force-close a stuck modal so the next test doesn't inherit it;
    # - add_material/add_container treat an error popup as authoritative and
    #   raise on it immediately, without waiting out the full modal-close
    #   timeout or attempting cleanup.
    #
    # _verify_save decides between them via raise_immediately_on_error /
    # cleanup_on_fail rather than picking one behaviour for all five callers,
    # which would have been a real (if probably harmless) behaviour change.
    _ERROR_SELECTORS = (
        ".Toastify__toast--error",
        "[role='alert']",
        "div[class*='MuiSnackbar']",
        ".MuiAlert-standardError",
    )

    def _verify_save(self, *, timeout, raise_immediately_on_error, cleanup_on_fail):
        popup_error = None
        for sel in self._ERROR_SELECTORS:
            err_el = self.page.locator(sel).first
            if err_el.is_visible(timeout=1000):
                err_text = err_el.text_content().strip()
                if "success" in err_text.lower():
                    continue
                if raise_immediately_on_error:
                    raise AssertionError(f"Action failed with popup: '{err_text}'")
                popup_error = err_text
                break

        try:
            self.page.locator(".MuiDialog-container").wait_for(state="hidden", timeout=timeout)
        except Exception:
            if cleanup_on_fail:
                self.page.keyboard.press("Escape")
                self.page.wait_for_timeout(500)
                self.page.keyboard.press("Escape")
                self.page.wait_for_timeout(1000)
            if popup_error:
                raise AssertionError(f"Action failed with popup: '{popup_error}'")
            raise AssertionError("Action failed: Modal did not close after clicking SAVE.")

    def _verify_device_save(self):
        # Bumped from 1500ms 2026-09-07: no popup_error is ever raised here (no
        # error toast renders), so a device record with several Bound
        # Workflows/Stations/Staging Areas just needs more than 1.5s for the
        # backend to persist every selection before the modal closes - not a
        # failed save.
        self._verify_save(timeout=6000, raise_immediately_on_error=False, cleanup_on_fail=True)

    def _verify_record_save(self, timeout=3000):
        self._verify_save(timeout=timeout, raise_immediately_on_error=True, cleanup_on_fail=False)

    def _open_add_modal(self, button_text, first_field, attempts=3):
        """Click an "Add"/"Add New X" button, retrying if the modal doesn't open.

        Same fix as ``_activate_tab``: on the live app a single click has
        been observed to not register at all, so this retries the click
        itself (checked via the modal's first field appearing) rather than
        just waiting longer.
        """
        button = self.page.locator("button").filter(has_text=button_text)
        for attempt in range(attempts):
            button.click(force=True)
            try:
                first_field.wait_for(state="visible", timeout=4000)
                return
            except Exception:
                if attempt == attempts - 1:
                    raise

    def add_requester_device(self, name, device_id, password, bound_machines, bound_workflows, staging_areas):
        """Create a Requester device.

        ``bound_machines``, ``bound_workflows`` and ``staging_areas`` each take
        either a single string or a list of them - the live app's "Bound"/
        "Visible" fields are real multi-select autocompletes (verified: picking
        one option leaves the dropdown open for more), so a device can bind to
        several workflows/staging areas the same way the admin UI allows.
        """
        name_field = self.page.get_by_placeholder("Requester Name")
        self._open_add_modal("ADD NEW", name_field)
        name_field.fill(name)
        self.page.get_by_placeholder("Device ID").fill(device_id)
        self.page.get_by_placeholder("Password").fill(password)

        # Bound Workflows MUST be filled before Bound Machines. Confirmed live
        # 2026-09-07: selecting a Bound Machines option first and closing its
        # popup (Escape) leaves "Bound Workflows" opening to 0 options no
        # matter how it's reopened (click, re-focus, native Tab, the popup's
        # own toggle button all tried) - a real app-side quirk, not a locator
        # problem. The reverse order (Workflows, then Machines) was verified
        # to open both fields with their full option lists every time. Saving
        # a form doesn't care what order independent fields were filled in, so
        # this reorder is a safe workaround, not a behaviour change.
        self._select_options("Bound Workflows", bound_workflows)
        self._select_options("Bound Machines", bound_machines)
        self._select_options("Visible Staging Areas", staging_areas)

        self.page.get_by_role("button", name="SAVE").click(force=True)
        self.page.wait_for_timeout(1500)
        self._verify_device_save()
        track_device("requester", name)

    def add_dispatcher_device(self, name, device_id, password, bound_stations, staging_areas):
        """Create a Dispatcher device. ``bound_stations``/``staging_areas``: see
        ``add_requester_device`` - both accept a single string or a list."""
        name_field = self.page.get_by_placeholder("Dispatcher Name")
        self._open_add_modal("ADD NEW", name_field)
        name_field.fill(name)
        self.page.get_by_placeholder("Device ID").fill(device_id)
        self.page.get_by_placeholder("Password").fill(password)

        self._select_options("Bound Stations", bound_stations)
        self._select_options("Visible Staging Areas", staging_areas)

        self.page.get_by_role("button", name="SAVE").click(force=True)
        self.page.wait_for_timeout(1500)
        self._verify_device_save()
        track_device("dispatcher", name)

    # ── Processing Area checkbox helper ──────────────────────────────────────
    #
    # The Supervisor device form renders Processing Area checkboxes as MUI
    # <Checkbox> components inside <FormControlLabel> wrappers. There is no
    # traditional <label for="..."> association, so Playwright's get_by_label()
    # never resolves the element and times out. The correct approach is to
    # scope to the MuiFormControlLabel-root that contains the visible area
    # name, then target the <input type="checkbox"> inside it.

    def _check_processing_area(self, area_name):
        """Tick the Processing Area checkbox for ``area_name`` in the open dialog."""
        label = self.page.locator(".MuiFormControlLabel-root").filter(
            has=self.page.get_by_text(area_name, exact=True)
        )
        checkbox = label.locator("input[type='checkbox']")
        checkbox.wait_for(state="attached", timeout=10000)
        if not checkbox.is_checked():
            label.click(force=True)
            self.page.wait_for_timeout(300)

    def add_supervisor_device(self, name, device_id, password, staging_areas, processing_areas):
        name_field = self.page.get_by_placeholder("Supervisor Name")
        self._open_add_modal("ADD NEW", name_field)
        name_field.fill(name)
        self.page.get_by_placeholder("Device ID").fill(device_id)
        self.page.get_by_placeholder("Password").fill(password)

        self._select_options("Visible Staging Areas", staging_areas)

        # Select Processing Area checkbox(es) - one or more processing areas.
        for area in ([processing_areas] if isinstance(processing_areas, str) else processing_areas):
            self._check_processing_area(area)
            self.page.wait_for_timeout(500)

        self.page.get_by_role("button", name="SAVE").click(force=True)
        self.page.wait_for_timeout(1500)
        self._verify_device_save()
        track_device("supervisor", name)

    # ── Materials CRUD ────────────────────────────────────────────────────────

    def add_material(self, material_type_name, production_unit, pre_proc_time, max_qty, prefix):
        """Click Add New Material, fill the modal using confirmed IDs, and submit.

        Enables the "Staging Area" toggle so this material also creates the
        staging area the requester/dispatcher/supervisor device records bind
        to - it's the only place in the app that builds one, there is no
        separate Staging Area creation flow.
        """
        track_ui_record(self.page, material_type_name)
        type_name_field = self.page.locator("#mat-type-name")
        self._open_add_modal("Add New Material", type_name_field)

        # Fill using exact IDs discovered via diagnostic
        type_name_field.fill(material_type_name)
        self.page.locator("#mat-pre-proc-time").fill(str(pre_proc_time))
        self.page.locator("#mat-max-qty").fill(str(max_qty))
        self.page.locator("#mat-prefix").fill(prefix)
        self.page.wait_for_timeout(500)
        # Click the '+' button to actually add the prefix to the list
        self.page.locator("button:right-of(#mat-prefix)").first.click(force=True)
        self.page.wait_for_timeout(500)

        # Production Unit is a combobox/autocomplete - type and select
        self.page.locator("[placeholder='e.g. Unit A']").fill(production_unit)
        self.page.wait_for_timeout(500)
        self.page.keyboard.press("Enter")
        self.page.wait_for_timeout(500)

        # Staging Area toggle - the only way this app builds a staging area
        # for device records to bind to.
        self.page.get_by_label("Staging Area", exact=True).check(force=True)
        self.page.wait_for_timeout(500)

        # Submit
        self.page.get_by_role("button", name="Add Material").click(force=True)
        self.page.wait_for_timeout(2000)
        self._verify_record_save()

    # ── Bulk upload (Materials + Containers) ────────────────────────────────
    #
    # Both the Materials and Containers tabs carry a "Bulk Upload" button
    # beside "Add New <entity>" (and an "Export CSV" button). It opens a
    # "Bulk Upload <entity>" dialog (verified live 2026-09-03):
    #   - a drop zone wrapping <input type="file" accept=".csv">
    #   - "Download CSV Template" -> a headers-only CSV
    #       Materials : production_unit, prefix_associated, material_type_name,
    #                   process_name, quarantine_time, staging_area, max_quantity
    #       Containers: containerType, containerSubType, length, width, height,
    #                   hitch_length, units
    #   - action buttons: #mat-bulk-cancel / #mat-bulk-upload  (Materials)
    #                      #ct-bulk-cancel  / #ct-bulk-upload   (Containers)
    #
    # Materials import is per-row: good rows land, and a rejected row is
    # reported in an auto-downloaded `material_config_failures.csv` (one extra
    # `error_reason` column). Containers import is all-or-nothing: one malformed
    # row (e.g. a blank numeric field) rejects the whole file with no failures
    # file. Either way, a fully-clean upload downloads nothing and the dialog
    # closes itself.

    _BULK_IDS = {
        "material": ("#mat-bulk-upload", "#mat-bulk-cancel"),
        "container": ("#ct-bulk-upload", "#ct-bulk-cancel"),
    }

    def open_bulk_upload(self, entity, attempts=3):
        """Open the 'Bulk Upload' dialog on the current (Materials/Containers) tab.

        The live app sometimes ignores a single click silently (similar to the
        other modal flows in this page object), so retry the click itself until
        the upload CTA becomes visible instead of relying on a single 5s wait.
        """
        upload_id, _ = self._BULK_IDS[entity]
        bulk_button = self.page.get_by_role("button", name="Bulk Upload")
        for attempt in range(attempts):
            bulk_button.click(force=True)
            try:
                self.page.locator(upload_id).wait_for(state="visible", timeout=4000)
                return
            except Exception:
                if attempt == attempts - 1:
                    raise

    def download_bulk_csv_template(self, entity):
        """Click 'Download CSV Template' in the open dialog; return the saved path."""
        self.open_bulk_upload(entity)
        with self.page.expect_download() as download:
            self.page.get_by_role(
                "button", name=re.compile("Download CSV Template", re.IGNORECASE)
            ).click(force=True)
        path = download.value.path()
        _, cancel_id = self._BULK_IDS[entity]
        cancel = self.page.locator(cancel_id)
        if cancel.count() and cancel.is_visible():
            cancel.click(force=True)
            self.page.wait_for_timeout(300)
        return path

    def bulk_upload(self, entity, csv_path):
        """Upload ``csv_path`` through the ``entity`` (Materials/Containers) ▸
        Bulk Upload dialog.

        Returns "" when the upload reported no failures, or the text of the
        per-row failures CSV the app downloads on a rejected row (Materials).
        NOTE for containers: a rejected file downloads nothing, so callers must
        also verify the rows actually landed in the table.
        """
        import csv
        with open(csv_path, newline="", encoding="utf-8-sig") as source:
            field = "material_type_name" if entity == "material" else "containerSubType"
            for row in csv.DictReader(source):
                track_ui_record(self.page, row.get(field, ""))
        upload_id, cancel_id = self._BULK_IDS[entity]
        self.open_bulk_upload(entity)
        self.page.locator(
            "[role='dialog'] input[type='file']"
        ).set_input_files(str(csv_path))
        self.page.wait_for_timeout(500)

        failures = ""
        try:
            with self.page.expect_download(timeout=5000) as download:
                self.page.locator(upload_id).click(force=True)
            try:
                with open(download.value.path()) as fh:
                    failures = fh.read()
            except Exception:
                failures = "(failures file downloaded but could not be read)"
        except PlaywrightTimeoutError:
            pass  # no failures file downloaded

        cancel = self.page.locator(cancel_id)
        if cancel.count() and cancel.is_visible():
            cancel.click(force=True)
        self.page.wait_for_timeout(1000)
        return failures

    # Backwards-compatible thin wrappers (Materials-specific call sites).
    def open_material_bulk_upload(self):
        self.open_bulk_upload("material")

    def download_material_csv_template(self):
        return self.download_bulk_csv_template("material")

    def bulk_upload_materials(self, csv_path):
        return self.bulk_upload("material", csv_path)

    def bulk_upload_containers(self, csv_path):
        return self.bulk_upload("container", csv_path)

    # ── Containers CRUD ────────────────────────────────────────────────────────

    def add_container(self, container_type, sub_type, length, width, height, hitch_length, qty=1):
        """Click Add New Container, fill the modal using confirmed IDs, and save."""
        track_ui_record(self.page, sub_type)
        ctr_type_field = self.page.locator("#ctr-type")
        self._open_add_modal("Add New Container", ctr_type_field)

        # Container Type dropdown - ID: ctr-type
        ctr_type_field.click(force=True)
        self.page.wait_for_timeout(500)
        self.page.get_by_role("option", name=container_type, exact=True).click()

        # Sub-type - ID: ctr-sub-type
        self.page.locator("#ctr-sub-type").fill(sub_type)

        # Dimensions - confirmed IDs
        self.page.locator("#ctr-length").fill(str(length))
        self.page.locator("#ctr-width").fill(str(width))
        self.page.locator("#ctr-height").fill(str(height))
        self.page.locator("#ctr-hitch-length").fill(str(hitch_length))
        self.page.locator("#ctr-qty").fill(str(qty))
        self.page.keyboard.press("Tab")
        self.page.wait_for_timeout(500)

        # Save
        self.page.locator(".MuiDialog-container").get_by_role("button", name="SAVE", exact=True).click()
        self.page.wait_for_timeout(2000)
        self._verify_record_save()
