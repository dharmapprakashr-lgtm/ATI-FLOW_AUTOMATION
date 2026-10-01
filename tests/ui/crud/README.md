# CRUD lifecycle suite

This suite groups tests that create temporary entities, inspect them, exercise
supported updates, and delete them. Fixtures remain in the root `conftest.py`.

| File | Cases | Existing operations |
|---|---|---|
| `test_01_processing_area.py` | 2 | Create, verify, rename, delete; absent-area deletion |
| `test_02_material_container.py` | 2 | Material/container create, verify, delete |
| `test_03_machine.py` | 1 | Machine create, verify, delete |
| `test_04_station_mapping.py` | 1 | Mapping create, verify, delete |
| `test_05_devices.py` | 4 | Requester/dispatcher/supervisor create, update, verify, delete; absent-device deletion |

The folder groups existing lifecycle coverage; it does not imply every entity
has update coverage. Tests retain their assertions and use throwaway entities
rather than editing shared role devices. Some temporary names are fixed in TOML,
so concurrent runs against the same environment are still unsupported.

```bash
python3 -m pytest tests/ui/crud/ --headed
python3 -m pytest -m crud
python3 -m pytest tests/ui/crud/ --collect-only --no-pdf
```

All cases carry `admin` and `crud`; processing-area child-entity cases retain
`admin_pa`. Full runs execute CRUD after admin processing-area and device setup,
before role dashboards. Standalone runs use existing root fixtures to prepare
the required area/device dependencies. Real Fleet Manager staging areas and
station data must already be available.

Baseline creation, input validation, bulk upload, and role behavior remain in
their existing suites. WIP lifecycle cases remain deferred in
[the WIP backlog](../../../docs/WIP_INVENTORY_TEST_CASES.md).
