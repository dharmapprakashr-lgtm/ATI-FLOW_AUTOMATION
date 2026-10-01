from utils.test_data_cleanup import track_area, track_area_rename, track_ui_record
from playwright.sync_api import expect

from utils.waits import wait_for_modal_close


class ProcessingAreaPage:
    def __init__(self, page):
        self.page = page

        #: Station ID chosen for each mapping name, so a caller can assert the
        #: pickup and drop mappings did not land on the same station.
        self.selected_station_ids = {}

        # Sidebar locators — scoped to the sidebar element to avoid false matches
        self.sidebar = self.page.locator("#operator-sidebar-root")
        self.processing_areas_header = self.page.get_by_text("Processing Areas", exact=True).first
        self.create_new_area_sidebar_btn = self.page.locator("#operator-sidebar-nav").get_by_text("Create New Area", exact=True)

        # Processing Area page sub-tabs (role-based, unambiguous)
        self.materials_tab     = self.page.get_by_role("tab", name="Materials")
        self.containers_tab    = self.page.get_by_role("tab", name="Containers")
        self.workflow_tab      = self.page.get_by_role("tab", name="Workflow")
        self.wip_tab           = self.page.get_by_role("tab", name="WIP Inventory")
        self.staging_area_tab  = self.page.get_by_role("tab", name="Staging Area")
        self.station_map_tab   = self.page.get_by_role("tab", name="Station Mapping")
        self.machine_names_tab = self.page.get_by_role("tab", name="Machine Names")

    # ── Sidebar helpers ───────────────────────────────────────────────────────

    def expand_processing_areas(self):
        """Ensure the sidebar Processing Areas accordion is expanded."""
        # "Create New Area" link is only visible when accordion is open
        if not self.create_new_area_sidebar_btn.is_visible():
            self.processing_areas_header.click()
        expect(self.create_new_area_sidebar_btn).to_be_visible(timeout=15000)

    def _area_link_in_sidebar(self, name):
        """Return the sidebar span that shows the area name."""
        return self.sidebar.get_by_text(name, exact=True)

    def navigate_to_existing_area(self, name):
        """Click the area in the sidebar and wait for the tab strip to appear."""
        self.expand_processing_areas()
        self._area_link_in_sidebar(name).first.click()
        # Execution Source Config has a tablist too; it cannot prove area navigation.
        expect(self.materials_tab).to_be_visible(timeout=15000)

    # ── CRUD ─────────────────────────────────────────────────────────────────

    def open_create_area_dialog(self):
        """Wait for the create dialog before tests start filling its fields."""
        self.expand_processing_areas()
        name_input = self.page.get_by_placeholder("Enter area name")
        for attempt in range(3):
            self.create_new_area_sidebar_btn.click()
            try:
                expect(name_input).to_be_visible(timeout=4000)
                break
            except AssertionError:
                if attempt == 2:
                    raise

    def create_processing_area(self, name, description):
        """Create a new processing area, or navigate to it if it already exists."""
        self.expand_processing_areas()

        # Check if it already exists in the sidebar
        if self._area_link_in_sidebar(name).count() > 0:
            self.navigate_to_existing_area(name)
            return

        track_area(name)
        self.open_create_area_dialog()
        name_input = self.page.get_by_placeholder("Enter area name")
        name_input.fill(name)
        self.page.get_by_placeholder("Enter area description").fill(description)
        self.page.locator(".MuiDialogActions-root button").filter(has_text="SAVE").click(force=True)
        wait_for_modal_close(self.page, "Create area")

        # Expand accordion and navigate
        self.expand_processing_areas()
        self._area_link_in_sidebar(name).first.wait_for(state="visible", timeout=10000)
        self.navigate_to_existing_area(name)

    def _open_row_menu(self, name, attempts=3):
        """Open the 3-dot row menu for a Processing Area, retrying the click.

        Same fix as ``_activate_tab``: against the live app a single click on
        the 3-dot button has been observed to not register at all rather than
        just being slow, so this retries until a menu item actually appears
        instead of trusting one click and a fixed wait.

        Structure: <div><div><span>name</span></div><button>...</button></div>
        """
        area_row = self._area_link_in_sidebar(name).locator(
            "xpath=ancestor::div[contains(@class,'css-13aljni') or contains(@class,'css-es7gyt')]"
        )
        menu_item = self.page.get_by_role("menuitem").first
        for attempt in range(attempts):
            area_row.last.locator("button").click(force=True)
            try:
                menu_item.wait_for(state="visible", timeout=2500)
                return
            except Exception:
                if attempt == attempts - 1:
                    raise AssertionError(
                        f"3-dot menu for '{name}' did not open after {attempts} attempts."
                    )
                self.page.keyboard.press("Escape")
                self.page.wait_for_timeout(300)

    def edit_processing_area(self, current_name, new_name, new_description):
        """Edit a processing area name and description via the 3-dot menu."""
        self.expand_processing_areas()

        if self._area_link_in_sidebar(current_name).count() == 0:
            raise Exception(f"Processing Area '{current_name}' not found for editing.")

        track_area_rename(current_name, new_name)
        self._open_row_menu(current_name)
        self.page.get_by_role("menuitem", name="Edit").click(force=True)
        self.page.wait_for_timeout(1000)

        self.page.get_by_placeholder("Enter area name").fill(new_name)
        self.page.get_by_placeholder("Enter area description").fill(new_description)
        self.page.locator(".MuiDialogActions-root button").filter(has_text="SAVE").click(force=True)
        wait_for_modal_close(self.page, "Edit area")

        self.expand_processing_areas()
        self._area_link_in_sidebar(new_name).first.wait_for(state="visible", timeout=10000)

    def delete_processing_area(self, name):
        """Delete a processing area via the 3-dot menu.

        Returns True if it deleted something, False if the area wasn't there.
        Raises if the area is still in the sidebar afterwards — a silent failure
        here strands the material/container/workflow/station data underneath it.
        """
        self.expand_processing_areas()

        if self._area_link_in_sidebar(name).count() == 0:
            return False  # Already gone

        self._open_row_menu(name)
        self.page.get_by_role("menuitem", name="Delete").click(force=True)
        self.page.wait_for_timeout(1000)

        self.page.get_by_role("button", name="DELETE").click(force=True)
        self.page.wait_for_timeout(2000)

        self.expand_processing_areas()
        expect(self._area_link_in_sidebar(name).first).not_to_be_visible(timeout=10000)
        return True

    # ── Sub-tab navigation ────────────────────────────────────────────────────

    def _activate_tab(self, tab, attempts=3):
        """Switch to a sub-tab, skipping the click if it's already active.

        Every caller used to click and then separately assert
        ``aria-selected="true"``. Folding that check in here means a tab
        that's already open — the fixture just landed on it, or the previous
        step used it too — isn't re-clicked and re-waited on every call.

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
                self.page.wait_for_timeout(500)
                return
            except AssertionError:
                if attempt == attempts - 1:
                    raise

    def go_to_materials(self):
        self._activate_tab(self.materials_tab)

    def go_to_containers(self):
        self._activate_tab(self.containers_tab)

    def go_to_workflow(self):
        self._activate_tab(self.workflow_tab)

    def go_to_wip_inventory(self):
        self._activate_tab(self.wip_tab)

    def go_to_staging_area(self):
        self._activate_tab(self.staging_area_tab)

    def go_to_station_mapping(self):
        self._activate_tab(self.station_map_tab)

    def go_to_machine_names(self):
        self._activate_tab(self.machine_names_tab)

    # ── Machine Names CRUD ────────────────────────────────────────────────────

    def fill_machine_form(self, name, production_type):
        """Open and fill the machine dialog, including its initialization waits.

        production_type is the dropdown label, e.g. "Production Type" or
        "Consumption Type".
        """
        self.page.get_by_role("button", name="Add", exact=True).click()
        dialog = self.page.locator(".MuiDialog-container")
        expect(dialog).to_be_visible()
        point_type = dialog.locator(".MuiSelect-select").first
        point_type.click()
        self.page.get_by_role("option", name=production_type, exact=True).click()
        expect(point_type).to_have_text(production_type)
        name_input = dialog.get_by_placeholder("e.g. Machine A")
        name_input.fill(name)
        name_input.press("Tab")
        expect(name_input).to_have_value(name)

    def add_machine_name(self, name, production_type):
        """Create a machine using the same form flow as validation tests."""
        track_ui_record(self.page, name)
        self.fill_machine_form(name, production_type)
        self.page.locator(".MuiDialogActions-root button").last.click()
        wait_for_modal_close(self.page, f"Create machine '{name}'", timeout=15000)
        expect(self.page.locator("tr").filter(has_text=name).first).to_be_visible(timeout=5000)

    # ── Station Mapping CRUD ──────────────────────────────────────────────────
    #
    # Unlike every other admin entity (Materials, Containers, Machines,
    # Devices, Workflows), a Station Mapping is NOT a table row - the
    # Material Mapping grid is a matrix (rows = Material Types, columns = one
    # per mapping name, cells = the assigned Station ID), and each mapping's
    # edit/delete icons sit on its own <th> column header. Verified live
    # (2026-08-26): a `<tr>` filtered by has_text=name looks row-based but
    # actually false-positives whenever some OTHER row's Station ID *value*
    # contains `name` as a substring - real live Station IDs like
    # "pick_station_1" and "pick2_gg" contain "pick", "drop_station_1"
    # contains "drop". That false positive let a mapping-creation check pass
    # even when the mapping never actually persisted, and it made
    # AdminDashboardPage.delete_device_if_exists (built for row-based
    # entities with a delete button inside the row) target the wrong element
    # for this one. _mapping_column_header/verify_station_mapping_exists/
    # delete_station_mapping_if_exists below are the correct, column-based
    # equivalents - use these instead of delete_device_if_exists /
    # a bare `<tr>` filter for Station Mapping specifically.

    def _mapping_column_header(self, name):
        """The exact Material Mapping column header for one mapping name."""
        return self.page.get_by_role("columnheader", name=name, exact=True)

    def verify_station_mapping_exists(self, name, timeout=5000):
        expect(self._mapping_column_header(name)).to_be_visible(timeout=timeout)

    def delete_station_mapping_if_exists(self, name):
        """Delete a Station Mapping column by its exact name, via its header's
        trash icon (the last of the two icon buttons on the column header -
        the first is edit). Returns False when no matching column exists."""
        header = self._mapping_column_header(name)
        if header.count() == 0:
            return False

        header.locator("button").last.click(force=True)
        self.page.wait_for_timeout(500)
        self.page.get_by_role("button", name="DELETE").click(force=True)
        self.page.wait_for_timeout(1500)
        try:
            self.page.locator(".MuiDialog-container").wait_for(state="hidden", timeout=2000)
        except Exception:
            pass

        try:
            expect(header).not_to_be_visible(timeout=5000)
            print(f"Successfully deleted station mapping {name}.")
        except AssertionError:
            print(f"Warning: station mapping {name} was not deleted successfully!")
        return True

    def _select_option(self, what, station=None, index=None):
        """Pick an open dropdown's option by exact name, or by position.

        Raises with the options that were actually offered - a bare Playwright
        timeout here tells you nothing about why the value was missing.
        """
        options = self.page.locator("li[role='option']")
        try:
            options.first.wait_for(state="visible", timeout=8000)
        except Exception:
            raise AssertionError(f"{what}: the dropdown rendered no options.")

        if station is not None:
            match = self.page.get_by_role("option", name=station, exact=True)
            if match.count() == 0:
                available = [o.strip() for o in options.all_text_contents()]
                raise AssertionError(f"{what}: '{station}' not offered. Available: {available}")
            match.first.click(force=True)
            return station

        available = [o.strip() for o in options.all_text_contents()]
        if index >= len(available):
            raise AssertionError(
                f"{what}: needed option #{index + 1} but only {len(available)} "
                f"exist: {available}"
            )
        options.nth(index).click(force=True)
        return available[index]

    def add_station_mapping(self, name, station_id=None, station_index=0):
        """Add a station mapping on the Station Mapping tab.

        ``station_id`` pins an exact Station ID; otherwise the one at
        ``station_index`` is used. Two mappings must not share a station, so
        callers creating a pickup/drop pair pass different values - taking the
        first option every time silently mapped both to the same station.

        Material Type takes the first option; the tab is only usable once a
        material and a machine already exist.
        """
        track_ui_record(self.page, name, kind="mapping")
        self.page.locator("button").filter(has_text="Add").first.click(force=True)
        self.page.wait_for_timeout(1000)

        # Mapping name is a free-type autocomplete, not a plain text input
        name_input = self.page.locator(".MuiDialog-container input[role='combobox']").first
        name_input.click(force=True)
        name_input.fill(name)
        self.page.wait_for_timeout(500)

        # Reveal the mapping row - required fields only appear after "Add Row"
        self.page.locator("button").filter(has_text="Add Row").click(force=True)
        self.page.wait_for_timeout(1000)

        # Row comboboxes in DOM order: [0]=mapping name (disabled), [1]=Material Type, [2]=Station ID
        combos = self.page.locator(".MuiDialogContent-root input[role='combobox']")

        # Material Type -> picking it auto-fills the (read-only) Production Unit
        combos.nth(1).click(force=True)
        self.page.wait_for_timeout(700)
        self._select_option(f"Material Type for '{name}'", index=0)
        self.page.wait_for_timeout(1000)

        # Station ID - distinct per mapping, see the docstring.
        combos.nth(2).click(force=True)
        self.page.wait_for_timeout(900)
        chosen = self._select_option(
            f"Station ID for '{name}'", station=station_id, index=station_index
        )
        self.page.wait_for_timeout(500)
        self.selected_station_ids[name] = chosen

        self.page.locator(".MuiDialogActions-root button").last.click(force=True)
        wait_for_modal_close(self.page, f"Create station mapping '{name}'", timeout=3000)
        self.verify_station_mapping_exists(name)

    # ── Workflow CRUD ─────────────────────────────────────────────────────────

    #: Station-selection mode that exposes the mapped stations.
    STATION_MODE_MAPPING = "Mapping-based"

    #: Per-section settings for wizard step 3. Both sections render their
    #: controls from the start in DOM order Pickup then Drop, so ``index``
    #: selects between the two identical-looking control groups.
    #:
    #: ACTION TYPE has no default selection - the wizard leaves all three
    #: options unchecked - so it must be set explicitly. Its radio *values*
    #: differ from the visible labels ("LIFT" is shown as "Pick", "UNLIFT" as
    #: "Drop"), and the values are unique across the dialog, so they are the
    #: reliable thing to target. MANUAL appears in both sections and is not.
    STATION_SECTIONS = {
        "Pickup": {"index": 0, "action_value": "LIFT", "action_label": "Pick"},
        "Drop": {"index": 1, "action_value": "UNLIFT", "action_label": "Drop"},
    }

    def _select_radio(self, dialog, value, index, description):
        """Select the ``index``-th MUI radio carrying ``value``, by its label.

        MUI renders the real input visually hidden behind a styled span, so
        clicking the input - even forced - does not fire React's change handler.

        ``index`` is applied to the filtered label list, not inside ``filter``:
        a ``has=`` locator is re-resolved against each candidate element, so an
        ``.nth(1)`` there would look for a second input inside a single label
        and never match.
        """
        labels = dialog.locator(".MuiFormControlLabel-root").filter(
            has=self.page.locator(f"input[value='{value}']")
        )
        found = labels.count()
        if found <= index:
            raise AssertionError(
                f"{description}: expected at least {index + 1} radio(s) with "
                f"value={value!r}, found {found}."
            )
        labels.nth(index).click(force=True)
        self.page.wait_for_timeout(900)

    def _configure_station_section(self, section, station, station_type="mapping",
                                    point_station_mode="Manual", staging_area_mode="Manual"):
        """Configure one station section of the workflow wizard.

        ``section``      – "Pickup" or "Drop"
        ``station``      – mapping name (station_type="mapping") or a real
                           physical Station ID (station_type="static")
        ``station_type`` – "mapping" (default) or "static"

        Both modes fill the same required Autocomplete field - verified live,
        it is labelled "Station Name *" and lists physical Station IDs while
        Static is selected (the radio's default), and "Mapping ID" listing
        configured mappings once switched to Mapping-based. Static does NOT
        mean "any station"; it still requires picking one, just from the
        physical station list instead of the Station Mapping table.

        ``point_station_mode``/``staging_area_mode`` set this section's own
        Confirmation Mode toggles - each section (Pickup, Drop) renders an
        independent Point Station / Staging Area Auto-Manual pair, not one
        shared per workflow.
        """
        settings = self.STATION_SECTIONS[section]
        section_index = settings["index"]
        dialog = self.page.locator(".MuiDialog-container")

        # Expand the section.
        dialog.locator("button").filter(has_text=section).first.click(force=True)
        self.page.wait_for_timeout(800)

        if station_type == "mapping":
            # Switch from Static to Mapping-based.
            self._select_radio(
                dialog, "mapping_based", section_index,
                f"{section} 'Mapping-based' station selection",
            )

            # Pick the named mapping from the Mapping ID dropdown.
            mapping_combos = dialog.locator(".MuiFormControl-root").filter(
                has_text="Mapping ID"
            ).locator("input[role='combobox']")
            mapping_combos.nth(section_index).click(force=True)
            self.page.wait_for_timeout(900)

            option = self.page.get_by_role("option", name=station, exact=True)
            try:
                option.first.wait_for(state="visible", timeout=8000)
            except Exception:
                available = self.page.locator("li[role='option']").all_text_contents()
                raise AssertionError(
                    f"{section} station '{station}' is not in the Mapping ID dropdown. "
                    f"Available options: {[o.strip() for o in available] or 'none'}. "
                    f"Check that this station mapping exists in Processing Area "
                    f"'{self.page.url.rsplit('/', 1)[-1]}'."
                )
            option.first.click(force=True)
            self.page.wait_for_timeout(600)
        else:
            # Static: radio stays on its default. Still pick a real Station
            # ID from the "Station Name" Autocomplete - it's required here too.
            station_name_combos = dialog.locator(".MuiFormControl-root").filter(
                has_text="Station Name"
            ).locator("input[role='combobox']")
            station_name_combos.nth(section_index).click(force=True)
            self.page.wait_for_timeout(900)

            option = self.page.get_by_role("option", name=station, exact=True)
            try:
                option.first.wait_for(state="visible", timeout=8000)
            except Exception:
                available = self.page.locator("li[role='option']").all_text_contents()
                raise AssertionError(
                    f"{section} static station '{station}' is not in the Station "
                    f"Name dropdown. Available options: "
                    f"{[o.strip() for o in available] or 'none'}."
                )
            option.first.click(force=True)
            self.page.wait_for_timeout(600)

        # Confirmation Mode - independent Auto/Manual toggle pair, rendered
        # inside this section only (verified live: Step 3, not Step 2).
        self._set_confirmation_mode(dialog, "Point Station", point_station_mode, section_index)
        self._set_confirmation_mode(dialog, "Staging Area", staging_area_mode, section_index)

        # Set ACTION TYPE — required regardless of station type.
        self._select_radio(
            dialog, settings["action_value"], 0,
            f"{section} action type '{settings['action_label']}'",
        )
        action_input = self.page.locator(f"input[value='{settings['action_value']}']")
        if not action_input.first.is_checked():
            raise AssertionError(
                f"{section} action type '{settings['action_label']}' "
                f"(value={settings['action_value']}) did not become selected."
            )
    def _set_confirmation_mode(self, dialog, station_type_label, mode, section_index):
        """Click the Auto or Manual toggle for one Confirmation Mode row.

        Confirmation Mode is *not* a real ``<table>``/``<tr>`` despite the
        "STATION TYPE"/"MODE" column headers - each row is a ``<p>`` label
        (e.g. "Point Station") followed by a sibling ``<div>`` holding the
        Auto/Manual ``<button>``s. It also renders once per station section
        (Pickup, Drop), and expanding Drop does not collapse Pickup, so with
        both sections open the dialog holds two "Point Station" labels in
        Pickup-then-Drop DOM order - ``section_index`` (0=Pickup, 1=Drop)
        picks the right one, same indexing already used for the mapping radio.

        ``station_type_label`` – visible row label, e.g. "Point Station" or "Staging Area".
        ``mode``               – "Auto" or "Manual" (matches button text exactly).
        """
        label = dialog.get_by_text(station_type_label, exact=True).nth(section_index)
        button_row = label.locator("xpath=following-sibling::div[1]")
        button_row.get_by_role("button", name=mode, exact=True).click(force=True)
        self.page.wait_for_timeout(300)


    def add_workflow(self, name, pickup_station, drop_station,
                     pickup_type="mapping", drop_type="mapping",
                     point_station_mode="Manual", staging_area_mode="Manual"):
        """Drive the 4-step workflow wizard on the Workflow tab.

        point_station_mode / staging_area_mode:
            "Auto" or "Manual" — the Confirmation Mode toggle per station type row.
        pickup_type / drop_type: "mapping" or "static" (Step 3 station sections).
        """
        if pickup_type == "mapping" and drop_type == "mapping" and pickup_station == drop_station:
            raise ValueError(
                f"Pickup and Drop must be different mappings, both are "
                f"'{pickup_station}'. Set distinct station_mapping names in "
                f"config/test_data.toml."
            )

        track_ui_record(self.page, name, kind="row")
        self.page.locator("button").filter(has_text="Add").first.click(force=True)
        self.page.wait_for_timeout(1000)

        # Wizard 1 of 4: Order Types - select the "Order Material" card
        self.page.locator(".MuiDialog-container").get_by_text("Order Material", exact=True).first.click(force=True)
        self.page.wait_for_timeout(500)
        self.page.locator("#wf-dialog-next").click(force=True)
        self.page.wait_for_timeout(1000)

        # Wizard 2 of 4: Basics — name and consumption unit only. Confirmation
        # Mode is NOT here (verified live) - it renders inside each Pickup/
        # Drop section on Step 3, so it's set from _configure_station_section.
        self.page.locator("#wf-name").fill(name)
        self.page.wait_for_timeout(300)
        self.page.locator(".MuiDialog-container .MuiAutocomplete-input").last.click(force=True)
        self.page.wait_for_timeout(700)
        self.page.locator("li[role='option']").first.click(force=True)
        self.page.wait_for_timeout(500)

        self.page.locator("#wf-dialog-next").click(force=True)
        self.page.wait_for_timeout(1000)

        # Wizard 3 of 4: Material Order - Pickup and Drop stations, each with
        # its own Confirmation Mode toggles.
        self._configure_station_section(
            "Pickup", pickup_station, pickup_type, point_station_mode, staging_area_mode
        )
        self._configure_station_section(
            "Drop", drop_station, drop_type, point_station_mode, staging_area_mode
        )
        self.page.locator("#wf-dialog-next").click(force=True)
        self.page.wait_for_timeout(1000)

        # Wizard 4 of 4: Review - submit
        self.page.locator("#wf-dialog-create").click(force=True)
        wait_for_modal_close(self.page, f"Create workflow '{name}'", timeout=5000)
        expect(self.page.locator("tr").filter(has_text=name).first).to_be_visible(timeout=5000)
