"""Structured views over the processing-area half of ``config/test_data.toml``.

``TestData`` exposes flat attributes, which is convenient at the call site but
means each page-object call re-lists the same five or seven values. These
builders group them so a fixture can pass one object, and so the dependency
order between the entities is stated in one place instead of being implied by
the order of statements in a test.
"""

from dataclasses import dataclass

from config.data import TestData


@dataclass(frozen=True)
class MaterialSpec:
    type_name: str
    production_unit: str
    pre_proc_time: int
    max_qty: int
    prefix: str


@dataclass(frozen=True)
class ContainerSpec:
    container_type: str
    sub_type: str
    length: int
    width: int
    height: int
    hitch_length: int
    qty: int


@dataclass(frozen=True)
class MachineSpec:
    name: str
    production_type: str


@dataclass(frozen=True)
class WorkflowSpec:
    name: str
    point_station_mode: str  # "Auto" or "Manual" (Confirmation Mode row 1)
    staging_area_mode: str   # "Auto" or "Manual" (Confirmation Mode row 2)
    pickup_type: str         # "mapping" or "static"
    pickup_station: str      # mapping name, or "" when static
    drop_type: str           # "mapping" or "static"
    drop_station: str        # mapping name, or "" when static


def material_spec():
    return MaterialSpec(
        type_name=TestData.material_type_name,
        production_unit=TestData.material_prod_unit,
        pre_proc_time=TestData.material_pre_proc,
        max_qty=TestData.material_max_qty,
        prefix=TestData.material_prefix,
    )


def container_spec():
    return ContainerSpec(
        container_type=TestData.container_type,
        sub_type=TestData.container_sub_type,
        length=TestData.container_length,
        width=TestData.container_width,
        height=TestData.container_height,
        hitch_length=TestData.container_hitch_length,
        qty=TestData.container_qty,
    )


def machine_specs():
    """Both machines, in the order the Machine Names tab expects them."""
    return (
        MachineSpec(TestData.machine_name_prod, "Production Type"),
        MachineSpec(TestData.machine_name_cons, "Consumption Type"),
    )


def machine_crud_spec():
    """Throwaway machine for test_06's create/verify/delete lifecycle."""
    label = "Production Type" if TestData.crud_machine_type == "production" else "Consumption Type"
    return MachineSpec(TestData.crud_machine_name, label)


def station_names():
    """Pickup and drop station mapping names.

    Matched exactly against the workflow wizard's Mapping ID dropdown, so one
    being a prefix of the other is fine. They must simply not be identical - the
    wizard rejects a workflow that picks up and drops at the same station.
    """
    return (TestData.station_mapping_name, TestData.station_mapping_name_2)


def workflow_specs():
    """Return all WorkflowSpec entries defined in [[workflow]] TOML array."""
    return [
        WorkflowSpec(
            name=w["name"],
            point_station_mode=w.get("point_station_mode", "Manual"),
            staging_area_mode=w.get("staging_area_mode", "Manual"),
            pickup_type=w.get("pickup_type", "mapping"),
            pickup_station=w.get("pickup_station", ""),
            drop_type=w.get("drop_type", "mapping"),
            drop_station=w.get("drop_station", ""),
        )
        for w in TestData.workflow_specs
    ]


def workflow_spec():
    """Return the first workflow (legacy single-workflow callers)."""
    specs = workflow_specs()
    if not specs:
        raise RuntimeError("No [[workflow]] entries found in config/test_data.toml.")
    return specs[0]


def station_mapping_crud_spec():
    """Throwaway station mapping name + Station ID for test_09's lifecycle test."""
    return (TestData.crud_station_name, TestData.crud_station_id)


# ── End-to-end suite — isolated views over the [e2e_*] tables ──────────────────
# Mirror the builders above but read TestData.e2e_*. Used only by
# the E2E fixtures in root conftest.py so an e2e run provisions its own `_e2e` Processing
# Area without disturbing the shared `test_9707` baseline.

def e2e_material_spec():
    return MaterialSpec(
        type_name=TestData.e2e_material_type_name,
        production_unit=TestData.e2e_material_prod_unit,
        pre_proc_time=TestData.e2e_material_pre_proc,
        max_qty=TestData.e2e_material_max_qty,
        prefix=TestData.e2e_material_prefix,
    )


def e2e_container_spec():
    return ContainerSpec(
        container_type=TestData.e2e_container_type,
        sub_type=TestData.e2e_container_sub_type,
        length=TestData.e2e_container_length,
        width=TestData.e2e_container_width,
        height=TestData.e2e_container_height,
        hitch_length=TestData.e2e_container_hitch_length,
        qty=TestData.e2e_container_qty,
    )


def e2e_machine_specs():
    """Both e2e machines, in the order the Machine Names tab expects them."""
    return (
        MachineSpec(TestData.e2e_machine_name_prod, "Production Type"),
        MachineSpec(TestData.e2e_machine_name_cons, "Consumption Type"),
    )


def e2e_station_names():
    """Pickup and drop station mapping labels for the e2e workflow."""
    return (TestData.e2e_station_mapping_name, TestData.e2e_station_mapping_name_2)


def e2e_workflow_specs():
    """Return all WorkflowSpec entries defined in the [[e2e_workflow]] array."""
    return [
        WorkflowSpec(
            name=w["name"],
            point_station_mode=w.get("point_station_mode", "Manual"),
            staging_area_mode=w.get("staging_area_mode", "Manual"),
            pickup_type=w.get("pickup_type", "mapping"),
            pickup_station=w.get("pickup_station", ""),
            drop_type=w.get("drop_type", "mapping"),
            drop_station=w.get("drop_station", ""),
        )
        for w in TestData.e2e_workflow_specs
    ]


def e2e_workflow_spec():
    """Return the first [[e2e_workflow]] entry (the one the baseline builds)."""
    specs = e2e_workflow_specs()
    if not specs:
        raise RuntimeError("No [[e2e_workflow]] entries found in config/test_data.toml.")
    return specs[0]


def validate_station_names():
    """Return a warning string when the two station names cannot work.

    Only identical names are a problem. Prefix overlap used to break the
    workflow wizard, but the Mapping ID dropdown is now matched exactly, so
    "pick" and "pick_2" are a valid pair.
    """
    pickup, drop = station_names()
    if pickup == drop:
        return (
            f"station_mapping.name and station_mapping.name_2 are both '{pickup}'. "
            f"The workflow wizard rejects a workflow whose Pickup and Drop are the "
            f"same station. Set distinct names in config/test_data.toml."
        )
    return None
