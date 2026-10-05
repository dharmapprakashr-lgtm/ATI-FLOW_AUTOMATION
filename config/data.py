"""Test input data — all values driven by ``config/test_data.toml``.

Separated from ``config/environment.py`` so that environment configuration
(``Settings``) and test-data configuration (``TestData``) are independent
concerns and can be imported individually without pulling each other in.

Edit ``config/test_data.toml`` to change any value — no need to touch test files.

Sections read with ``_raw[...]`` are *required*: a missing section raises
``KeyError`` at import time, which fails collection for the whole suite early.
Sections read with ``.get(...)`` fall back to the shown default.
"""

from pathlib import Path

try:
    import tomllib
except ImportError:          # Python 3.10 and below
    import tomli as tomllib  # type: ignore[no-redef]

_CONFIG_DIR = Path(__file__).resolve().parent
_DATA_FILE = _CONFIG_DIR / "test_data.toml"

with open(_DATA_FILE, "rb") as _f:
    _raw = tomllib.load(_f)


class TestData:
    """Central access point for all test input values."""

    # CRUD area/device prefixes and editable lifecycle inputs.
    crud_area_name_prefix = _raw["processing_area_crud"]["name_prefix"]
    crud_area_renamed_prefix = _raw["processing_area_crud"]["renamed_prefix"]
    crud_area_absent_prefix = _raw["processing_area_crud"]["absent_name_prefix"]
    crud_area_description = _raw["processing_area_crud"]["description"]
    crud_area_updated_description = _raw["processing_area_crud"]["updated_description"]
    crud_device_absent_prefix = _raw["devices_crud"]["absent_name_prefix"]
    crud_device_password = _raw["devices_crud"]["password"]
    crud_device_updated_password = _raw["devices_crud"]["updated_password"]
    crud_requester_name_prefix = _raw["devices_crud"]["requester_name_prefix"]
    crud_requester_id_prefix = _raw["devices_crud"]["requester_id_prefix"]
    crud_dispatcher_name_prefix = _raw["devices_crud"]["dispatcher_name_prefix"]
    crud_dispatcher_id_prefix = _raw["devices_crud"]["dispatcher_id_prefix"]
    crud_supervisor_name_prefix = _raw["devices_crud"]["supervisor_name_prefix"]
    crud_supervisor_id_prefix = _raw["devices_crud"]["supervisor_id_prefix"]
    _machine_api_ui_crud = _raw.get("machine_api_ui_crud", {})
    crud_api_area_name_prefix = _machine_api_ui_crud.get("area_name_prefix", "AUTO_PAM")
    crud_api_area_description = _machine_api_ui_crud.get("area_description", "Temporary automated API/UI test")
    crud_api_machine_name_prefix = _machine_api_ui_crud.get("machine_name_prefix", "AUTO_MACHINE")
    crud_api_default_point_type = _machine_api_ui_crud.get("default_point_type", "production_type")
    crud_api_production_point_type = _machine_api_ui_crud.get("production_point_type", "production_type")
    crud_api_production_label = _machine_api_ui_crud.get("production_label", "Production Type")
    crud_api_consumption_point_type = _machine_api_ui_crud.get("consumption_point_type", "consumption_type")
    crud_api_consumption_label = _machine_api_ui_crud.get("consumption_label", "Consumption Type")

    # Processing Area
    processing_area_name        = _raw["processing_area"]["name"]
    processing_area_description = _raw["processing_area"]["description"]

    # Staging Area (created in FM; AtiFlow only navigates + manages cell states)
    staging_area_name        = _raw["staging_area"]["name"]
    staging_area_bound_fleet = _raw.get("staging_area", {}).get("bound_fleet", "")
    staging_area_other_fleet = _raw.get("staging_area", {}).get("other_fleet", "")

    # Execution Source Config tabs
    exec_config_tabs = _raw["execution_source_config"]["tabs"]

    # Material
    material_type_name = _raw["material"]["material_type_name"]
    material_prod_unit = _raw["material"]["production_unit"]
    material_pre_proc  = _raw["material"]["pre_proc_time"]
    material_max_qty   = _raw["material"]["max_qty"]
    material_prefix    = _raw["material"]["prefix"]

    # Container (shared baseline — created in test_01, used by all downstream tests)
    container_type         = _raw["container"]["container_type"]
    container_sub_type     = _raw["container"]["sub_type"]
    container_length       = _raw["container"]["length"]
    container_width        = _raw["container"]["width"]
    container_height       = _raw["container"]["height"]
    container_hitch_length = _raw["container"]["hitch_length"]
    container_qty          = _raw["container"]["qty"]

    # Material CRUD (lifecycle test — created, edited, deleted in test_03)
    crud_material_name        = _raw.get("material_crud", {}).get("material_type_name", "crud_material_45")
    crud_material_name_edited = _raw.get("material_crud", {}).get("material_type_name_edited", "crud_material_45_edited")
    crud_material_prod_unit   = _raw.get("material_crud", {}).get("production_unit", "MFG3_10CFE")
    crud_material_pre_proc    = _raw.get("material_crud", {}).get("pre_proc_time", 1)
    crud_material_max_qty     = _raw.get("material_crud", {}).get("max_qty", 10)
    crud_material_prefix      = _raw.get("material_crud", {}).get("prefix", "CRD")

    # Container CRUD (lifecycle test — created, edited, deleted in test_03)
    crud_container_type         = _raw.get("container_crud", {}).get("container_type", "Trolley")
    crud_container_sub_type     = _raw.get("container_crud", {}).get("sub_type", "crud_trolly")
    crud_container_sub_type_ed  = _raw.get("container_crud", {}).get("sub_type_edited", "crud_trolly_edited")
    crud_container_length       = _raw.get("container_crud", {}).get("length", 100)
    crud_container_width        = _raw.get("container_crud", {}).get("width", 50)
    crud_container_height       = _raw.get("container_crud", {}).get("height", 30)
    crud_container_hitch_length = _raw.get("container_crud", {}).get("hitch_length", 100)
    crud_container_qty          = _raw.get("container_crud", {}).get("qty", 2)

    # Role-specific data (distinct from the [devices] entries below)
    requester_request_name = _raw["requester"]["sample_request_name"]
    requester_priority     = _raw["requester"]["priority"]

    # Requester > Make New Request wizard — real live WIP-inventory-backed SKU
    req_request_sku_code            = _raw.get("requester_request_material", {}).get("sku_code", "")
    req_request_sku_description     = _raw.get("requester_request_material", {}).get("sku_description", "")
    req_request_sub_sku_code        = _raw.get("requester_request_material", {}).get("sub_sku_code", "")
    req_request_sub_sku_description = _raw.get("requester_request_material", {}).get("sub_sku_description", "")
    req_request_zero_stock_sub_sku  = _raw.get("requester_request_material", {}).get("zero_stock_sub_sku", "")
    mes_machine_name    = _raw["mes"]["machine_name"]
    dispatcher_zone     = _raw["dispatcher"]["zone"]
    supervisor_report   = _raw["supervisor"]["report_name"]

    # Supervisor dashboard (/stagingArea, /opsinventory, /auto-trips)
    _sup_dash = _raw.get("supervisor_dashboard", {})
    _sup_devices = _raw.get("devices", {})
    sup_bound_processing_area  = _sup_dash.get("bound_processing_area", _sup_devices.get("supervisor_processing_areas", "test_45"))
    sup_bound_staging_area     = _sup_dash.get("bound_staging_area", _sup_devices.get("supervisor_staging_areas", "AH_stage"))
    sup_staging_grid_size      = _sup_dash.get("staging_area_grid_size", "1 x 4 cells")
    sup_legend_states          = _sup_dash.get("legend_states", ["Available", "Reserved", "Blocked", "Filled"])
    sup_reserved_colour        = _sup_dash.get("reserved_colour", "#FFB300")
    sup_wip_columns            = _sup_dash.get("wip_columns", [])
    sup_notification_titles    = _sup_dash.get("notification_titles", [])
    sup_mes_error_text         = _sup_dash.get("mes_error_text", "")

    # Dispatcher > Requests screen (/approval)
    disp_req_default_station = _raw.get("dispatcher_requests", {}).get("default_station", "")
    disp_req_alt_station     = _raw.get("dispatcher_requests", {}).get("alt_station", "")
    disp_req_empty_state     = _raw.get("dispatcher_requests", {}).get("empty_state_contains", "requests found")
    disp_req_no_match        = _raw.get("dispatcher_requests", {}).get("no_match_search", "ZZZ_NO_MATCH_9999_QWERTY")

    # Devices (Execution Source Config records)
    req_device_name    = _raw.get("devices", {}).get("requester_name", "Test_Requester")
    req_device_id      = _raw.get("devices", {}).get("requester_id", "REQ-001")
    req_device_pass    = _raw.get("devices", {}).get("requester_pass", "password123")
    req_bound_machines  = _raw.get("devices", {}).get("requester_bound_machines", "Machine 1")
    req_bound_workflows = _raw.get("devices", {}).get("requester_bound_workflows", "Workflow 1")
    req_staging_areas   = _raw.get("devices", {}).get("requester_staging_areas", "Staging Area 1")
    req_update_pass     = _raw.get("devices", {}).get("requester_update_pass", "newpass123")
    req_update_machines  = _raw.get("devices", {}).get("requester_update_bound_machines", "GOOD")
    req_update_workflows = _raw.get("devices", {}).get("requester_update_bound_workflows", "A1")

    disp_device_name   = _raw.get("devices", {}).get("dispatcher_name", "Test_Dispatcher")
    disp_device_id     = _raw.get("devices", {}).get("dispatcher_id", "DIS-001")
    disp_device_pass   = _raw.get("devices", {}).get("dispatcher_pass", "password123")
    disp_bound_stations = _raw.get("devices", {}).get("dispatcher_bound_stations", "Station 1")
    disp_staging_areas  = _raw.get("devices", {}).get("dispatcher_staging_areas", "Staging Area 1")
    disp_update_pass    = _raw.get("devices", {}).get("dispatcher_update_pass", "newpass123")
    disp_update_stations = _raw.get("devices", {}).get("dispatcher_update_bound_stations", "sta_4_Green")

    sup_device_name     = _raw.get("devices", {}).get("supervisor_name", "Test_Supervisor")
    sup_device_id       = _raw.get("devices", {}).get("supervisor_id", "SUP-001")
    sup_device_pass     = _raw.get("devices", {}).get("supervisor_pass", "password123")
    sup_staging_areas   = _raw.get("devices", {}).get("supervisor_staging_areas", "Staging Area 1")
    sup_processing_areas = _raw.get("devices", {}).get("supervisor_processing_areas", "mohit_test_area")
    sup_update_pass     = _raw.get("devices", {}).get("supervisor_update_pass", "newpass123")
    sup_update_processing_areas = _raw.get("devices", {}).get("supervisor_update_processing_areas", "area 1")

    # Station Mapping
    station_mapping_name   = _raw.get("station_mapping", {}).get("name", "SM_test_01")
    station_mapping_name_2 = _raw.get("station_mapping", {}).get("name_2", "SM_test_01_new")
    station_id             = _raw.get("station_mapping", {}).get("station_id")
    station_id_2           = _raw.get("station_mapping", {}).get("station_id_2")

    # Machine Name
    machine_area_name = _raw["processing_area"]["name"]
    machine_name_prod = _raw.get("machine_name", {}).get("machine_name_prod", "M-001_Prod")
    machine_name_cons = _raw.get("machine_name", {}).get("machine_name_cons", "M-001_Cons")

    # Machine Name CRUD (lifecycle test — created and deleted in test_06)
    crud_machine_name    = _raw.get("machine_name_crud", {}).get("name", "crud_machine_45")
    crud_machine_name_ed = _raw.get("machine_name_crud", {}).get("name_edited", "crud_machine_45_edited")
    crud_machine_type    = _raw.get("machine_name_crud", {}).get("type", "production")

    # Station Mapping CRUD (lifecycle test — created and deleted in test_09)
    crud_station_name    = _raw.get("station_mapping_crud", {}).get("name", "crud_pick")
    crud_station_name_ed = _raw.get("station_mapping_crud", {}).get("name_edited", "crud_pick_edited")
    crud_station_id      = _raw.get("station_mapping_crud", {}).get("station_id", "crud_station_01")

    # Workflows — list of dicts, each with name/pickup_type/pickup_station/drop_type/drop_station
    workflow_specs = _raw.get("workflow", [])
    # Backwards-compat: single [workflow] table (non-array) → wrap in a list
    if isinstance(workflow_specs, dict):
        workflow_specs = [workflow_specs]
    # Convenience: the first workflow's name (used by legacy references)
    workflow_name = workflow_specs[0]["name"] if workflow_specs else "mohit_workflow"

    # ── End-to-end suite — isolated names ([e2e_*] tables in test_data.toml) ────
    # Only the names AtiFlow creates are overridden here; every real Fleet
    # Manager / live-inventory value (station ids, fleet, AH_stage, the live
    # SKU) falls back to the shared attribute above so it stays identical.
    # Consumed by tests/ui/e2e/ only — the role suites never read these.
    _e2e_pa   = _raw.get("e2e_processing_area", {})
    _e2e_mat  = _raw.get("e2e_material", {})
    _e2e_con  = _raw.get("e2e_container", {})
    _e2e_mac  = _raw.get("e2e_machine_name", {})
    _e2e_sm   = _raw.get("e2e_station_mapping", {})
    _e2e_dev  = _raw.get("e2e_devices", {})

    e2e_processing_area_name        = _e2e_pa.get("name", processing_area_name)
    e2e_processing_area_description = _e2e_pa.get("description", processing_area_description)

    e2e_material_type_name = _e2e_mat.get("material_type_name", material_type_name)
    e2e_material_prod_unit = _e2e_mat.get("production_unit", material_prod_unit)
    e2e_material_pre_proc  = _e2e_mat.get("pre_proc_time", material_pre_proc)
    e2e_material_max_qty   = _e2e_mat.get("max_qty", material_max_qty)
    e2e_material_prefix    = _e2e_mat.get("prefix", material_prefix)

    e2e_container_type         = _e2e_con.get("container_type", container_type)
    e2e_container_sub_type     = _e2e_con.get("sub_type", container_sub_type)
    e2e_container_length       = _e2e_con.get("length", container_length)
    e2e_container_width        = _e2e_con.get("width", container_width)
    e2e_container_height       = _e2e_con.get("height", container_height)
    e2e_container_hitch_length = _e2e_con.get("hitch_length", container_hitch_length)
    e2e_container_qty          = _e2e_con.get("qty", container_qty)

    e2e_machine_name_prod = _e2e_mac.get("machine_name_prod", machine_name_prod)
    e2e_machine_name_cons = _e2e_mac.get("machine_name_cons", machine_name_cons)

    e2e_station_mapping_name   = _e2e_sm.get("name", station_mapping_name)
    e2e_station_mapping_name_2 = _e2e_sm.get("name_2", station_mapping_name_2)
    e2e_station_id             = _e2e_sm.get("station_id", station_id)
    e2e_station_id_2           = _e2e_sm.get("station_id_2", station_id_2)

    e2e_req_device_name     = _e2e_dev.get("requester_name", req_device_name)
    e2e_req_device_id       = _e2e_dev.get("requester_id", req_device_id)
    e2e_req_device_pass     = _e2e_dev.get("requester_pass", req_device_pass)
    e2e_req_bound_machines  = _e2e_dev.get("requester_bound_machines", req_bound_machines)
    e2e_req_bound_workflows = _e2e_dev.get("requester_bound_workflows", req_bound_workflows)
    e2e_req_staging_areas   = _e2e_dev.get("requester_staging_areas", req_staging_areas)

    e2e_disp_device_name    = _e2e_dev.get("dispatcher_name", disp_device_name)
    e2e_disp_device_id      = _e2e_dev.get("dispatcher_id", disp_device_id)
    e2e_disp_device_pass    = _e2e_dev.get("dispatcher_pass", disp_device_pass)
    e2e_disp_bound_stations = _e2e_dev.get("dispatcher_bound_stations", disp_bound_stations)
    e2e_disp_staging_areas  = _e2e_dev.get("dispatcher_staging_areas", disp_staging_areas)

    e2e_sup_device_name      = _e2e_dev.get("supervisor_name", sup_device_name)
    e2e_sup_device_id        = _e2e_dev.get("supervisor_id", sup_device_id)
    e2e_sup_device_pass      = _e2e_dev.get("supervisor_pass", sup_device_pass)
    e2e_sup_staging_areas    = _e2e_dev.get("supervisor_staging_areas", sup_staging_areas)
    e2e_sup_processing_areas = _e2e_dev.get("supervisor_processing_areas", sup_processing_areas)

    # [[e2e_workflow]] array — same shape as workflow_specs above.
    e2e_workflow_specs = _raw.get("e2e_workflow", [])
    if isinstance(e2e_workflow_specs, dict):
        e2e_workflow_specs = [e2e_workflow_specs]
