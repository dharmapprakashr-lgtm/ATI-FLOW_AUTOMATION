# ATIFlow 2.0 — Test Coverage Documentation

**Release:** ATIFlow v2.0

**Document date:** 2026-09-29

**Scope:** Current working-tree pytest inventory, including uncommitted additions

**Reference:** User-provided ATIFlow coverage document dated 2026-09-25 (MTS-138)

**Stack verified locally:** Python 3.10 · pytest 9.1.1 · Playwright 1.61.0 · pytest-playwright 0.8.0 · PDF / Allure support

> **Last updated:** 2026-09-29 — Verified **483 collected cases** using pytest collection.
> Counts include parameter variants and Chromium cases. Collection confirms discovery,
> not passing behavior, requirements completeness, or release readiness.
> The full live suite was not executed as part of this documentation update.

---

## 1. Release Sign-Off

The supplied reference contains historical approvals. They are not treated as
approval of the current working tree or the newly added API/model coverage.

| Role | Approved by | Date | Current status |
| --- | --- | --- | --- |
| Test Manager | — | — | Pending current release review |
| Development Manager | — | — | Pending current release review |
| Product Manager | — | — | Pending current release review |

## 2. Coverage Summary

| Suite | Collected | Not marked skip | Marked skip | Cases containing runtime skip |
| --- | --- | --- | --- | --- |
| Common — shared browser checks | 26 | 26 | 0 | 0 |
| Admin — Processing Area, Settings & Notifications | 48 | 47 | 1 | 4 |
| Admin — Execution Source Config | 10 | 10 | 0 | 1 |
| UI — CRUD | 15 | 15 | 0 | 0 |
| UI — Requester | 21 | 20 | 1 | 1 |
| UI — Dispatcher | 18 | 17 | 1 | 10 |
| UI — Supervisor | 33 | 33 | 0 | 9 |
| UI — E2E | 2 | 2 | 0 | 1 |
| API — HTTP contract tests | 128 | 128 | 0 | 0 |
| API folder — MTS model/mock adapter | 182 | 182 | 0 | 0 |
| **TOTAL** | **483** | **480** | **3** | **26** |

### Current folder coverage

| Folder | Collected cases | Scope |
| --- | --- | --- |
| `tests/api/` | 310 | 128 HTTP contract cases and 182 MTS model/mock cases |
| `tests/common/` | 26 | Shared login, version, access, dashboards, security, NFR, and navigation |
| `tests/ui/` | 147 | Admin, CRUD, requester, dispatcher, supervisor, and E2E |
| **Total** | **483** | All current pytest cases |

```text
tests/
├── api/       # 310 cases; all API scripts remain directly in this folder
├── common/    # 26 shared browser cases
└── ui/        # 147 role/feature browser cases
```

The `ui` marker selects **173 browser cases** across `tests/ui/` and
`tests/common/`. Running only `pytest tests/ui` selects **147**, not the common
suite. Use `pytest tests/ui tests/common` or `pytest -m ui` for all browser tests.

Runtime-skip counts inspect test bodies only. Fixtures and helpers can introduce
additional skips or setup failures. Conditional cases are included in the
“Not marked skip” column; this is not a prediction of a run's pass/skip totals.

| Status | Meaning |
| --- | --- |
| ✅ Collected | Discovered by pytest without an unconditional skip marker; not a pass result. |
| ◐ Conditional | Test body contains a runtime skip for configuration or live-data conditions. |
| ⏭ Marked skip | Unconditional pytest skip marker is present. |
| Model/mock | Runs against a local simulation/model, with some network probes; does not establish deployed API/UI correctness. |

## 3. Test Environment & Configuration

| Item | Current configuration / source |
| --- | --- |
| Environment selection | TEST_ENV selects `config/environments/<env>.yaml`; default is qa. |
| Observed local configuration | qa; base URL https://192.168.6.32/login; 15,000 ms default timeout; headed browser; TLS verification bypass enabled. |
| Staging profile | config/environments/staging.yaml: empty base_url, headless true, 20,000 ms timeout, ignore_https_errors true. Supply BASE_URL when selecting staging. |
| Precedence | Environment/.env overrides YAML defaults; inspect config/environment.py for resolution. |
| Credentials | ADMIN_USERNAME / ADMIN_PASSWORD and role configuration; secret values intentionally omitted. |
| API configuration | MTS_BASE_URL / BASE_URL and MTS_TOKEN / API_BEARER_TOKEN; machine/mapping clients also support configured token-file lookup. Requirements vary by client. |
| Shared test data | config/test_data.toml, config/data.py, config/processing_area.py, config/credentials.py. |
| Browser scope | Counts reflect Chromium only; additional browser selection changes totals. |
| Reporting | Root conftest.py generates `reports/report_<timestamp>.pdf` unless --no-pdf is used. |

---

## 4. Common Tests — Login, Access, Dashboards, Version, Security & Navigation

**Path:** `tests/common/` · **7 test files** · **26 collected cases**

Shared browser checks retain the `ui` marker and use the root authentication,
environment validation, cleanup, and ordering hooks. Their original relative
execution order is preserved; the folder move does not change their assertions.

### test_login.py

**File:** [test_login.py](../tests/common/test_login.py) · **Collected cases:** 2

| ID | Function | Coverage / assertion intent | Cases | Status |
| --- | --- | --- | --- | --- |
| TC_AUTH_001 | `test_admin_login_with_valid_credentials` | TC_AUTH_001 — Admin logs in with valid credentials | 1 | ✅ Collected |
| TC_AUTH_002 | `test_login_rejected_with_invalid_credentials` | TC_AUTH_002 — Login is rejected with an invalid password | 1 | ✅ Collected |

### test_application_version.py

**File:** [test_application_version.py](../tests/common/test_application_version.py) · **Collected cases:** 1

| ID | Function | Coverage / assertion intent | Cases | Status |
| --- | --- | --- | --- | --- |
| TC_SET_002 | `test_capture_displayed_atiflow_version` | TC_SET_002 — Capture the AtiFlow version displayed in the UI | 1 | ✅ Collected |

### test_access_control.py

**File:** [test_access_control.py](../tests/common/test_access_control.py) · **Collected cases:** 4

| ID | Function | Coverage / assertion intent | Cases | Status |
| --- | --- | --- | --- | --- |
| TC_AC_001 | `test_requester_cannot_reach_admin_routes_by_url` | TC_AC_001 — Requester cannot reach Admin routes by URL | 1 | ✅ Collected |
| TC_AC_002 | `test_dispatcher_cannot_reach_admin_configuration` | TC_AC_002 — Dispatcher cannot reach Admin configuration | 1 | ✅ Collected |
| TC_AC_003 | `test_supervisor_navigation_limited_to_permitted_areas` | TC_AC_003 — Supervisor navigation is limited to permitted areas | 1 | ✅ Collected |
| TC_AC_004 | `test_admin_sees_complete_navigation_tree` | TC_AC_004 — Admin sees the complete navigation tree | 1 | ✅ Collected |

### test_dashboard_common.py

**File:** [test_dashboard_common.py](../tests/common/test_dashboard_common.py) · **Collected cases:** 3

| ID | Function | Coverage / assertion intent | Cases | Status |
| --- | --- | --- | --- | --- |
| TC_DASH_ALL_001 | `test_live_updates_survive_network_interruption` | TC_DASH_ALL_001 — History recovers after an interrupted request and reopening | 1 | ✅ Collected |
| TC_DASH_ALL_002 | `test_empty_loading_and_error_states_render_correctly` | TC_DASH_ALL_002 — History shows loading, empty and request-error states | 1 | ✅ Collected |
| TC_DASH_ALL_003 | `test_timestamps_use_correct_timezone_and_format` | TC_DASH_ALL_003 — UTC history timestamps render in the expected local timezone | 1 | ✅ Collected |

### test_security.py

**File:** [test_security.py](../tests/common/test_security.py) · **Collected cases:** 2

| ID | Function | Coverage / assertion intent | Cases | Status |
| --- | --- | --- | --- | --- |
| TC_SEC_001 | `test_stored_xss_payloads_are_escaped_everywhere` | TC_SEC_001 — Stored XSS payloads are escaped everywhere | 1 | ✅ Collected |
| TC_SEC_002 | `test_injection_payloads_in_search_and_forms_are_safe` | TC_SEC_002 — Injection payloads in search and forms are safe | 1 | ✅ Collected |

### test_nfr.py

**File:** [test_nfr.py](../tests/common/test_nfr.py) · **Collected cases:** 1

| ID | Function | Coverage / assertion intent | Cases | Status |
| --- | --- | --- | --- | --- |
| TC_NFR_001 | `test_supported_browsers_and_shopfloor_viewports_render` | TC_NFR_001 — Supported viewports render the admin console | 1 | ✅ Collected |

### test_ui_navigation.py

**File:** [test_ui_navigation.py](../tests/common/test_ui_navigation.py) · **Collected cases:** 13

| ID | Function | Coverage / assertion intent | Cases | Status |
| --- | --- | --- | --- | --- |
| TC_UI_001 | `test_every_navigation_item_routes_to_correct_screen` | TC_UI_001 — Every navigation item routes to the correct screen | 1 | ✅ Collected |
| TC_UI_002 | `test_context_preserved_between_processing_area_submodules` | TC_UI_002 — Context preserved between Processing Area submodules | 1 | ✅ Collected |
| TC_UI_003 | `test_browser_back_and_forward_keep_app_consistent` | TC_UI_003 — Browser Back and Forward keep the app consistent | 1 | ✅ Collected |
| TC_UI_004 | `test_browser_refresh_midform_does_not_break_app` | TC_UI_004 — Browser refresh mid-form does not break the app | 1 | ✅ Collected |
| TC_UI_005 | `test_navigating_away_from_dirty_form_is_predictable` | TC_UI_005 — Navigating away from a dirty form is predictable | 1 | ✅ Collected |
| TC_UI_006 | `test_field_labels_required_markers_and_tab_order` | TC_UI_006 — Field labels, required markers and tab order | 1 | ✅ Collected |
| TC_UI_007 | `test_save_is_protected_against_double_click` | TC_UI_007 — Save is protected against double-click | 1 | ✅ Collected |
| TC_UI_008 | `test_success_messages_appear_readable_and_dismissible` | TC_UI_008 — Success messages appear, are readable, and are dismissible | 1 | ✅ Collected |
| TC_UI_009 | `test_error_messages_are_operator_readable` | TC_UI_009 — Error messages are operator-readable | 1 | ✅ Collected |
| TC_UI_010 | `test_tables_render_correctly_with_long_values_and_many_rows` | TC_UI_010 — Tables render correctly with long values and many rows | 1 | ✅ Collected |
| TC_UI_012 | `test_dropdowns_reflect_records_created_in_same_session` | TC_UI_012 — Dropdowns reflect records created in the same session | 1 | ✅ Collected |
| TC_UI_013 | `test_screens_usable_at_shopfloor_viewport_sizes` | TC_UI_013 — Screens usable at shopfloor viewport sizes | 1 | ✅ Collected |
| TC_UI_014 | `test_page_and_browser_tab_titles_are_correct` | TC_UI_014 — Page and browser tab titles are correct | 1 | ✅ Collected |

---

## 5. Admin — Processing Area, Settings & Notifications

Settings and notifications now live in `test_18_setting.py` and `test_19_notification.py`. Numbering gaps reflect removed/moved files; they are not missing pytest collection. CRUD cases have a separate `tests/ui/crud/` suite.

### test_01_processing_area_creation.py

**File:** [test_01_processing_area_creation.py](../tests/ui/admin/processing_area/test_01_processing_area_creation.py) · **Collected cases:** 2

| ID | Function | Coverage / assertion intent | Cases | Status |
| --- | --- | --- | --- | --- |
| — | `test_processing_area_exists_in_sidebar` | TC_PA_001v — Processing Area exists in the sidebar | 1 | ✅ Collected |
| — | `test_navigating_to_area_shows_tab_strip` | TC_PA_002v — Navigating to the Processing Area renders the tab strip | 1 | ✅ Collected |

### test_02_area_tabs_visibility.py

**File:** [test_02_area_tabs_visibility.py](../tests/ui/admin/processing_area/test_02_area_tabs_visibility.py) · **Collected cases:** 8

| ID | Function | Coverage / assertion intent | Cases | Status |
| --- | --- | --- | --- | --- |
| TC_PA_TAB_001 | `test_materials_tab_visible` | TC_PA_TAB_001 — 'Materials' tab is visible and enabled | 1 | ✅ Collected |
| TC_PA_TAB_002 | `test_containers_tab_visible` | TC_PA_TAB_002 — 'Containers' tab is visible and enabled | 1 | ✅ Collected |
| TC_PA_TAB_003 | `test_workflow_tab_visible` | TC_PA_TAB_003 — 'Workflow' tab is visible and enabled | 1 | ✅ Collected |
| TC_PA_TAB_004 | `test_wip_inventory_tab_visible` | TC_PA_TAB_004 — 'WIP Inventory' tab is visible and enabled | 1 | ✅ Collected |
| TC_PA_TAB_005 | `test_staging_area_tab_visible` | TC_PA_TAB_005 — 'Staging Area' tab is visible and enabled | 1 | ✅ Collected |
| TC_PA_TAB_006 | `test_station_mapping_tab_visible` | TC_PA_TAB_006 — 'Station Mapping' tab is visible and enabled | 1 | ✅ Collected |
| TC_PA_TAB_007 | `test_machine_names_tab_visible` | TC_PA_TAB_007 — 'Machine Names' tab is visible and enabled | 1 | ✅ Collected |
| TC_PA_TAB_ALL | `test_all_tabs_visible_in_one_pass` | TC_PA_TAB_ALL — All 7 tabs can be opened in sequence | 1 | ✅ Collected |

### test_03_material_container.py

**File:** [test_03_material_container.py](../tests/ui/admin/processing_area/test_03_material_container.py) · **Collected cases:** 1

| ID | Function | Coverage / assertion intent | Cases | Status |
| --- | --- | --- | --- | --- |
| — | `test_create_material_and_container` | Create a fresh Processing Area with one material and one container | 1 | ✅ Collected |

### test_04_material_container_validation.py

**File:** [test_04_material_container_validation.py](../tests/ui/admin/processing_area/test_04_material_container_validation.py) · **Collected cases:** 4

| ID | Function | Coverage / assertion intent | Cases | Status |
| --- | --- | --- | --- | --- |
| — | `test_baseline_material_exists` | TC_MAT_001v — Baseline material exists after creation | 1 | ✅ Collected |
| — | `test_baseline_container_exists` | TC_CON_001v — Baseline container exists after creation | 1 | ✅ Collected |
| TC_MAT_002 | `test_material_scoped_to_own_processing_area` | TC_MAT_002 — Material is scoped to its own Processing Area | 1 | ✅ Collected |
| TC_CON_002 | `test_container_numeric_fields_reject_invalid_values` | TC_CON_002 — Container numeric fields reject invalid values | 1 | ✅ Collected |

### test_06_machine_name.py

**File:** [test_06_machine_name.py](../tests/ui/admin/processing_area/test_06_machine_name.py) · **Collected cases:** 1

| ID | Function | Coverage / assertion intent | Cases | Status |
| --- | --- | --- | --- | --- |
| — | `test_create_machines` | Create the production and consumption machines | 1 | ✅ Collected |

### test_07_machine_name_validation.py

**File:** [test_07_machine_name_validation.py](../tests/ui/admin/processing_area/test_07_machine_name_validation.py) · **Collected cases:** 2

| ID | Function | Coverage / assertion intent | Cases | Status |
| --- | --- | --- | --- | --- |
| — | `test_baseline_machines_exist` | TC_MCH_001v — Baseline machines exist after creation | 1 | ✅ Collected |
| TC_MCH_002 | `test_machine_name_uniqueness_scope` | TC_MCH_002 — Duplicate name is rejected within one area | 1 | ✅ Collected |

### test_09_station_mapping.py

**File:** [test_09_station_mapping.py](../tests/ui/admin/processing_area/test_09_station_mapping.py) · **Collected cases:** 1

| ID | Function | Coverage / assertion intent | Cases | Status |
| --- | --- | --- | --- | --- |
| — | `test_create_station_mappings` | Create pickup and drop station mappings on different stations | 1 | ✅ Collected |

### test_10_station_mapping_validation.py

**File:** [test_10_station_mapping_validation.py](../tests/ui/admin/processing_area/test_10_station_mapping_validation.py) · **Collected cases:** 4

| ID | Function | Coverage / assertion intent | Cases | Status |
| --- | --- | --- | --- | --- |
| — | `test_baseline_mappings_exist` | TC_STM_001v — Baseline station mappings exist after creation | 1 | ✅ Collected |
| TC_STM_002 | `test_mapping_referencing_deleted_station_or_machine` | TC_STM_002 — Mapping referencing a deleted station or machine | 1 | ⏭ Marked skip |
| TC_STM_003 | `test_duplicate_mapping_is_rejected` | TC_STM_003 — Duplicate station mapping is rejected | 1 | ✅ Collected |
| TC_STM_004 | `test_incomplete_mapping_cannot_be_saved` | TC_STM_004 — Incomplete station mapping cannot be saved | 1 | ✅ Collected |

### test_12_workflow.py

**File:** [test_12_workflow.py](../tests/ui/admin/processing_area/test_12_workflow.py) · **Collected cases:** 1

| ID | Function | Coverage / assertion intent | Cases | Status |
| --- | --- | --- | --- | --- |
| — | `test_create_workflow` | Create all workflows with their pickup/drop station types | 1 | ✅ Collected |

### test_14_area_validation.py

**File:** [test_14_area_validation.py](../tests/ui/admin/processing_area/test_14_area_validation.py) · **Collected cases:** 8

| ID | Function | Coverage / assertion intent | Cases | Status |
| --- | --- | --- | --- | --- |
| TC_PA_006 | `test_duplicate_processing_area_name_rejected` | TC_PA_006 — Duplicate Processing Area name is rejected | 1 | ✅ Collected |
| TC_PA_007 | `test_name_length_boundaries` | TC_PA_007 — Name length boundaries (1 char, 255 chars, 256 chars) | 1 | ✅ Collected |
| TC_PA_008 | `test_blank_or_whitespace_only_name_rejected` | TC_PA_008 — Blank or whitespace-only name is rejected | 1 | ✅ Collected |
| TC_PA_009 | `test_special_characters_and_unicode_handled` | TC_PA_009 — Special characters and unicode handled without server error | 1 | ✅ Collected |
| TC_PA_010 | `test_delete_confirmation_can_be_cancelled` | TC_PA_010 — Delete confirmation can be cancelled | 1 | ✅ Collected |
| TC_PA_011 | `test_cancel_on_create_form_discards_input` | TC_PA_011 — Cancel on the create form discards input | 1 | ✅ Collected |
| TC_PA_012 | `test_list_search_sort_pagination_with_realistic_volume` | TC_PA_012 — List search with a realistic record count | 1 | ✅ Collected |
| TC_PA_013 | `test_two_admins_editing_same_area_do_not_lose_data` | TC_PA_013 — Two admins editing the same area do not silently lose data | 1 | ✅ Collected |

### test_15_staging_area.py

**File:** [test_15_staging_area.py](../tests/ui/admin/processing_area/test_15_staging_area.py) · **Collected cases:** 2

| ID | Function | Coverage / assertion intent | Cases | Status |
| --- | --- | --- | --- | --- |
| TC_STG_001 | `test_staging_area_shows_cell_grid_and_legend` | TC_STG_001 — Staging Area renders as a colour-coded cell grid with a legend | 1 | ✅ Collected |
| TC_STG_003 | `test_manage_cell_fields` | TC_STG_003 — Managing a cell exposes Cell State and Filled-with-Material fields | 1 | ◐ Conditional |

### test_17_material_container_bulk_upload.py

**File:** [test_17_material_container_bulk_upload.py](../tests/ui/admin/processing_area/test_17_material_container_bulk_upload.py) · **Collected cases:** 2

| ID | Function | Coverage / assertion intent | Cases | Status |
| --- | --- | --- | --- | --- |
| TC_MAT_BULK | `test_bulk_upload_materials_from_csv` | TC_MAT_BULK — Bulk-upload materials from a CSV file | 1 | ✅ Collected |
| TC_CON_BULK | `test_bulk_upload_containers_from_csv` | TC_CON_BULK — Bulk-upload containers from a CSV file | 1 | ✅ Collected |

### test_18_setting.py

**File:** [test_18_setting.py](../tests/ui/admin/processing_area/test_18_setting.py) · **Collected cases:** 6

| ID | Function | Coverage / assertion intent | Cases | Status |
| --- | --- | --- | --- | --- |
| TC_SET_FM_001 | `test_fleet_manager_connection_details` | TC_SET_FM_001 — Fleet Manager shows a configured host and last-sync value | 1 | ✅ Collected |
| TC_SET_FM_002 | `test_fleet_manager_connection_is_healthy` | TC_SET_FM_002 — Fleet Manager connection is healthy | 1 | ✅ Collected |
| TC_SET_MES_001 | `test_mes_connection_endpoint_details` | TC_SET_MES_001 — MES shows valid AMR and BOM endpoint URLs | 1 | ✅ Collected |
| TC_SET_MES_002 | `test_mes_connection_is_healthy` | TC_SET_MES_002 — MES connection is healthy | 1 | ✅ Collected |
| TC_SET_001 | `test_connection_cards_show_resolved_status` | TC_SET_001 — Settings renders both connection cards without placeholders | 1 | ✅ Collected |
| TC_SET_003 | `test_connection_status_after_reopening_panel` | TC_SET_003 — Reopening Connections renders both statuses again | 1 | ✅ Collected |

### test_19_notification.py

**File:** [test_19_notification.py](../tests/ui/admin/processing_area/test_19_notification.py) · **Collected cases:** 6

| ID | Function | Coverage / assertion intent | Cases | Status |
| --- | --- | --- | --- | --- |
| TC_ADMIN_NOTIF_001 | `test_notifications_panel_opens` | TC_ADMIN_NOTIF_001 — Sidebar Notifications opens the drawer | 1 | ✅ Collected |
| TC_ADMIN_NOTIF_002 | `test_notifications_panel_closes` | TC_ADMIN_NOTIF_002 — Notifications drawer closes with Escape | 1 | ✅ Collected |
| TC_ADMIN_NOTIF_003 | `test_notification_count_matches_cards` | TC_ADMIN_NOTIF_003 — Badge count matches the listed notifications | 1 | ✅ Collected |
| TC_ADMIN_NOTIF_004 | `test_unreachable_alert_details` | TC_ADMIN_NOTIF_004 — {service} unreachable alert includes details and time | 2 | ◐ Conditional |
| TC_ADMIN_NOTIF_005 | `test_clear_all_control` | TC_ADMIN_NOTIF_005 — Clear all is available when notifications exist | 1 | ◐ Conditional |

<details>
<summary>Collected parameter variants</summary>

- `test_unreachable_alert_details[chromium-fleet_manager]`
- `test_unreachable_alert_details[chromium-mes]`

</details>

---

## 6. Admin — Execution Source Config

### test_create_dispatcher.py

**File:** [test_create_dispatcher.py](../tests/ui/admin/execution_source_config/test_create_dispatcher.py) · **Collected cases:** 1

| ID | Function | Coverage / assertion intent | Cases | Status |
| --- | --- | --- | --- | --- |
| — | `test_create_dispatcher_device` | Create a dispatcher device bound to a station and staging area | 1 | ✅ Collected |

### test_create_requester.py

**File:** [test_create_requester.py](../tests/ui/admin/execution_source_config/test_create_requester.py) · **Collected cases:** 1

| ID | Function | Coverage / assertion intent | Cases | Status |
| --- | --- | --- | --- | --- |
| — | `test_create_requester_device` | Create a requester device bound to the suite workflow and machine | 1 | ✅ Collected |

### test_create_supervisor.py

**File:** [test_create_supervisor.py](../tests/ui/admin/execution_source_config/test_create_supervisor.py) · **Collected cases:** 1

| ID | Function | Coverage / assertion intent | Cases | Status |
| --- | --- | --- | --- | --- |
| — | `test_create_supervisor_device` | Create a supervisor device bound to the suite Processing Area | 1 | ✅ Collected |

### test_exec_config_validation.py

**File:** [test_exec_config_validation.py](../tests/ui/admin/execution_source_config/test_exec_config_validation.py) · **Collected cases:** 5

| ID | Function | Coverage / assertion intent | Cases | Status |
| --- | --- | --- | --- | --- |
| TC_RQD_003 | `test_duplicate_device_name_or_identifier_rejected` | TC_RQD_003 — Duplicate device name or identifier is rejected | 1 | ✅ Collected |
| TC_RQD_004 | `test_newly_provisioned_device_can_actually_login` | TC_RQD_004 — A newly provisioned device can actually log in | 1 | ✅ Collected |
| TC_MES_002 | `test_invalid_mes_parameters_fail_cleanly` | TC_MES_002 — Invalid MES parameters fail cleanly | 1 | ◐ Conditional |
| TC_DSP_002 | `test_dispatcher_only_receives_tasks_from_assigned_scope` | TC_DSP_002 — Dispatcher only receives tasks from its assigned scope | 1 | ✅ Collected |
| TC_SPD_002 | `test_supervisor_scope_spans_configured_processing_areas` | TC_SPD_002 — Supervisor scope spans the configured Processing Areas | 1 | ✅ Collected |

### test_mes_config.py

**File:** [test_mes_config.py](../tests/ui/admin/execution_source_config/test_mes_config.py) · **Collected cases:** 2

| ID | Function | Coverage / assertion intent | Cases | Status |
| --- | --- | --- | --- | --- |
| — | `test_all_tabs_present` | All four Execution Source Config tabs render with the expected labels | 1 | ✅ Collected |
| — | `test_mes_tab_activates` | MES tab activates when selected | 1 | ✅ Collected |

---

## 7. CRUD & API/UI Consistency

### test_01_processing_area.py

**File:** [test_01_processing_area.py](../tests/ui/crud/test_01_processing_area.py) · **Collected cases:** 2

| ID | Function | Coverage / assertion intent | Cases | Status |
| --- | --- | --- | --- | --- |
| — | `test_area_edit_and_delete` | Create, rename and delete a throwaway Processing Area | 1 | ✅ Collected |
| — | `test_delete_absent_area_is_noop` | Deleting an absent Processing Area is a no-op | 1 | ✅ Collected |

### test_02_material_container.py

**File:** [test_02_material_container.py](../tests/ui/crud/test_02_material_container.py) · **Collected cases:** 2

| ID | Function | Coverage / assertion intent | Cases | Status |
| --- | --- | --- | --- | --- |
| TC_MAT_CRUD | `test_material_create_and_delete` | TC_MAT_CRUD — Material create and delete lifecycle | 1 | ✅ Collected |
| TC_CON_CRUD | `test_container_create_and_delete` | TC_CON_CRUD — Container create and delete lifecycle | 1 | ✅ Collected |

### test_03_machine.py

**File:** [test_03_machine.py](../tests/ui/crud/test_03_machine.py) · **Collected cases:** 1

| ID | Function | Coverage / assertion intent | Cases | Status |
| --- | --- | --- | --- | --- |
| TC_MCH_CRUD | `test_machine_create_and_delete` | TC_MCH_CRUD — Machine create and delete lifecycle | 1 | ✅ Collected |

### test_04_station_mapping.py

**File:** [test_04_station_mapping.py](../tests/ui/crud/test_04_station_mapping.py) · **Collected cases:** 1

| ID | Function | Coverage / assertion intent | Cases | Status |
| --- | --- | --- | --- | --- |
| TC_STM_CRUD | `test_station_mapping_create_and_delete` | TC_STM_CRUD — Station mapping create and delete lifecycle | 1 | ✅ Collected |

### test_05_devices.py

**File:** [test_05_devices.py](../tests/ui/crud/test_05_devices.py) · **Collected cases:** 3

| ID | Function | Coverage / assertion intent | Cases | Status |
| --- | --- | --- | --- | --- |
| — | `test_requester_device_lifecycle` | Create, edit and delete a throwaway requester device | 1 | ✅ Collected |
| — | `test_dispatcher_device_lifecycle` | Create, edit and delete a throwaway dispatcher device | 1 | ✅ Collected |
| — | `test_supervisor_device_lifecycle` | Create, edit and delete a throwaway supervisor device | 1 | ✅ Collected |

### test_machine_api_ui.py

**File:** [test_machine_api_ui.py](../tests/ui/crud/test_machine_api_ui.py) · **Collected cases:** 6

| ID | Function | Coverage / assertion intent | Cases | Status |
| --- | --- | --- | --- | --- |
| — | `test_ui_create_persists_in_api_and_after_reload` | Ui create persists in api and after reload | 2 | ✅ Collected |
| — | `test_api_create_update_delete_reflected_in_ui` | Api create update delete reflected in ui | 1 | ✅ Collected |
| — | `test_ui_delete_persists_in_api_and_after_reload` | Ui delete persists in api and after reload | 1 | ✅ Collected |
| — | `test_cancel_creation_does_not_persist` | Cancel creation does not persist | 1 | ✅ Collected |
| — | `test_machine_table_is_scoped_to_selected_area` | Machine table is scoped to selected area | 1 | ✅ Collected |

<details>
<summary>Collected parameter variants</summary>

- `test_ui_create_persists_in_api_and_after_reload[chromium-production_type-Production Type]`
- `test_ui_create_persists_in_api_and_after_reload[chromium-consumption_type-Consumption Type]`

</details>

---

## 8. Requester

### test_00_login.py

**File:** [test_00_login.py](../tests/ui/requester/test_00_login.py) · **Collected cases:** 2

| ID | Function | Coverage / assertion intent | Cases | Status |
| --- | --- | --- | --- | --- |
| TC_LOGIN_REQ_001 | `test_requester_device_login_with_valid_credentials` | TC_LOGIN_REQ_001 — Admin-provisioned requester device logs in | 1 | ✅ Collected |
| TC_LOGIN_REQ_002 | `test_requester_device_login_rejected_with_invalid_credentials` | TC_LOGIN_REQ_002 — Requester login is rejected with an invalid password | 1 | ✅ Collected |

### test_01_staging_area_matches_bound_cells.py

**File:** [test_01_staging_area_matches_bound_cells.py](../tests/ui/requester/test_01_staging_area_matches_bound_cells.py) · **Collected cases:** 1

| ID | Function | Coverage / assertion intent | Cases | Status |
| --- | --- | --- | --- | --- |
| — | `test_staging_area_matches_bound_cells` | Staging Area card shows the bound area with its real cell grid | 1 | ✅ Collected |

### test_02_machine_dropdown_switches_context.py

**File:** [test_02_machine_dropdown_switches_context.py](../tests/ui/requester/test_02_machine_dropdown_switches_context.py) · **Collected cases:** 1

| ID | Function | Coverage / assertion intent | Cases | Status |
| --- | --- | --- | --- | --- |
| — | `test_machine_dropdown_switches_context` | Machine dropdown switches context | 1 | ⏭ Marked skip |

### test_03_wizard_loads_with_machine_and_workflow.py

**File:** [test_03_wizard_loads_with_machine_and_workflow.py](../tests/ui/requester/test_03_wizard_loads_with_machine_and_workflow.py) · **Collected cases:** 1

| ID | Function | Coverage / assertion intent | Cases | Status |
| --- | --- | --- | --- | --- |
| — | `test_wizard_loads_with_machine_and_workflow` | Make New Request wizard loads in its empty Step 1 state | 1 | ✅ Collected |

### test_04_staging_area_search_filters.py

**File:** [test_04_staging_area_search_filters.py](../tests/ui/requester/test_04_staging_area_search_filters.py) · **Collected cases:** 1

| ID | Function | Coverage / assertion intent | Cases | Status |
| --- | --- | --- | --- | --- |
| — | `test_staging_area_search_filters` | Search box filters the Staging Area card grid | 1 | ✅ Collected |

### test_05_staging_area_utilisation_bar_accurate.py

**File:** [test_05_staging_area_utilisation_bar_accurate.py](../tests/ui/requester/test_05_staging_area_utilisation_bar_accurate.py) · **Collected cases:** 1

| ID | Function | Coverage / assertion intent | Cases | Status |
| --- | --- | --- | --- | --- |
| — | `test_staging_area_utilisation_bar_accurate` | Utilisation bar's fill accurately reflects its own 'X/Y' label | 1 | ✅ Collected |

### test_06_workflow_dropdown_switches_context.py

**File:** [test_06_workflow_dropdown_switches_context.py](../tests/ui/requester/test_06_workflow_dropdown_switches_context.py) · **Collected cases:** 1

| ID | Function | Coverage / assertion intent | Cases | Status |
| --- | --- | --- | --- | --- |
| — | `test_workflow_dropdown_switches_context` | Selecting a different workflow updates the sidebar context | 1 | ✅ Collected |

### test_07_request_history_sort_filter.py

**File:** [test_07_request_history_sort_filter.py](../tests/ui/requester/test_07_request_history_sort_filter.py) · **Collected cases:** 2

| ID | Function | Coverage / assertion intent | Cases | Status |
| --- | --- | --- | --- | --- |
| — | `test_request_history_sort_filter` | Request History sort control actually reorders the table | 1 | ✅ Collected |
| — | `test_search_requester_history` | Request History search box filters by component/SKU code | 1 | ✅ Collected |

### test_08_sku_search_by_material_code.py

**File:** [test_08_sku_search_by_material_code.py](../tests/ui/requester/test_08_sku_search_by_material_code.py) · **Collected cases:** 1

| ID | Function | Coverage / assertion intent | Cases | Status |
| --- | --- | --- | --- | --- |
| — | `test_sku_search_by_material_code` | Searching a material code returns the matching SKU | 1 | ✅ Collected |

### test_09_staging_area_fleet_filter.py

**File:** [test_09_staging_area_fleet_filter.py](../tests/ui/requester/test_09_staging_area_fleet_filter.py) · **Collected cases:** 1

| ID | Function | Coverage / assertion intent | Cases | Status |
| --- | --- | --- | --- | --- |
| — | `test_staging_area_fleet_filter` | 'All Fleets' dropdown filters Staging Area cards by fleet | 1 | ✅ Collected |

### test_10_selecting_sku_loads_sub_sku_rows.py

**File:** [test_10_selecting_sku_loads_sub_sku_rows.py](../tests/ui/requester/test_10_selecting_sku_loads_sub_sku_rows.py) · **Collected cases:** 1

| ID | Function | Coverage / assertion intent | Cases | Status |
| --- | --- | --- | --- | --- |
| — | `test_selecting_sku_loads_sub_sku_rows` | Selecting a SKU populates the Sub-SKU column with rows | 1 | ✅ Collected |

### test_11_add_items_increment_decrement.py

**File:** [test_11_add_items_increment_decrement.py](../tests/ui/requester/test_11_add_items_increment_decrement.py) · **Collected cases:** 1

| ID | Function | Coverage / assertion intent | Cases | Status |
| --- | --- | --- | --- | --- |
| — | `test_add_items_increment_decrement` | '+' and '-' increment and decrement a Sub-SKU's Add Items count | 1 | ✅ Collected |

### test_12_quantity_cannot_exceed_available.py

**File:** [test_12_quantity_cannot_exceed_available.py](../tests/ui/requester/test_12_quantity_cannot_exceed_available.py) · **Collected cases:** 1

| ID | Function | Coverage / assertion intent | Cases | Status |
| --- | --- | --- | --- | --- |
| — | `test_quantity_cannot_exceed_available` | Quantity cannot be pushed past the 'X Available' figure | 1 | ✅ Collected |

### test_13_zero_available_row_disabled.py

**File:** [test_13_zero_available_row_disabled.py](../tests/ui/requester/test_13_zero_available_row_disabled.py) · **Collected cases:** 1

| ID | Function | Coverage / assertion intent | Cases | Status |
| --- | --- | --- | --- | --- |
| — | `test_zero_available_row_disabled` | A '0 Available' Sub-SKU row keeps its '+' control disabled | 1 | ✅ Collected |

### test_14_next_button_enable_and_bottom_summary.py

**File:** [test_14_next_button_enable_and_bottom_summary.py](../tests/ui/requester/test_14_next_button_enable_and_bottom_summary.py) · **Collected cases:** 1

| ID | Function | Coverage / assertion intent | Cases | Status |
| --- | --- | --- | --- | --- |
| — | `test_next_button_enable_and_bottom_summary` | Adding an item swaps the footer message and enables Next | 1 | ✅ Collected |

### test_15_advance_to_request_summary_step.py

**File:** [test_15_advance_to_request_summary_step.py](../tests/ui/requester/test_15_advance_to_request_summary_step.py) · **Collected cases:** 1

| ID | Function | Coverage / assertion intent | Cases | Status |
| --- | --- | --- | --- | --- |
| — | `test_advance_to_request_summary_step` | Next advances from Request Material to Request Summary | 1 | ✅ Collected |

### test_16_request_summary_reflects_selection.py

**File:** [test_16_request_summary_reflects_selection.py](../tests/ui/requester/test_16_request_summary_reflects_selection.py) · **Collected cases:** 1

| ID | Function | Coverage / assertion intent | Cases | Status |
| --- | --- | --- | --- | --- |
| — | `test_request_summary_reflects_selection` | Request Summary reflects exactly what was added in Step 1 | 1 | ✅ Collected |

### test_17_submit_shows_confirmation.py

**File:** [test_17_submit_shows_confirmation.py](../tests/ui/requester/test_17_submit_shows_confirmation.py) · **Collected cases:** 1

| ID | Function | Coverage / assertion intent | Cases | Status |
| --- | --- | --- | --- | --- |
| — | `test_submit_shows_confirmation` | Submitting the request shows the Step 3 Confirmation screen | 1 | ✅ Collected |

### test_18_cancel_requested_order.py

**File:** [test_18_cancel_requested_order.py](../tests/ui/requester/test_18_cancel_requested_order.py) · **Collected cases:** 1

| ID | Function | Coverage / assertion intent | Cases | Status |
| --- | --- | --- | --- | --- |
| — | `test_cancel_requested_order` | A Requested order can be cancelled via the ACTIONS column ⊗ icon | 1 | ◐ Conditional |

---

## 9. Dispatcher

### test_00_login.py

**File:** [test_00_login.py](../tests/ui/dispatcher/test_00_login.py) · **Collected cases:** 2

| ID | Function | Coverage / assertion intent | Cases | Status |
| --- | --- | --- | --- | --- |
| TC_LOGIN_DISP_001 | `test_dispatcher_device_login_with_valid_credentials` | TC_LOGIN_DISP_001 — Admin-provisioned dispatcher device logs in | 1 | ✅ Collected |
| TC_LOGIN_DISP_002 | `test_dispatcher_device_login_rejected_with_invalid_credentials` | TC_LOGIN_DISP_002 — Dispatcher login is rejected with an invalid password | 1 | ✅ Collected |

### test_01_dashboard_loads_with_bound_station.py

**File:** [test_01_dashboard_loads_with_bound_station.py](../tests/ui/dispatcher/test_01_dashboard_loads_with_bound_station.py) · **Collected cases:** 1

| ID | Function | Coverage / assertion intent | Cases | Status |
| --- | --- | --- | --- | --- |
| — | `test_dashboard_loads_with_bound_station` | Dispatcher lands on the Requests screen scoped to its default bound station | 1 | ✅ Collected |

### test_02_station_dropdown_lists_bound_stations.py

**File:** [test_02_station_dropdown_lists_bound_stations.py](../tests/ui/dispatcher/test_02_station_dropdown_lists_bound_stations.py) · **Collected cases:** 1

| ID | Function | Coverage / assertion intent | Cases | Status |
| --- | --- | --- | --- | --- |
| — | `test_station_dropdown_lists_bound_stations` | Station dropdown lists only this device's bound stations | 1 | ✅ Collected |

### test_03_switching_station_updates_breadcrumb_and_list.py

**File:** [test_03_switching_station_updates_breadcrumb_and_list.py](../tests/ui/dispatcher/test_03_switching_station_updates_breadcrumb_and_list.py) · **Collected cases:** 1

| ID | Function | Coverage / assertion intent | Cases | Status |
| --- | --- | --- | --- | --- |
| — | `test_switching_station_updates_breadcrumb_and_list` | Selecting another bound station re-scopes the breadcrumb and the queue | 1 | ✅ Collected |

### test_04_sort_dropdown_toggles_newest_oldest.py

**File:** [test_04_sort_dropdown_toggles_newest_oldest.py](../tests/ui/dispatcher/test_04_sort_dropdown_toggles_newest_oldest.py) · **Collected cases:** 1

| ID | Function | Coverage / assertion intent | Cases | Status |
| --- | --- | --- | --- | --- |
| — | `test_sort_dropdown_toggles_newest_oldest` | The sort control actually re-orders the queue by Request Time | 1 | ◐ Conditional |

### test_05_search_by_id_no_filters_table.py

**File:** [test_05_search_by_id_no_filters_table.py](../tests/ui/dispatcher/test_05_search_by_id_no_filters_table.py) · **Collected cases:** 1

| ID | Function | Coverage / assertion intent | Cases | Status |
| --- | --- | --- | --- | --- |
| — | `test_search_by_id_no_filters_table` | Search box does not match the ID No. column (matches material code only) | 1 | ◐ Conditional |

### test_06_search_by_material_code_filters_table.py

**File:** [test_06_search_by_material_code_filters_table.py](../tests/ui/dispatcher/test_06_search_by_material_code_filters_table.py) · **Collected cases:** 1

| ID | Function | Coverage / assertion intent | Cases | Status |
| --- | --- | --- | --- | --- |
| — | `test_search_by_material_code_filters_table` | Searching a material code filters the queue to matching rows | 1 | ◐ Conditional |

### test_07_search_no_match_shows_empty_state.py

**File:** [test_07_search_no_match_shows_empty_state.py](../tests/ui/dispatcher/test_07_search_no_match_shows_empty_state.py) · **Collected cases:** 1

| ID | Function | Coverage / assertion intent | Cases | Status |
| --- | --- | --- | --- | --- |
| — | `test_search_no_match_shows_empty_state` | A search with no matches shows the empty state, not an error or blank table | 1 | ✅ Collected |

### test_08_pending_tab_shows_awaiting_dispatch_only.py

**File:** [test_08_pending_tab_shows_awaiting_dispatch_only.py](../tests/ui/dispatcher/test_08_pending_tab_shows_awaiting_dispatch_only.py) · **Collected cases:** 1

| ID | Function | Coverage / assertion intent | Cases | Status |
| --- | --- | --- | --- | --- |
| — | `test_pending_tab_shows_awaiting_dispatch_only` | PENDING tab is active on load and only shows 'Awaiting Dispatch' rows | 1 | ◐ Conditional |

### test_09_dispatched_tab_shows_dispatched_only.py

**File:** [test_09_dispatched_tab_shows_dispatched_only.py](../tests/ui/dispatcher/test_09_dispatched_tab_shows_dispatched_only.py) · **Collected cases:** 1

| ID | Function | Coverage / assertion intent | Cases | Status |
| --- | --- | --- | --- | --- |
| — | `test_dispatched_tab_shows_dispatched_only` | DISPATCHED tab shows only dispatched rows with no further Dispatch action | 1 | ◐ Conditional |

### test_10_all_tab_shows_union_of_both.py

**File:** [test_10_all_tab_shows_union_of_both.py](../tests/ui/dispatcher/test_10_all_tab_shows_union_of_both.py) · **Collected cases:** 1

| ID | Function | Coverage / assertion intent | Cases | Status |
| --- | --- | --- | --- | --- |
| — | `test_all_tab_shows_union_of_both` | ALL tab contains every Pending and Dispatched request (plus other statuses) | 1 | ◐ Conditional |

### test_11_request_row_shows_details_on_click.py

**File:** [test_11_request_row_shows_details_on_click.py](../tests/ui/dispatcher/test_11_request_row_shows_details_on_click.py) · **Collected cases:** 1

| ID | Function | Coverage / assertion intent | Cases | Status |
| --- | --- | --- | --- | --- |
| — | `test_request_row_shows_details_on_click` | Each request row renders its full detail inline (no click-to-expand) | 1 | ◐ Conditional |

### test_12_dispatch_action_moves_request_to_dispatched.py

**File:** [test_12_dispatch_action_moves_request_to_dispatched.py](../tests/ui/dispatcher/test_12_dispatch_action_moves_request_to_dispatched.py) · **Collected cases:** 1

| ID | Function | Coverage / assertion intent | Cases | Status |
| --- | --- | --- | --- | --- |
| — | `test_dispatch_action_moves_request_to_dispatched` | Dispatch action moves a request to Dispatched (e2e-only - see module docstring) | 1 | ⏭ Marked skip |

### test_13_manual_confirmation_mode_visible.py

**File:** [test_13_manual_confirmation_mode_visible.py](../tests/ui/dispatcher/test_13_manual_confirmation_mode_visible.py) · **Collected cases:** 1

| ID | Function | Coverage / assertion intent | Cases | Status |
| --- | --- | --- | --- | --- |
| — | `test_manual_confirmation_mode_visible` | Manual Confirmation Mode: pending rows show an actionable Dispatch control | 1 | ◐ Conditional |

### test_14_pagination_row_count_and_controls.py

**File:** [test_14_pagination_row_count_and_controls.py](../tests/ui/dispatcher/test_14_pagination_row_count_and_controls.py) · **Collected cases:** 1

| ID | Function | Coverage / assertion intent | Cases | Status |
| --- | --- | --- | --- | --- |
| — | `test_pagination_row_count_and_controls` | Pagination range label and Prev/Next enabled-state are accurate | 1 | ◐ Conditional |

### test_15_notifications_icon_opens_panel.py

**File:** [test_15_notifications_icon_opens_panel.py](../tests/ui/dispatcher/test_15_notifications_icon_opens_panel.py) · **Collected cases:** 1

| ID | Function | Coverage / assertion intent | Cases | Status |
| --- | --- | --- | --- | --- |
| — | `test_notifications_icon_opens_panel` | The Notifications sidebar item opens a panel of recent alerts | 1 | ✅ Collected |

### test_16_notifications_scoped_to_this_dispatcher.py

**File:** [test_16_notifications_scoped_to_this_dispatcher.py](../tests/ui/dispatcher/test_16_notifications_scoped_to_this_dispatcher.py) · **Collected cases:** 1

| ID | Function | Coverage / assertion intent | Cases | Status |
| --- | --- | --- | --- | --- |
| — | `test_notifications_scoped_to_this_dispatcher` | Notifications are scoped to the device, not the selected station | 1 | ◐ Conditional |

---

## 10. Supervisor

### test_00_login.py

**File:** [test_00_login.py](../tests/ui/supervisor/test_00_login.py) · **Collected cases:** 2

| ID | Function | Coverage / assertion intent | Cases | Status |
| --- | --- | --- | --- | --- |
| TC_SUP_LOGIN_001 | `test_supervisor_device_login_with_valid_credentials` | TC_SUP_LOGIN_001 — Admin-provisioned supervisor device logs in | 1 | ✅ Collected |
| TC_SUP_LOGIN_002 | `test_supervisor_device_login_rejected_with_invalid_credentials` | TC_SUP_LOGIN_002 — Supervisor login is rejected with an invalid password | 1 | ✅ Collected |

### test_01_dashboard_shell.py

**File:** [test_01_dashboard_shell.py](../tests/ui/supervisor/test_01_dashboard_shell.py) · **Collected cases:** 3

| ID | Function | Coverage / assertion intent | Cases | Status |
| --- | --- | --- | --- | --- |
| TC_DASH_S_001 | `test_supervisor_dashboard_loads_after_provisioning` | TC_DASH_S_001 — Supervisor dashboard loads after provisioning | 1 | ✅ Collected |
| TC_SUP_SHELL_001 | `test_sidebar_has_exactly_the_supervisor_nav_items` | TC_SUP_SHELL_001 — Sidebar exposes the in-scope supervisor screens | 1 | ✅ Collected |
| TC_SUP_SHELL_002 | `test_each_screen_is_reachable` | TC_SUP_SHELL_002 — Each sidebar screen is reachable and routes correctly | 1 | ✅ Collected |

### test_02_processing_area_selector.py

**File:** [test_02_processing_area_selector.py](../tests/ui/supervisor/test_02_processing_area_selector.py) · **Collected cases:** 2

| ID | Function | Coverage / assertion intent | Cases | Status |
| --- | --- | --- | --- | --- |
| TC-013 | `test_dropdown_lists_only_assigned_processing_areas` | TC-013/TC-014 — PA selector lists only this supervisor's assigned areas | 1 | ✅ Collected |
| TC-011 | `test_default_selection_is_the_assigned_area` | TC-011 — With no explicit choice the selector still shows the assigned area | 1 | ✅ Collected |

### test_03_staging_area_list.py

**File:** [test_03_staging_area_list.py](../tests/ui/supervisor/test_03_staging_area_list.py) · **Collected cases:** 4

| ID | Function | Coverage / assertion intent | Cases | Status |
| --- | --- | --- | --- | --- |
| TC-001 | `test_list_shows_only_assigned_staging_areas` | TC-001/TC-002 — Staging Area list shows only this supervisor's assigned areas | 1 | ✅ Collected |
| TC-001 | `test_assigned_card_shows_grid_size` | TC-001 — The assigned staging area card shows its real grid size | 1 | ✅ Collected |
| TC-011 | `test_list_never_blank_or_errored` | TC-011 — Staging Area list renders a state, never a blank crash | 1 | ✅ Collected |
| TC-012 | `test_switching_staging_areas_refreshes` | TC-012 — Switching between two assigned staging areas refreshes the view | 1 | ◐ Conditional |

### test_04_staging_area_detail.py

**File:** [test_04_staging_area_detail.py](../tests/ui/supervisor/test_04_staging_area_detail.py) · **Collected cases:** 3

| ID | Function | Coverage / assertion intent | Cases | Status |
| --- | --- | --- | --- | --- |
| TC-003 | `test_detail_shows_cell_grid_and_legend` | TC-003 — Opening a staging area shows its occupancy grid and legend | 1 | ✅ Collected |
| TC-004 | `test_reserved_state_is_amber` | TC-004 — Reserved cells are shown in amber/orange | 1 | ✅ Collected |
| TC-005 | `test_staging_detail_has_no_in_transit_indicator` | TC-005 — In-transit is not represented on the staging detail (current contract) | 1 | ✅ Collected |

### test_05_staging_area_manage.py

**File:** [test_05_staging_area_manage.py](../tests/ui/supervisor/test_05_staging_area_manage.py) · **Collected cases:** 4

| ID | Function | Coverage / assertion intent | Cases | Status |
| --- | --- | --- | --- | --- |
| TC-008 | `test_manage_mode_opens_cell_editor` | TC-008/TC-025 — Manage mode opens an in-scope cell editor with State + Filled-with | 1 | ◐ Conditional |
| TC-008 | `test_cell_state_options` | TC-008 — Cell State offers Available / Reserved / Blocked only | 1 | ◐ Conditional |
| TC-009 | `test_invalid_values_are_constrained` | TC-009 — Invalid modification values are constrained by the dialog | 1 | ◐ Conditional |
| TC-010 | `test_cancel_discards_edit_without_mutation` | TC-010 — Cancelling a cell edit discards it and leaves the cell unchanged | 1 | ◐ Conditional |

### test_07_realtime_refresh.py

**File:** [test_07_realtime_refresh.py](../tests/ui/supervisor/test_07_realtime_refresh.py) · **Collected cases:** 1

| ID | Function | Coverage / assertion intent | Cases | Status |
| --- | --- | --- | --- | --- |
| TC-041 | `test_auto_trips_manual_refresh_affordance` | TC-041 — Auto Trips also uses the manual Refresh model | 1 | ✅ Collected |

### test_09_notifications.py

**File:** [test_09_notifications.py](../tests/ui/supervisor/test_09_notifications.py) · **Collected cases:** 10

| ID | Function | Coverage / assertion intent | Cases | Status |
| --- | --- | --- | --- | --- |
| TC-031 | `test_notifications_panel_lists_alerts` | TC-031/TC-040 — Drawer opens and lists connectivity alerts with title + body | 1 | ◐ Conditional |
| TC-031 | `test_mes_error_notification_text` | TC-031/TC-040 — The persistent MES error text is the expected message | 1 | ◐ Conditional |
| TC-034 | `test_no_handle_manually_option` | TC-034 — 'Handle Manually' is not offered (correct for this build) | 1 | ✅ Collected |
| TC-035 | `test_notification_full_description_visible` | TC-035 — A notification's full description is readable from the drawer | 1 | ◐ Conditional |
| TC-035 | `test_clear_all_present` | TC-035/TC-040 — The drawer provides a resolution affordance ('Clear all') | 1 | ◐ Conditional |
| TC-006 | `test_notification_feed_is_device_scoped` | TC-006/TC-007 — The notification feed is device-scoped, not per-staging-area | 1 | ✅ Collected |
| TC-028 | `test_notification_types_are_connectivity_only` | TC-028/TC-029/TC-030 — Notifications are connectivity alerts only (no event types) | 1 | ✅ Collected |
| TC-032 | `test_no_retry_or_handle_manually_controls` | TC-032/TC-033/TC-036 — No Retry and no 'Handle Manually' control in the drawer | 1 | ✅ Collected |
| TC-037 | `test_no_foreign_area_in_notification_feed` | TC-037 — No foreign area leaks into the supervisor's notification feed | 1 | ✅ Collected |
| TC-035 | `test_no_notification_history_section` | TC-035/TC-040 — Resolved alerts are cleared, not moved to a History section | 1 | ✅ Collected |

### test_10_auto_trips.py

**File:** [test_10_auto_trips.py](../tests/ui/supervisor/test_10_auto_trips.py) · **Collected cases:** 2

| ID | Function | Coverage / assertion intent | Cases | Status |
| --- | --- | --- | --- | --- |
| TC_SUP_TRIPS_001 | `test_auto_trips_table_columns` | TC_SUP_TRIPS_001 — Auto Trips table renders with its column contract | 1 | ✅ Collected |
| TC_SUP_TRIPS_002 | `test_auto_trips_controls_present` | TC_SUP_TRIPS_002 — Auto Trips has Refresh + Status/Date filters | 1 | ✅ Collected |

### test_11_access_control.py

**File:** [test_11_access_control.py](../tests/ui/supervisor/test_11_access_control.py) · **Collected cases:** 2

| ID | Function | Coverage / assertion intent | Cases | Status |
| --- | --- | --- | --- | --- |
| TC-043 | `test_supervisor_blocked_from_admin_and_config_routes` | TC-043/TC-044/TC-045/TC-038 — Supervisor is blocked from every admin/config route | 1 | ✅ Collected |
| TC-038 | `test_supervisor_navigation_is_scoped` | TC-038 — Supervisor navigation stays inside their operational remit | 1 | ✅ Collected |

---

## 11. End-to-End

Covers cross-role configuration consistency and a requester → dispatch → Fleet Manager trip flow. The trip flow has runtime preconditions and can skip; collecting it does not prove physical AMR completion.

### test_full_workflow_admin_to_supervisor.py

**File:** [test_full_workflow_admin_to_supervisor.py](../tests/ui/e2e/test_full_workflow_admin_to_supervisor.py) · **Collected cases:** 2

| ID | Function | Coverage / assertion intent | Cases | Status |
| --- | --- | --- | --- | --- |
| — | `test_admin_setup_is_usable_by_every_role` | Admin-built workflow and devices are consistent across all three roles | 1 | ✅ Collected |
| — | `test_request_flows_from_requester_through_dispatch_to_a_fleet_manager_trip` | A dispatched request creates a real trip in Fleet Manager | 1 | ◐ Conditional |

---

## 12. HTTP API Contract Coverage

### test_material_station_mapping_api.py

**File:** [test_material_station_mapping_api.py](../tests/api/test_material_station_mapping_api.py) · **Collected cases:** 46

| ID | Function | Coverage / assertion intent | Cases | Status |
| --- | --- | --- | --- | --- |
| — | `test_material_station_mapping` | Material station mapping | 43 | ✅ Collected |
| — | `test_mapping_authentication` | Mapping authentication | 3 | ✅ Collected |

<details>
<summary>Collected parameter variants</summary>

- `test_material_station_mapping[TC-01_list_authenticated]`
- `test_material_station_mapping[TC-02_list_fields]`
- `test_material_station_mapping[TC-03_existing_mapping_in_list]`
- `test_material_station_mapping[TC-05_create_mapping]`
- `test_material_station_mapping[TC-06_post_upsert_station]`
- `test_material_station_mapping[TC-07_post_no_duplicate]`
- `test_material_station_mapping[TC-08_new_material_type]`
- `test_material_station_mapping[TC-09_new_mapping_key]`
- `test_material_station_mapping[TC-10_new_material_code]`
- `test_material_station_mapping[TC-11_missing_material_code]`
- `test_material_station_mapping[TC-12_missing_mapping_key]`
- `test_material_station_mapping[TC-13_missing_station_id]`
- `test_material_station_mapping[TC-14_missing_material_type]`
- `test_material_station_mapping[TC-15_invalid_area_type]`
- `test_material_station_mapping[TC-16_empty_body]`
- `test_material_station_mapping[TC-17_filter_processing_area]`
- `test_material_station_mapping[TC-18_exclude_other_areas]`
- `test_material_station_mapping[TC-19_nonexistent_area]`
- `test_material_station_mapping[TC-20_filter_material]`
- `test_material_station_mapping[TC-21_exclude_other_materials]`
- `test_material_station_mapping[TC-22_nonexistent_material]`
- `test_material_station_mapping[TC-23_get_existing_id]`
- `test_material_station_mapping[TC-24_get_nonexistent_id]`
- `test_material_station_mapping[TC-25_get_invalid_id]`
- `test_material_station_mapping[TC-26_put_mapping]`
- `test_material_station_mapping[TC-27_get_after_put]`
- `test_material_station_mapping[TC-28_put_nonexistent]`
- `test_material_station_mapping[TC-29_invalid_put_preserves_data]`
- `test_material_station_mapping[TC-30_delete_mapping]`
- `test_material_station_mapping[TC-31_get_after_delete]`
- `test_material_station_mapping[TC-32_delete_nonexistent]`
- `test_material_station_mapping[TC-33_bulk_create]`
- `test_material_station_mapping[TC-34_verify_bulk_create]`
- `test_material_station_mapping[TC-35_bulk_duplicate]`
- `test_material_station_mapping[TC-36_bulk_invalid_record]`
- `test_material_station_mapping[TC-37_bulk_update]`
- `test_material_station_mapping[TC-38_verify_bulk_update]`
- `test_material_station_mapping[TC-39_bulk_invalid_id]`
- `test_material_station_mapping[TC-40_delete_by_key]`
- `test_material_station_mapping[TC-41_verify_delete_by_key]`
- `test_material_station_mapping[TC-42_other_keys_preserved]`
- `test_material_station_mapping[TC-43_delete_absent_key]`
- `test_material_station_mapping[TC-44_authenticated_crud]`
- `test_mapping_authentication[TC-04_no_auth_list]`
- `test_mapping_authentication[TC-45_no_auth]`
- `test_mapping_authentication[TC-46_invalid_token]`

</details>

### test_processing_area_api.py

**File:** [test_processing_area_api.py](../tests/api/test_processing_area_api.py) · **Collected cases:** 22

| ID | Function | Coverage / assertion intent | Cases | Status |
| --- | --- | --- | --- | --- |
| PA-GET-001 | `test_pa_get_001_get_all_processing_areas` | Pa get 001 get all processing areas | 1 | ✅ Collected |
| PA-GET-002 | `test_pa_get_002_get_processing_area_by_valid_id` | Pa get 002 get processing area by valid id | 1 | ✅ Collected |
| PA-GET-003 | `test_pa_get_003_get_processing_area_nonexistent_id` | Pa get 003 get processing area nonexistent id | 1 | ✅ Collected |
| PA-GET-004 | `test_pa_get_004_get_processing_area_invalid_id_format` | Pa get 004 get processing area invalid id format | 1 | ✅ Collected |
| PA-POST-001 | `test_pa_post_001_create_processing_area` | Pa post 001 create processing area | 1 | ✅ Collected |
| PA-POST-002 | `test_pa_post_002_create_duplicate_processing_area_name` | Pa post 002 create duplicate processing area name | 1 | ✅ Collected |
| PA-POST-003 | `test_pa_post_003_create_processing_area_missing_name` | Pa post 003 create processing area missing name | 1 | ✅ Collected |
| PA-POST-004 | `test_pa_post_004_create_processing_area_missing_description` | Pa post 004 create processing area missing description | 1 | ✅ Collected |
| PA-POST-005 | `test_pa_post_005_create_processing_area_empty_body` | Pa post 005 create processing area empty body | 1 | ✅ Collected |
| PA-POST-006 | `test_pa_post_006_create_processing_area_empty_name` | Pa post 006 create processing area empty name | 1 | ✅ Collected |
| PA-POST-007 | `test_pa_post_007_create_processing_area_special_long_name` | Pa post 007 create processing area special long name | 1 | ✅ Collected |
| PA-PUT-001 | `test_pa_put_001_update_existing_processing_area` | Pa put 001 update existing processing area | 1 | ✅ Collected |
| PA-PUT-002 | `test_pa_put_002_verify_updated_processing_area` | Pa put 002 verify updated processing area | 1 | ✅ Collected |
| PA-PUT-003 | `test_pa_put_003_update_nonexistent_processing_area` | Pa put 003 update nonexistent processing area | 1 | ✅ Collected |
| PA-PUT-004 | `test_pa_put_004_update_processing_area_invalid_id_format` | Pa put 004 update processing area invalid id format | 1 | ✅ Collected |
| PA-PUT-006 | `test_pa_put_006_update_processing_area_duplicate_name` | Pa put 006 update processing area duplicate name | 1 | ✅ Collected |
| PA-DEL-002 | `test_pa_del_002_verify_processing_area_deletion` | Pa del 002 verify processing area deletion | 1 | ✅ Collected |
| PA-DEL-003 | `test_pa_del_003_delete_nonexistent_processing_area` | Pa del 003 delete nonexistent processing area | 1 | ✅ Collected |
| PA-DEL-004 | `test_pa_del_004_delete_processing_area_invalid_id_format` | Pa del 004 delete processing area invalid id format | 1 | ✅ Collected |
| PA-AUTH-001 | `test_pa_auth_001_access_api_with_valid_admin_token` | Pa auth 001 access api with valid admin token | 1 | ✅ Collected |
| PA-AUTH-002 | `test_pa_auth_002_access_api_without_token` | Pa auth 002 access api without token | 1 | ✅ Collected |
| PA-AUTH-003 | `test_pa_auth_003_access_api_with_invalid_token` | Pa auth 003 access api with invalid token | 1 | ✅ Collected |

### test_processing_area_machines_api.py

**File:** [test_processing_area_machines_api.py](../tests/api/test_processing_area_machines_api.py) · **Collected cases:** 60

| ID | Function | Coverage / assertion intent | Cases | Status |
| --- | --- | --- | --- | --- |
| — | `test_pam_get_001` | Pam get 001 | 1 | ✅ Collected |
| — | `test_pam_get_002` | Pam get 002 | 1 | ✅ Collected |
| — | `test_pam_get_003` | Pam get 003 | 1 | ✅ Collected |
| — | `test_pam_post_001` | Pam post 001 | 1 | ✅ Collected |
| — | `test_pam_post_002` | Pam post 002 | 1 | ✅ Collected |
| — | `test_pam_post_003` | Pam post 003 | 3 | ✅ Collected |
| — | `test_pam_post_004` | Pam post 004 | 1 | ✅ Collected |
| — | `test_pam_post_005` | Pam post 005 | 1 | ✅ Collected |
| — | `test_pam_post_006` | Pam post 006 | 1 | ✅ Collected |
| — | `test_pam_page_001` | Pam page 001 | 1 | ✅ Collected |
| — | `test_pam_page_002` | Pam page 002 | 1 | ✅ Collected |
| — | `test_pam_page_003` | Pam page 003 | 1 | ✅ Collected |
| — | `test_pam_page_004` | Pam page 004 | 4 | ✅ Collected |
| — | `test_pam_area_001` | Pam area 001 | 1 | ✅ Collected |
| — | `test_pam_area_002` | Pam area 002 | 1 | ✅ Collected |
| — | `test_pam_area_003` | Pam area 003 | 1 | ✅ Collected |
| — | `test_pam_area_004` | Pam area 004 | 1 | ✅ Collected |
| — | `test_pam_del_area_001` | Pam del area 001 | 1 | ✅ Collected |
| — | `test_pam_del_area_002` | Pam del area 002 | 1 | ✅ Collected |
| — | `test_pam_del_area_003` | Pam del area 003 | 1 | ✅ Collected |
| — | `test_pam_del_area_004` | Pam del area 004 | 1 | ✅ Collected |
| — | `test_pam_point_001` | Pam point 001 | 2 | ✅ Collected |
| — | `test_pam_point_002` | Pam point 002 | 1 | ✅ Collected |
| — | `test_pam_point_003` | Pam point 003 | 1 | ✅ Collected |
| — | `test_pam_name_001` | Pam name 001 | 1 | ✅ Collected |
| — | `test_pam_name_002` | Pam name 002 | 1 | ✅ Collected |
| — | `test_pam_name_003` | Pam name 003 | 1 | ✅ Collected |
| — | `test_pam_name_004` | Pam name 004 | 1 | ✅ Collected |
| — | `test_pam_id_001` | Pam id 001 | 1 | ✅ Collected |
| — | `test_pam_id_002` | Pam id 002 | 1 | ✅ Collected |
| — | `test_pam_id_003` | Pam id 003 | 1 | ✅ Collected |
| — | `test_pam_put_001` | Pam put 001 | 1 | ✅ Collected |
| — | `test_pam_put_002` | Pam put 002 | 1 | ✅ Collected |
| — | `test_pam_put_003` | Pam put 003 | 1 | ✅ Collected |
| — | `test_pam_put_004` | Pam put 004 | 1 | ✅ Collected |
| — | `test_pam_put_005` | Pam put 005 | 1 | ✅ Collected |
| — | `test_pam_invalid_update_preserves_record` | Pam invalid update preserves record | 1 | ✅ Collected |
| — | `test_pam_del_001` | Pam del 001 | 1 | ✅ Collected |
| — | `test_pam_del_002` | Pam del 002 | 1 | ✅ Collected |
| — | `test_pam_del_003` | Pam del 003 | 1 | ✅ Collected |
| — | `test_pam_del_004` | Pam del 004 | 1 | ✅ Collected |
| — | `test_pam_auth_001` | Pam auth 001 | 1 | ✅ Collected |
| — | `test_pam_authentication` | Pam authentication | 12 | ✅ Collected |

<details>
<summary>Collected parameter variants</summary>

- `test_pam_post_003[machine_name]`
- `test_pam_post_003[processing_area_id]`
- `test_pam_post_003[point_type]`
- `test_pam_page_004[params0]`
- `test_pam_page_004[params1]`
- `test_pam_page_004[params2]`
- `test_pam_page_004[params3]`
- `test_pam_point_001[production_type]`
- `test_pam_point_001[consumption_type]`
- `test_pam_authentication[list-missing]`
- `test_pam_authentication[list-invalid]`
- `test_pam_authentication[get-missing]`
- `test_pam_authentication[get-invalid]`
- `test_pam_authentication[create-missing]`
- `test_pam_authentication[create-invalid]`
- `test_pam_authentication[update-missing]`
- `test_pam_authentication[update-invalid]`
- `test_pam_authentication[delete-missing]`
- `test_pam_authentication[delete-invalid]`
- `test_pam_authentication[delete_area-missing]`
- `test_pam_authentication[delete_area-invalid]`

</details>

---

## 13. MTS Model / Mock API Coverage

**Adapter:** [test_mts_automation.py](../tests/api/test_mts_automation.py)

**Execution bridge:** built into [test_mts_automation.py](../tests/api/test_mts_automation.py)

**Marker:** `api_model` · **Collected cases:** 182

Each case below is a separate pytest parameter. Each legacy suite executes once
in an isolated subprocess, retaining its case ordering and shared state. Selecting
one case still executes its underlying legacy suite. Recorded non-pass statuses,
runner crashes, missing/mismatched results, and timeouts fail the adapter.

MTS-146 and MTS-147 explicitly use model mode under pytest. Other MTS runners use
local state/models and/or local HTTP servers, with some network probes. Scenario
names below describe the legacy checks' intent, not verified production behavior.

### MTS135 — 38 cases

**Source:** [test_mes_integration_polling.py](../tests/api/test_mes_integration_polling.py)

| Case ID | Module | Scenario | Mode |
| --- | --- | --- | --- |
| MES-SCH-001 | Scheduler | Polling Interval Config | Model/mock |
| MES-SCH-002 | Scheduler | Interval Change on Restart | Model/mock |
| MES-SCH-003 | Scheduler | Single Job Guarantee | Model/mock |
| MES-SCH-004 | Scheduler | Configurable Window Delta | Model/mock |
| MES-SCH-005 | Scheduler | App Lifecycle Attachment | Model/mock |
| MES-API-001 | API Format | Live Endpoint Pattern | Model/mock |
| MES-API-002 | API Format | ISO Minute Formatting | Model/mock |
| MES-API-003 | API Format | Minute Boundary Flooring | Model/mock |
| MES-API-004 | API Format | API Error Resilience | Model/mock |
| MES-API-005 | API Format | Checkpoint as Start Time | Model/mock |
| MES-API-006 | API Format | Dynamic End Time Capping | Model/mock |
| MES-EVT-001 | Event Handling | Missing Field Filter | Model/mock |
| MES-EVT-002 | Event Handling | Cross-Cycle Deduplication | Model/mock |
| MES-EVT-003 | Event Handling | Intra-Batch Deduplication | Model/mock |
| MES-EVT-004 | Event Handling | Valid Live Event Ingestion | Model/mock |
| MES-EVT-005 | Event Handling | Mixed Batch Processing | Model/mock |
| MES-EVT-006 | Event Handling | Persistent QR Store | Model/mock |
| MES-INV-001 | Inventory | Accurate Record Updates | Model/mock |
| MES-INV-002 | Inventory | Update Idempotency | Model/mock |
| MES-INV-003 | Inventory | Untouched on Dropped Events | Model/mock |
| MES-INV-004 | Inventory | Atomic Batch Rollback | Model/mock |
| MES-INV-005 | Inventory | JSON Schema Conformance | Model/mock |
| MES-CHK-001 | Checkpointing | Save on Batch Success | Model/mock |
| MES-CHK-002 | Checkpointing | Hold on Job Failure | Model/mock |
| MES-CHK-003 | Checkpointing | Advance on 0 Records | Model/mock |
| MES-CHK-004 | Checkpointing | Resume from Last Checkpoint | Model/mock |
| MES-CHK-005 | Checkpointing | Downtime Gap Processing | Model/mock |
| MES-CHK-006 | Checkpointing | Crash Durability | Model/mock |
| MES-FAIL-001 | Failure Recovery | API Downtime Scenario | Model/mock |
| MES-FAIL-002 | Failure Recovery | Invalid Event Scenario | Model/mock |
| MES-FAIL-003 | Failure Recovery | Duplicate Event Scenario | Model/mock |
| MES-FAIL-004 | Failure Recovery | Partial Failure Scenario | Model/mock |
| MES-FAIL-005 | Failure Recovery | Cold Restart Scenario | Model/mock |
| MES-NFR-001 | Non-Functional | API Failure Log Details | Model/mock |
| MES-NFR-002 | Non-Functional | Dropped Event Reasons | Model/mock |
| MES-NFR-003 | Non-Functional | Checkpoint Audit Logs | Model/mock |
| MES-NFR-004 | Non-Functional | Job Serialization | Model/mock |
| MES-NFR-005 | Non-Functional | 30-Day Retention Cleanup | Model/mock |

### MTS136 — 48 cases

**Source:** [test_central_config_health.py](../tests/api/test_central_config_health.py)

| Case ID | Module | Scenario | Mode |
| --- | --- | --- | --- |
| ADM-CON-FM-001 | FM Config | Configure Fleet Manager IP | Model/mock |
| ADM-CON-FM-002 | FM Config | Invalid FM IP Validation | Model/mock |
| ADM-CON-FM-003 | FM Config | Test Connection Reachability (Success) | Model/mock |
| ADM-CON-FM-004 | FM Config | Test Connection Unreachable Failure | Model/mock |
| ADM-CON-FM-005 | FM Config | FM IP Persistence Across Reload | Model/mock |
| ADM-CON-AMR-001 | AMR API Config | Configure AMR API Endpoint | Model/mock |
| ADM-CON-AMR-002 | AMR API Config | Invalid AMR API Endpoint Validation | Model/mock |
| ADM-CON-AMR-003 | AMR API Config | AMR API Test Connection Success | Model/mock |
| ADM-CON-AMR-004 | AMR API Config | AMR API Test Connection Failure | Model/mock |
| ADM-CON-BOM-001 | BOM API Config | Configure BOM API Endpoint | Model/mock |
| ADM-CON-BOM-002 | BOM API Config | Invalid BOM API Endpoint Validation | Model/mock |
| ADM-CON-BOM-003 | BOM API Config | BOM API Test Connection Success | Model/mock |
| ADM-CON-BOM-004 | BOM API Config | BOM API Test Connection Failure | Model/mock |
| ADM-HLT-001 | Health Dashboard | Connected Status for Healthy FM | Model/mock |
| ADM-HLT-002 | Health Dashboard | Disconnected Status on FM Drop | Model/mock |
| ADM-HLT-003 | Health Dashboard | Error Status for Error Condition | Model/mock |
| ADM-HLT-004 | Health Dashboard | Independent Health Statuses | Model/mock |
| ADM-HLT-005 | Health Dashboard | Health Polling Interval Consistency | Model/mock |
| ADM-HLT-006 | Health Dashboard | Reconnection Recovery to Connected | Model/mock |
| ADM-NOT-001 | Notifications | Disconnection Generates Notification | Model/mock |
| ADM-NOT-002 | Notifications | Error State Distinct Notification | Model/mock |
| ADM-NOT-003 | Notifications | Notification System Identifier & Timestamp | Model/mock |
| ADM-NOT-004 | Notifications | Reconnection Recovery Notification | Model/mock |
| ADM-NOT-005 | Notifications | Role-Based Notification Visibility | Model/mock |
| ADM-NOT-006 | Notifications | Simultaneous Disconnections Distinct Alerts | Model/mock |
| ADM-VER-001 | Versioning | Configuration Version History Log | Model/mock |
| ADM-VER-002 | Versioning | Version Diff Inspection | Model/mock |
| ADM-VER-003 | Versioning | Rollback to Previous Version | Model/mock |
| ADM-VER-004 | Versioning | Audit Trail Integrity | Model/mock |
| ADM-VER-005 | Versioning | Concurrent Edit Conflict Handling | Model/mock |
| ADM-FMM-001 | Central Config | Admin Role Access Restriction | Model/mock |
| ADM-FMM-002 | Central Config | FM Section Required Field Completeness | Model/mock |
| ADM-FMM-003 | Central Config | MES Section Required Field Completeness | Model/mock |
| ADM-FMM-004 | Central Config | Independent Config Section Persistence | Model/mock |
| ADM-FMM-005 | Central Config | Inline Field-Level Validation Errors | Model/mock |
| ADM-MAT-001 | Material Catalog | Admin Creates New Material | Model/mock |
| ADM-MAT-002 | Material Catalog | Mandatory Fields Enforced on Material | Model/mock |
| ADM-MAT-003 | Material Catalog | Duplicate Material Code Prevented | Model/mock |
| ADM-MAT-004 | Material Catalog | Admin Edits Existing Material | Model/mock |
| ADM-MAT-005 | Material Catalog | Material Archive/Deactivation | Model/mock |
| ADM-MAT-006 | Container Catalog | Admin Creates New Container Type | Model/mock |
| ADM-MAT-007 | Container Catalog | Mandatory Fields Enforced on Container | Model/mock |
| ADM-MAT-008 | Container Catalog | Admin Edits Existing Container | Model/mock |
| ADM-MAT-009 | Downstream Sync | Material/Container Downstream Availability | Model/mock |
| ADM-ACC-001 | Acceptance | End-to-End Three Connection Setup | Model/mock |
| ADM-ACC-002 | Acceptance | Disconnection-to-Notification Pipeline | Model/mock |
| ADM-ACC-003 | Acceptance | Config Versioning Across All Types | Model/mock |
| ADM-ACC-004 | Acceptance | Deterministic Downstream Control Layer | Model/mock |

### MTS146 — 20 cases

**Source:** [test_processing_staging_grid.py](../tests/api/test_processing_staging_grid.py)

| Case ID | Module | Scenario | Mode |
| --- | --- | --- | --- |
| TC_PA_001 | Processing Area | Staging Area - List View | Model/mock |
| TC_PA_002 | Processing Area | Staging Area - List View | Model/mock |
| TC_PA_003 | Processing Area | Staging Area - List View | Model/mock |
| TC_PA_004 | Processing Area | Staging Area - List View | Model/mock |
| TC_PA_005 | Processing Area | Staging Area - Grid View | Model/mock |
| TC_PA_006 | Processing Area | Staging Area - Grid View | Model/mock |
| TC_PA_007 | Processing Area | Staging Area - Grid View | Model/mock |
| TC_PA_008 | Processing Area | Staging Area - Cell Management | Model/mock |
| TC_PA_009 | Processing Area | Staging Area - Cell Management | Model/mock |
| TC_PA_010 | Processing Area | Staging Area - Cell Management | Model/mock |
| TC_PA_011 | Processing Area | Staging Area - Cell Management | Model/mock |
| TC_PA_012 | Processing Area | Staging Area - Cell Management | Model/mock |
| TC_PA_013 | Processing Area | Processing Area Config | Model/mock |
| TC_PA_014 | Processing Area | Processing Area Config | Model/mock |
| TC_PA_015 | Processing Area | Processing Area Config | Model/mock |
| TC_PA_016 | Processing Area | Processing Area Config | Model/mock |
| TC_PA_017 | Processing Area | Containers | Model/mock |
| TC_PA_018 | Processing Area | Containers | Model/mock |
| TC_PA_019 | Processing Area | Containers | Model/mock |
| TC_PA_020 | Processing Area | Containers | Model/mock |

### MTS147 — 27 cases

**Source:** [test_material_master_config.py](../tests/api/test_material_master_config.py)

| Case ID | Module | Scenario | Mode |
| --- | --- | --- | --- |
| TC-01 | UI | Functional | Model/mock |
| TC-02 | UI | Validation | Model/mock |
| TC-03 | UI | Validation | Model/mock |
| TC-04 | UI | Validation | Model/mock |
| TC-05 | UI | Validation | Model/mock |
| TC-06 | UI | Validation | Model/mock |
| TC-07 | UI | Validation | Model/mock |
| TC-08 | UI | Validation | Model/mock |
| TC-09 | UI | Functional | Model/mock |
| TC-10 | UI | Functional | Model/mock |
| TC-11 | UI | Functional | Model/mock |
| TC-12 | UI | Functional | Model/mock |
| TC-13 | UI | Functional | Model/mock |
| TC-14 | UI | Functional | Model/mock |
| TC-15 | UI | Integration | Model/mock |
| TC-16 | API | Functional | Model/mock |
| TC-17 | API | Validation | Model/mock |
| TC-18 | API | Validation | Model/mock |
| TC-19 | API | Validation | Model/mock |
| TC-20 | API | Functional | Model/mock |
| TC-21 | API | Functional | Model/mock |
| TC-22 | API | Functional | Model/mock |
| TC-23 | API | Functional | Model/mock |
| TC-24 | API | Integration | Model/mock |
| TC-25 | Edge | Validation | Model/mock |
| TC-26 | Edge | Validation | Model/mock |
| TC-27 | API | Validation | Model/mock |

### MTS155 — 11 cases

**Source:** [test_settings_rest_api.py](../tests/api/test_settings_rest_api.py)

| Case ID | Module | Scenario | Mode |
| --- | --- | --- | --- |
| TC_01 | Settings API | Discovery / List All External Systems | Model/mock |
| TC_02 | Settings API | Configuration / Update FM IP Address | Model/mock |
| TC_03 | Settings API | Configuration / Update AMR API URL | Model/mock |
| TC_04 | Settings API | Configuration / Update BOM API URL | Model/mock |
| TC_05 | Settings API | Validation / Invalid IP Format Rejection | Model/mock |
| TC_06 | Settings API | Validation / Invalid URL Format Rejection | Model/mock |
| TC_07 | Settings API | Health Monitoring / All Systems Connected | Model/mock |
| TC_08 | Settings API | Health Monitoring / Disconnected State Detection | Model/mock |
| TC_09 | Settings API | Alerting / Mandatory Connection Drop Alert | Model/mock |
| TC_10 | Settings API | Persistence / Service Restart Persistence | Model/mock |
| TC_11 | Settings API | Enforcement / 'Always Connected' Mandatory Policy | Model/mock |

### MTS162 — 13 cases

**Source:** [test_tablet_login_security.py](../tests/api/test_tablet_login_security.py)

| Case ID | Module | Scenario | Mode |
| --- | --- | --- | --- |
| TC-LGN-001 | Login | Verify Login screen renders correctly on tablet | Model/mock |
| TC-LGN-002 | Login | Login with valid credentials | Model/mock |
| TC-LGN-003 | Login | Login with invalid username | Model/mock |
| TC-LGN-004 | Login | Login with invalid password | Model/mock |
| TC-LGN-005 | Login | Login with empty Username field | Model/mock |
| TC-LGN-006 | Login | Login with empty Password field | Model/mock |
| TC-LGN-007 | Login | Login with both fields empty | Model/mock |
| TC-LGN-008 | Login | Tap 'Need help?' link | Model/mock |
| TC-LGN-009 | Login | Close 'Need Help?' modal via Close button | Model/mock |
| TC-LGN-010 | Login | Close 'Need Help?' modal via backdrop tap | Model/mock |
| TC-LGN-011 | Login | Session persists after app minimise | Model/mock |
| TC-LGN-012 | Login | Password field masked by default | Model/mock |
| TC-LGN-013 | Login | Tablet landscape orientation layout | Model/mock |

### MTS167 — 25 cases

**Source:** [test_external_connections_setup.py](../tests/api/test_external_connections_setup.py)

| Case ID | Module | Scenario | Mode |
| --- | --- | --- | --- |
| MTS-167-TC-01 | External Connections | Verify GET all external connections | Model/mock |
| MTS-167-TC-02 | External Connections | Verify default status flags | Model/mock |
| MTS-167-TC-03 | External Connections | Setup FM Connection - Valid Credentials | Model/mock |
| MTS-167-TC-04 | External Connections | Setup FM Connection - Invalid Host URL | Model/mock |
| MTS-167-TC-05 | External Connections | Setup FM Connection - Unauthorized | Model/mock |
| MTS-167-TC-06 | External Connections | Setup FM Connection - Missing Host | Model/mock |
| MTS-167-TC-07 | External Connections | Setup FM Connection - Missing Client ID | Model/mock |
| MTS-167-TC-08 | External Connections | Setup MES Connection - Valid Credentials | Model/mock |
| MTS-167-TC-09 | External Connections | Setup MES Connection - Invalid Credentials | Model/mock |
| MTS-167-TC-10 | External Connections | Update AMR Connection Attributes | Model/mock |
| MTS-167-TC-11 | External Connections | Update BOM Connection Attributes | Model/mock |
| MTS-167-TC-12 | External Connections | Verify Sync Schedule Persistence | Model/mock |
| MTS-167-TC-13 | External Connections | Disable Connection | Model/mock |
| MTS-167-TC-14 | External Connections | Enable Connection | Model/mock |
| MTS-167-TC-15 | External Connections | Verify 'connected' flag on success | Model/mock |
| MTS-167-TC-16 | External Connections | Verify 'connected' flag on failure | Model/mock |
| MTS-167-TC-17 | External Connections | Credential Swap on Active Connection | Model/mock |
| MTS-167-TC-18 | External Connections | UI Validation - Error Message | Model/mock |
| MTS-167-TC-19 | External Connections | GET specific connection by ID | Model/mock |
| MTS-167-TC-20 | External Connections | GET specific connection by ID - Invalid | Model/mock |
| MTS-167-TC-21 | External Connections | Delete Connection | Model/mock |
| MTS-167-TC-22 | External Connections | Concurrent Multi-user Updates | Model/mock |
| MTS-167-TC-23 | External Connections | Large Payload - Long URL | Model/mock |
| MTS-167-TC-24 | External Connections | Special Characters in Attributes | Model/mock |
| MTS-167-TC-25 | External Connections | Verify API Response Time | Model/mock |

---

## 14. Removed Infrastructure Tests

The `tests/unit/` suite (13 cases) was removed at the user's request on
2026-09-29. Runtime cleanup and wait helpers remain in use; their dedicated
regression tests are no longer collected. `tests/api/`, `tests/ui/`, and `tests/common/`
remain as test suites.

---

## 15. Skipped & Conditional Coverage Backlog

### Unconditionally skipped cases

| File | Function | Declared reason |
| --- | --- | --- |
| [test_10_station_mapping_validation.py](../tests/ui/admin/processing_area/test_10_station_mapping_validation.py) | `test_mapping_referencing_deleted_station_or_machine` | Not implemented: needs an isolated, explicitly linked machine/mapping fixture and a defined deletion contract. FM stations cannot be deleted through AtiFlow admin. Historical product behavior has not been reverified. |
| [test_02_machine_dropdown_switches_context.py](../tests/ui/requester/test_02_machine_dropdown_switches_context.py) | `test_machine_dropdown_switches_context` | Confirmed via config/test_data.toml: requester_bound_machines is a single scalar value ('consuption_machine_45'), not a list - the mohit_requester device is bound to exactly one machine. There is no second machine to switch to, so this scenario cannot be exercised against the current provisioning. Would need the requester device rebound to two+ machines in admin (Execution Source Config) before this test has anything real to assert. |
| [test_12_dispatch_action_moves_request_to_dispatched.py](../tests/ui/dispatcher/test_12_dispatch_action_moves_request_to_dispatched.py) | `test_dispatch_action_moves_request_to_dispatched` | Clicking Dispatch moves a real AMR via the live Fleet Manager. It may only be run against a request this test run created itself, which requires the cross-role run_context fixture from tests/ui/e2e/. Not runnable from the dispatcher-only folder. |

### Runtime conditions

These conditions are derived from explicit `pytest.skip(...)` calls in test bodies.

| File | Function | Condition / declared skip reason |
| --- | --- | --- |
| [test_15_staging_area.py](../tests/ui/admin/processing_area/test_15_staging_area.py) | `test_manage_cell_fields` | f"Staging area '{TestData.staging_area_name}' currently exposes no editable (non-[disabled]) grid cell — every cell is locked. Nothing to open a manage dialog on." |
| [test_19_notification.py](../tests/ui/admin/processing_area/test_19_notification.py) | `test_unreachable_alert_details` | f'No {service} Unreachable notification is currently present' |
| [test_19_notification.py](../tests/ui/admin/processing_area/test_19_notification.py) | `test_clear_all_control` | No notifications present; Clear all may be hidden or disabled |
| [test_exec_config_validation.py](../tests/ui/admin/execution_source_config/test_exec_config_validation.py) | `test_invalid_mes_parameters_fail_cleanly` | MES configuration form not found — MES may not be configurable from the UI in this environment. |
| [test_18_cancel_requested_order.py](../tests/ui/requester/test_18_cancel_requested_order.py) | `test_cancel_requested_order` | f'Could not stage an order for {sub_sku}/{sku} — the wizard shows no available stock right now ({exc.__class__.__name__}).' |
| [test_04_sort_dropdown_toggles_newest_oldest.py](../tests/ui/dispatcher/test_04_sort_dropdown_toggles_newest_oldest.py) | `test_sort_dropdown_toggles_newest_oldest` | Default bound station has fewer than 2 pending requests right now - nothing to prove an ordering with. This is live production data. |
| [test_05_search_by_id_no_filters_table.py](../tests/ui/dispatcher/test_05_search_by_id_no_filters_table.py) | `test_search_by_id_no_filters_table` | No pending requests on the default station to search for. |
| [test_06_search_by_material_code_filters_table.py](../tests/ui/dispatcher/test_06_search_by_material_code_filters_table.py) | `test_search_by_material_code_filters_table` | No pending requests on the default station to search for. |
| [test_08_pending_tab_shows_awaiting_dispatch_only.py](../tests/ui/dispatcher/test_08_pending_tab_shows_awaiting_dispatch_only.py) | `test_pending_tab_shows_awaiting_dispatch_only` | Default station's Pending queue is empty right now. |
| [test_09_dispatched_tab_shows_dispatched_only.py](../tests/ui/dispatcher/test_09_dispatched_tab_shows_dispatched_only.py) | `test_dispatched_tab_shows_dispatched_only` | Default station has no dispatched requests right now. |
| [test_10_all_tab_shows_union_of_both.py](../tests/ui/dispatcher/test_10_all_tab_shows_union_of_both.py) | `test_all_tab_shows_union_of_both` | Default station has neither pending nor dispatched requests right now. |
| [test_11_request_row_shows_details_on_click.py](../tests/ui/dispatcher/test_11_request_row_shows_details_on_click.py) | `test_request_row_shows_details_on_click` | Default station's Pending queue is empty right now. |
| [test_13_manual_confirmation_mode_visible.py](../tests/ui/dispatcher/test_13_manual_confirmation_mode_visible.py) | `test_manual_confirmation_mode_visible` | Default station's Pending queue is empty right now - no row to check the confirmation control on. |
| [test_14_pagination_row_count_and_controls.py](../tests/ui/dispatcher/test_14_pagination_row_count_and_controls.py) | `test_pagination_row_count_and_controls` | ALL tab is empty on the default station right now. |
| [test_16_notifications_scoped_to_this_dispatcher.py](../tests/ui/dispatcher/test_16_notifications_scoped_to_this_dispatcher.py) | `test_notifications_scoped_to_this_dispatcher` | No notifications in the feed right now - nothing to scope-check. |
| [test_03_staging_area_list.py](../tests/ui/supervisor/test_03_staging_area_list.py) | `test_switching_staging_areas_refreshes` | f"Supervisor device '{TestData.sup_device_name}' is bound to a single staging area ({home.staging_card_titles()}) — nothing to switch to. Bind it to 2+ staging areas in Execution Source Config to enable this case." |
| [test_05_staging_area_manage.py](../tests/ui/supervisor/test_05_staging_area_manage.py) | `test_manage_mode_opens_cell_editor` | f"'{TestData.sup_bound_staging_area}' currently exposes no editable (non-[disabled]) cell — every cell is locked." |
| [test_05_staging_area_manage.py](../tests/ui/supervisor/test_05_staging_area_manage.py) | `test_cell_state_options` | no editable cell to open right now |
| [test_05_staging_area_manage.py](../tests/ui/supervisor/test_05_staging_area_manage.py) | `test_invalid_values_are_constrained` | no editable cell to open right now |
| [test_05_staging_area_manage.py](../tests/ui/supervisor/test_05_staging_area_manage.py) | `test_cancel_discards_edit_without_mutation` | no editable cell to open right now |
| [test_09_notifications.py](../tests/ui/supervisor/test_09_notifications.py) | `test_notifications_panel_lists_alerts` | No notifications present on the supervisor device right now. |
| [test_09_notifications.py](../tests/ui/supervisor/test_09_notifications.py) | `test_mes_error_notification_text` | No MES notification present right now (FM-only or none). |
| [test_09_notifications.py](../tests/ui/supervisor/test_09_notifications.py) | `test_notification_full_description_visible` | No notification body to inspect right now. |
| [test_09_notifications.py](../tests/ui/supervisor/test_09_notifications.py) | `test_clear_all_present` | No notifications, so no 'Clear all' shown. |
| [test_full_workflow_admin_to_supervisor.py](../tests/ui/e2e/test_full_workflow_admin_to_supervisor.py) | `test_request_flows_from_requester_through_dispatch_to_a_fleet_manager_trip` | f'{sub_sku} shows 0 Available right now - no live stock to raise a request with, so there is nothing to dispatch.'; f"Approve Request dialog for {request_id} never let 'Confirm Approval' enable itself - no eligible physical item/trolley to complete a real dispatch with right now." |

### Excluded or removed coverage

- `TC_RQD_005` (device deletion with an in-flight request), `TC_MES_001`
  (valid MES connection parameters), `TC_UI_011` (loading spinner), and
  `test_delete_absent_device_is_noop` were removed at the user's request.
  They are not counted as active or skipped coverage.
- Historical WIP inventory and settings file listings in the reference do not
  match the current tree. See [WIP inventory cases](WIP_INVENTORY_TEST_CASES.md)
  for separately documented scenarios; documentation is not executable coverage.
- The standalone manual browser runner was removed at the user's request.
  It contributed zero pytest cases; collection counts are unchanged.
- The unused MES repair script was removed during project cleanup; it is not test coverage.
- Model passes do not validate real MES/FM services, authentication security,
  persistence, performance, or browser behavior in the deployment.

## 16. Test Data & Automatic Cleanup

- UI ownership tracking covers newly created processing areas, tracked renames,
  successfully saved role devices, and helper-created child records (materials,
  containers, bulk rows, machines, station mappings, workflows).
- The UI teardown attempts device deletion, then child records in dependency
  order, then owned processing areas. Cleanup failures are surfaced as warnings;
  row deletion helpers now raise when a record remains visible.
- Pre-existing records detected by the helpers are not claimed for cleanup.
  Direct form interactions outside those helpers, modifications to pre-existing
  records, and interrupted processes are not guaranteed to be restored.
- API processing-area, machine, and mapping fixtures clean up owned records on
  teardown. MTS module teardown removes temporary subprocess/model directories.
- `CLEANUP_TEST_DATA=0` disables the session UI cleaner for debugging; API fixture
  cleanup remains mandatory. Reports are preserved (subject to retention).
- Cleanup ownership behavior was previously checked by the now-removed unit suite. Full live UI teardown has not
  been validated in this documentation update.

## 17. How to Run

From the repository root:

```bash
# Inventory only: no test execution
pytest --collect-only --no-pdf

# Entire suite
pytest

# All 173 browser cases (role-specific + shared)
pytest tests/ui tests/common

# Shared checks only: 26 cases
pytest tests/common

# Role/feature checks only: 147 cases
pytest tests/ui

# Individual UI suites
pytest tests/ui/admin/processing_area/
pytest tests/ui/admin/execution_source_config/
pytest tests/ui/crud/
pytest tests/ui/requester/
pytest tests/ui/dispatcher/
pytest tests/ui/supervisor/
pytest tests/ui/e2e/

# All 310 API-folder cases
pytest tests/api

# HTTP contracts only / legacy models only
pytest tests/api -m 'not api_model'
pytest tests/api -m api_model

# Configuration and diagnostics
TEST_ENV=staging pytest tests/ui/admin/processing_area/
pytest tests/ui tests/common --headed -rs
CLEANUP_TEST_DATA=0 pytest tests/ui/admin/processing_area/
```

Running `pytest` directly inside `tests/api/` also collects the API-folder suite.
Supply staging configuration and credentials before live execution. E2E tests
can submit requests and interact with Fleet Manager; select the intended environment.

## 18. Reports & Verification Evidence

Pytest writes one combined PDF directly into `reports/`, named
`report_<timestamp>.pdf`. Screenshots/build intermediates use temporary storage.
`REPORT_KEEP_RUNS` defaults to 20; use `0` to disable pruning. `--no-pdf` suppresses
PDF generation. The earlier `api_run_*` folder was a manual-run artifact, not the
central pytest report layout.

| Check | Observed result | Interpretation |
| --- | --- | --- |
| Current full collection | 483 cases collected; no collection errors | Inventory only; not a full test run. |
| MTS adapter validation earlier in this session | 182 passed | Legacy model/mock coverage only. |
| Historical cleanup regression verification | 7 passed before removal | The unit suite was removed; these results are historical, not current executable coverage. |
| Full live UI/API regression | Not executed for this document | Current release pass rate and approval remain unverified. |

## 19. Changelog

| Date | Change |
| --- | --- |
| 2026-09-29 | Updated current layout to `tests/api/`, `tests/common/`, and `tests/ui/`; corrected folder counts, commands, and links. All 483 cases retain their original ordering after accounting for the common path change. |
| 2026-09-28 | Rebuilt coverage from current pytest collection: 496 items; 310 API-folder cases including 182 MTS model checks; 173 UI cases; 13 unit cases. Added current cleanup boundaries, report behavior, and conditional coverage. |
| 2026-09-28 | Excluded four removed cases; reflected CRUD relocation and Settings/Notifications under Processing Area. Historical approvals and pass totals were not carried forward as current evidence. |
| 2026-09-25 | User-provided reference layout used for section structure; its inventory and historical counts are superseded by this snapshot. |

### Folder cleanup — 2026-09-29

Legacy MTS sources now live in `tests/api/`; the pytest adapter
remains in `tests/api/`. The manual browser runner and its folder were removed
at the user's request. Removed the unused API setup
placeholder and malformed MES repair utility. Collection was 496 cases at that point; removal of the unit suite reduced it to 483.

### Unit suite removal — 2026-09-29

Removed `tests/unit/` by request. After the common-suite move, the remaining
**483 cases** are **147 UI + 26 common + 310 API**. Earlier unit-test results
above are historical evidence.

### Common suite relocation — 2026-09-29

Shared browser tests now live in `tests/common/`. Counts: **147 UI + 26 common
+ 310 API = 483**. The common suite retains the `ui` marker and original execution
order, authentication, environment validation, and cleanup behavior.
