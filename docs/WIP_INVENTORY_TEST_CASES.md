# WIP Inventory test cases — deferred to the next suite version

Status: **Not included in the current automated suite.**

This backlog preserves 17 removed test functions and the WIP portions of shared
checks. These are historical test expectations, not current execution results.
Revalidate the product contract before implementing them in the next version.
No configuration-guide changes are part of this work.

## Preconditions for restoration

- Admin and supervisor accounts must have access to the intended processing areas.
- Use a suite-owned material/SKU with real stock and a matching WIP row in the
  requester machine/workflow's processing area. Do not use unrelated live stock
  for destructive material/container checks.
- Cross-area cases need at least two assigned areas with distinguishable inventory.
- Control stock changes while asserting row counts or round-trip table equality;
  volatile live data can otherwise cause false failures.
- Confirm the quantity formula: Total Qty = In Transit + Processed + Pre-processed
  + Requested, and the expected columns configured for the supervisor.
- Confirm whether the release is read-only/manual-refresh or supports adjustments
  and automatic refresh. Absence-of-control guards are not positive validation of
  adjustment, audit, or real-time update features.
- A task lifecycle test needs request correlation, completion/cancellation control,
  bounded polling, and cleanup. The former TC_WIP_002 was a placeholder: its title
  referred to task completion while its notes described request/cancellation.
  Define the lifecycle transitions and expected deltas before implementation.

## Case index

| # | Historical case | Previous automation status |
|---|---|---|
| 1 | TC_WIP_002 — WIP quantity updates when a task completes | Expected failure, not executed (xfail run=False) |
| 2 | TC_WIP_005 — WIP Inventory is a live, read-only projection | Enabled |
| 3 | TC-015 — Aggregated table has the same columns the Requester view uses | Enabled |
| 4 | TC-015 — Aggregated table obeys the shared rollup contract (Total = parts) | Enabled with conditional data skips |
| 5 | TC-017/TC-042 — The table only ever shows the selected area's inventory | Enabled with conditional data skips |
| 6 | TC-017 — Switching area back and forth keeps the table correct | Enabled with conditional data skips |
| 7 | TC_SUP_ADJ_GUARD — WIP Inventory exposes no write/adjustment control | Enabled |
| 8 | TC-020/TC-021 — No Add / Remove action anywhere on the WIP screen | Enabled |
| 9 | TC-022 — WIP quantities are not editable, so none can be driven below zero | Enabled |
| 10 | TC-027 — No free Sub-SKU Type entry to reject an invalid value in | Enabled |
| 11 | TC-023/TC-024/TC-039 — No adjustment audit-log surface or route | Enabled |
| 12 | TC-016/TC-026 — WIP Inventory offers a working manual Refresh + 'Updated' marker | Enabled |
| 13 | TC-016/TC-041 — The supervisor dashboards use a manual-refresh model (no live push) | Enabled |
| 14 | TC-018 — Switching Processing Area reloads the aggregated table | Enabled with conditional data skips |
| 15 | TC_PA_TAB_004 — 'WIP Inventory' tab is visible and enabled | Enabled |
| 16 | TC_MAT_003 — Deleting a Material referenced by WIP or open task | Expected failure, not executed (xfail run=False) |
| 17 | TC_CON_003 — A container cannot be assigned to two locations at once | Expected failure, not executed (xfail run=False) |

## Case details and former implementation

The code excerpts below are reference material only: Markdown is not collected by
pytest. They retain assertions, steps, skip conditions, and known limitations so
next-version work does not depend on deleted source files. Former source paths
are historical and may no longer exist.

### 1. TC_WIP_002 — WIP quantity updates when a task completes

Former source: `tests/ui/admin/processing_area/test_16_wip_inventory.py` → `test_wip_quantity_updates_when_task_completes`.

Previous status: Expected failure, not executed (xfail run=False). Current status: deferred.

```python
    @allure.title("TC_WIP_002 — WIP quantity updates when a task completes")
    @pytest.mark.xfail(
        reason="Blocked on test data, not fixtures (requester_page now exists). "
               "Verified live 2026-09-04: the only SKU this requester device can "
               "order (DGT15A0666-01/DTE15A0666, real stock) has no row in any "
               "WIP Inventory tab this suite manages (test_45 empty; test_9707 "
               "holds only the DSW* throwaway family), so a placed order would "
               "leave an unverifiable in-flight request on live Fleet Manager. "
               "Wire to requester_page + pa_page once the requester's bound "
               "machine/workflow feeds a PA whose WIP tab this suite reads.",
        run=False,
        strict=False,
    )
    def test_wip_quantity_updates_when_task_completes(
        self, admin_page, processing_area
    ):
        """
        ID     : TC_WIP_002
        Title  : WIP quantity updates when a task completes
        Reason : The whole point of WIP Inventory is real-time stock tracking.
                 If the count does not change on task activity, planning data
                 becomes stale immediately.
        """
```

### 2. TC_WIP_005 — WIP Inventory is a live, read-only projection

Former source: `tests/ui/admin/processing_area/test_16_wip_inventory.py` → `test_wip_inventory_is_live_readonly_projection`.

Previous status: Enabled. Current status: deferred.

```python
    @allure.title("TC_WIP_005 — WIP Inventory is a live, read-only projection")
    def test_wip_inventory_is_live_readonly_projection(self, admin_page, pa_page):
        """
        ID     : TC_WIP_005
        Title  : WIP Inventory renders a computed, refreshable, read-only view
        Reason : WIP Inventory is the source-of-truth for stock in transit.
                 It must show a genuinely computed rollup, let an operator
                 re-pull it on demand, and never expose an editable quantity
                 here (stock only moves via tasks).

        Structural checks run every time. The rollup + read-only-panel checks
        run only when the PA currently has WIP rows — that row set is volatile
        live data, and "empty right now" is a valid state, not a failure.
        """
        pa_page.navigate_to_existing_area(WIP_DATA_PA)
        pa_page.go_to_wip_inventory()
        wip = WipInventoryPage(admin_page)
        wip.wait_until_loaded()

        with allure.step("The computed columns are present"):
            headers = wip.column_headers()
            for label in ("In Transit", "Processed", "Pre-processed",
                          "Requested", "Total Qty"):
                assert label in headers, f"Missing WIP column '{label}': {headers}"

        with allure.step("The tab exposes NO create / edit / import control"):
            offenders = wip.write_control_labels()
            assert not offenders, (
                f"WIP Inventory now has a write-shaped control {offenders} — the "
                "app grew a WIP creation/import path; add write-path coverage "
                "(create/edit/delete lifecycle, quantity boundaries, "
                "material+container prerequisite) against it."
            )

        with allure.step("Refresh re-fetches without breaking the view"):
            before = len(wip.row_records())
            wip.refresh()
            after = len(wip.row_records())
            assert after == before, (
                f"Row count changed across a plain Refresh: {before} → {after}"
            )
            assert admin_page.get_by_role("tab", name="WIP Inventory").is_visible()

        records = wip.row_records()
        if not records:
            allure.attach(
                f"Processing Area '{WIP_DATA_PA}' has no WIP rows right now — "
                "rollup / detail-panel checks skipped (valid: WIP is populated "
                "by task flow, TC_WIP_002).",
                name="WIP empty",
            )
            return

        with allure.step("Total Qty is a real rollup of the other quantity columns"):
            bad = [r for r in records if not wip.rollup_ok(r)]
            assert not bad, (
                "Total Qty != In Transit + Processed + Pre-processed + Requested "
                f"for {len(bad)} row(s), e.g. {bad[0]}"
            )

        with allure.step("A row's detail panel is strictly read-only"):
            panel = wip.open_row_detail(0)
            assert panel.is_visible(), "Row info icon did not open a detail panel."
            assert wip.detail_editable_field_count() == 0, (
                "WIP detail panel now has an editable field — the app has grown "
                "a WIP edit path; add WIP write-path coverage."
            )
            wip.close_detail()
```

### 3. TC-015 — Aggregated table has the same columns the Requester view uses

Former source: `tests/ui/supervisor/test_06_wip_inventory_dashboard.py` → `test_aggregated_table_columns_match_contract`.

Previous status: Enabled. Current status: deferred.

```python
    @allure.title("TC-015 — Aggregated table has the same columns the Requester view uses")
    @pytest.mark.smoke
    def test_aggregated_table_columns_match_contract(self, supervisor_page):
        """
        ID     : TC-015
        Title  : The supervisor's aggregated inventory table matches the shared
                 column contract (same as Requester / admin WIP)
        Reason : If the supervisor and requester read different columns for the
                 same area, they cannot reconcile a discrepancy on a call.
        """
        home = SupervisorHomePage(supervisor_page)
        home.go_to_wip_inventory()
        headers = home.wip_column_headers()
        assert headers == TestData.sup_wip_columns, (
            f"WIP columns {headers} != agreed contract {TestData.sup_wip_columns}"
        )
```

### 4. TC-015 — Aggregated table obeys the shared rollup contract (Total = parts)

Former source: `tests/ui/supervisor/test_06_wip_inventory_dashboard.py` → `test_aggregated_table_rollup_contract`.

Previous status: Enabled with conditional data skips. Current status: deferred.

```python
    @allure.title("TC-015 — Aggregated table obeys the shared rollup contract (Total = parts)")
    def test_aggregated_table_rollup_contract(self, supervisor_page):
        """
        ID     : TC-015
        Title  : The supervisor's aggregated table shows the same computed
                 rollup the admin WIP tab and Requester view use —
                 Total Qty == In Transit + Processed + Pre-processed + Requested
        Reason : "Identical between Requester and Supervisor views" (TC-015)
                 means the same projection and the same arithmetic. Verified per
                 row when `test_45` has data; self-skips when it is empty
                 (a valid, volatile state).

        Known defect (tester, 2026-09-07, tracked in docs §7, NOT asserted
        here): a request raised on the requester side does not raise the
        supervisor's `Requested` figure for the same area. Proving that needs a
        real order round-trip fixture (same blocker as requester/test_17).
        """
        home = SupervisorHomePage(supervisor_page)
        home.go_to_wip_inventory()
        records = home.wip_row_records()
        if not records:
            pytest.skip(
                f"'{TestData.sup_bound_processing_area}' has no WIP rows right "
                f"now — nothing to check the rollup arithmetic against."
            )
        bad = [r for r in records if not SupervisorHomePage.wip_rollup_ok(r)]
        assert not bad, (
            f"{len(bad)} WIP row(s) violate Total Qty == In Transit + Processed "
            f"+ Pre-processed + Requested: {bad[:3]}"
        )
```

### 5. TC-017/TC-042 — The table only ever shows the selected area's inventory

Former source: `tests/ui/supervisor/test_06_wip_inventory_dashboard.py` → `test_no_cross_processing_area_contamination`.

Previous status: Enabled with conditional data skips. Current status: deferred.

```python
    @allure.title("TC-017/TC-042 — The table only ever shows the selected area's inventory")
    def test_no_cross_processing_area_contamination(self, supervisor_page):
        """
        ID     : TC-017 / TC-042
        Title  : Selecting one processing area never shows another area's rows
        Reason : Merged inventory across areas would have the supervisor
                 double-counting or acting on stock that is not on their floor.
        """
        home = SupervisorHomePage(supervisor_page)
        options = home.open_processing_area_dropdown()
        home.close_dropdown()
        home.go_to_wip_inventory()

        if len(options) < 2:
            # Single bound area: isolation is enforced by the selector only
            # offering that one area (asserted in test_02). Confirm the table
            # is scoped to it and does not silently show "all areas".
            rows = home.wip_row_texts()
            if not rows or home.wip_is_empty_state():
                pytest.skip(
                    f"'{TestData.sup_bound_processing_area}' has no WIP rows "
                    f"right now (valid, volatile live state) and the device is "
                    f"bound to a single area — no cross-area comparison to make."
                )
            assert home.wip_pagination_total() == len(rows) or home.wip_pagination_total() is not None
            return

        # 2+ bound areas: each area's row set must be disjoint in identity.
        home.select_processing_area(options[0])
        first_rows = set(home.wip_row_texts())
        home.select_processing_area(options[1])
        second_rows = set(home.wip_row_texts())
        if not first_rows or not second_rows:
            pytest.skip("one of the two areas has no WIP rows to compare right now")
        assert first_rows.isdisjoint(second_rows), (
            "The two processing areas share identical WIP rows — data is bleeding "
            "across areas."
        )
```

### 6. TC-017 — Switching area back and forth keeps the table correct

Former source: `tests/ui/supervisor/test_06_wip_inventory_dashboard.py` → `test_switching_area_keeps_table_consistent`.

Previous status: Enabled with conditional data skips. Current status: deferred.

```python
    @allure.title("TC-017 — Switching area back and forth keeps the table correct")
    def test_switching_area_keeps_table_consistent(self, supervisor_page):
        """
        ID     : TC-017
        Title  : Table content always matches the currently selected area, even
                 after switching away and back
        """
        home = SupervisorHomePage(supervisor_page)
        options = home.open_processing_area_dropdown()
        home.close_dropdown()
        if len(options) < 2:
            pytest.skip(
                "Supervisor bound to a single processing area — no switching to verify."
            )
        home.go_to_wip_inventory()
        home.select_processing_area(options[0])
        baseline = home.wip_row_texts()
        home.select_processing_area(options[1])
        home.select_processing_area(options[0])
        assert home.wip_row_texts() == baseline, (
            "WIP rows for the original area changed after a round-trip switch."
        )
```

### 7. TC_SUP_ADJ_GUARD — WIP Inventory exposes no write/adjustment control

Former source: `tests/ui/supervisor/test_08_inventory_adjustment.py` → `test_wip_inventory_has_no_write_surface`.

Previous status: Enabled. Current status: deferred.

```python
    @allure.title("TC_SUP_ADJ_GUARD — WIP Inventory exposes no write/adjustment control")
    def test_wip_inventory_has_no_write_surface(self, supervisor_page):
        """
        ID     : TC_SUP_ADJ_GUARD
        Title  : The supervisor WIP dashboard is read-only (Refresh + search only)
        Reason : Primary tripwire for the whole TC-020..TC-027/TC-039 block.
        """
        home = SupervisorHomePage(supervisor_page)
        home.go_to_wip_inventory()

        labels = [b.strip().lower()
                  for b in supervisor_page.locator("button").all_text_contents()
                  if b.strip()]
        offenders = [l for l in labels if any(w == l or w in l.split() for w in _WRITE_WORDS)]
        assert not offenders, (
            f"WIP Inventory now shows write-like control(s) {offenders} — the "
            f"adjustment feature may have shipped. Re-enable TC-020..TC-027 / "
            f"TC-039 as positive assertions."
        )
        assert home.wip_refresh_btn.is_visible()
```

### 8. TC-020/TC-021 — No Add / Remove action anywhere on the WIP screen

Former source: `tests/ui/supervisor/test_08_inventory_adjustment.py` → `test_no_add_or_remove_action`.

Previous status: Enabled. Current status: deferred.

```python
    @allure.title("TC-020/TC-021 — No Add / Remove action anywhere on the WIP screen")
    def test_no_add_or_remove_action(self, supervisor_page):
        """
        ID     : TC-020 / TC-021
        Title  : There is no Action = Add / Remove control to change a Sub-SKU
                 quantity
        Reason : Both cases depend on that control existing. Locks its absence.
        """
        home = SupervisorHomePage(supervisor_page)
        home.go_to_wip_inventory()
        body = supervisor_page.locator("body").inner_text().lower()
        for token in ("action", "add stock", "remove stock", "add quantity", "remove quantity"):
            assert token not in body, (
                f"WIP screen now contains {token!r} — an adjustment action may exist."
            )
        # The only interactive controls are Refresh + search + pagination.
        assert supervisor_page.get_by_role("button", name="Refresh").is_visible()
        assert supervisor_page.locator("#wip-search").is_visible()
```

### 9. TC-022 — WIP quantities are not editable, so none can be driven below zero

Former source: `tests/ui/supervisor/test_08_inventory_adjustment.py` → `test_wip_quantities_are_read_only`.

Previous status: Enabled. Current status: deferred.

```python
    @allure.title("TC-022 — WIP quantities are not editable, so none can be driven below zero")
    def test_wip_quantities_are_read_only(self, supervisor_page):
        """
        ID     : TC-022
        Title  : No editable quantity field exists, so 'cannot reduce below zero'
                 is enforced by there being no reduce path at all
        Reason : The below-zero guard is moot while the numbers are a read-only
                 projection. Asserts the table body has no inputs.
        """
        home = SupervisorHomePage(supervisor_page)
        home.go_to_wip_inventory()
        editable = supervisor_page.locator(
            "table tbody input:not([readonly]):not([disabled]), "
            "table tbody [contenteditable='true']"
        )
        assert editable.count() == 0, (
            f"WIP table body now has {editable.count()} editable field(s) — "
            f"quantities may be adjustable."
        )
```

### 10. TC-027 — No free Sub-SKU Type entry to reject an invalid value in

Former source: `tests/ui/supervisor/test_08_inventory_adjustment.py` → `test_no_sub_sku_type_entry_field`.

Previous status: Enabled. Current status: deferred.

```python
    @allure.title("TC-027 — No free Sub-SKU Type entry to reject an invalid value in")
    def test_no_sub_sku_type_entry_field(self, supervisor_page):
        """
        ID     : TC-027
        Title  : There is no Sub-SKU Type input on any supervisor screen
        Reason : Manual note — SKU details are auto-filled elsewhere; the
                 supervisor never types a Sub-SKU Type, so there is nothing to
                 validate/reject. Locks that.
        """
        home = SupervisorHomePage(supervisor_page)
        for goto in (home.go_to_wip_inventory, home.go_to_auto_trips):
            goto()
            body = supervisor_page.locator("body").inner_text().lower()
            assert "sub-sku type" not in body and "sub sku type" not in body, (
                "A 'Sub-SKU Type' field appeared on a supervisor screen."
            )
```

### 11. TC-023/TC-024/TC-039 — No adjustment audit-log surface or route

Former source: `tests/ui/supervisor/test_08_inventory_adjustment.py` → `test_no_adjustment_audit_log`.

Previous status: Enabled. Current status: deferred.

```python
    @allure.title("TC-023/TC-024/TC-039 — No adjustment audit-log surface or route")
    def test_no_adjustment_audit_log(self, supervisor_page):
        """
        ID     : TC-023 / TC-024 / TC-039
        Title  : There is no adjustment history / audit-log view for the
                 supervisor — not in the nav, not by direct URL
        Reason : All three cases assume an audit log to read entries from. Locks
                 its absence: the sidebar has exactly the three operational
                 screens, and adjustment/audit routes are blocked.
        """
        home = SupervisorHomePage(supervisor_page)
        assert home.sidebar_nav_labels() == ["Staging Area", "WIP Inventory", "Auto Trips"], (
            f"Sidebar changed: {home.sidebar_nav_labels()} — an audit/history "
            f"screen may have been added."
        )
        for route in ("/adjustment", "/inventory-adjustment", "/opsinventory/adjust",
                      "/audit", "/opsinventory/history"):
            supervisor_page.goto(config.app_url + route, wait_until="domcontentloaded")
            supervisor_page.wait_for_timeout(1200)
            assert _blocked(supervisor_page), (
                f"Route {route!r} resolved for the supervisor (url="
                f"{supervisor_page.url}) — an adjustment/audit surface may exist."
            )
```

### 12. TC-016/TC-026 — WIP Inventory offers a working manual Refresh + 'Updated' marker

Former source: `tests/ui/supervisor/test_07_realtime_refresh.py` → `test_wip_manual_refresh_affordance`.

Previous status: Enabled. Current status: deferred.

```python
    @allure.title("TC-016/TC-026 — WIP Inventory offers a working manual Refresh + 'Updated' marker")
    def test_wip_manual_refresh_affordance(self, supervisor_page):
        """
        ID     : TC-016 / TC-026
        Title  : The WIP dashboard exposes a manual Refresh control and a
                 last-updated marker, and Refresh does not error
        Reason : Given the app does not push live, the supervisor's only way to
                 trust the numbers is an explicit Refresh + a visible "Updated
                 <time>". If either is missing they cannot tell stale from live.
        """
        home = SupervisorHomePage(supervisor_page)
        home.go_to_wip_inventory()

        assert home.wip_refresh_btn.is_visible(), "WIP dashboard has no Refresh button."
        assert "updated" in home.wip_updated_label().lower(), (
            f"WIP dashboard shows no last-updated marker (got {home.wip_updated_label()!r})."
        )
        home.wip_refresh()  # must not throw / navigate away
        assert "/opsinventory" in supervisor_page.url
        assert home.wip_column_headers(), "WIP table gone after Refresh."
```

### 13. TC-016/TC-041 — The supervisor dashboards use a manual-refresh model (no live push)

Former source: `tests/ui/supervisor/test_07_realtime_refresh.py` → `test_no_auto_refresh_mechanism`.

Previous status: Enabled. Current status: deferred.

```python
    @allure.title("TC-016/TC-041 — The supervisor dashboards use a manual-refresh model (no live push)")
    def test_no_auto_refresh_mechanism(self, supervisor_page):
        """
        ID     : TC-016 / TC-041
        Title  : WIP Inventory and Auto Trips expose a manual Refresh only —
                 there is no auto/live-refresh toggle or indicator, and an open
                 WIP view does not reload itself within a short idle window
        Reason : Locks the current contract (manual observation: values change
                 only after a manual Refresh). If a live-push / auto-refresh
                 control is ever added this test fails, flagging that TC-016 /
                 TC-041 should become positive "updates within N seconds"
                 assertions.
        """
        home = SupervisorHomePage(supervisor_page)
        home.go_to_wip_inventory()

        page_text = supervisor_page.locator("body").inner_text().lower()
        for token in ("auto-refresh", "auto refresh", "live update", "real-time", "realtime", "streaming"):
            assert token not in page_text, (
                f"WIP Inventory now advertises {token!r} — the manual-refresh "
                f"contract has changed; rewrite TC-016/TC-041 as positive."
            )

        # An idle, untouched WIP view must not reload on its own.
        before = home.wip_row_texts()
        supervisor_page.wait_for_timeout(6000)
        after = home.wip_row_texts()
        assert before == after, (
            "The WIP table changed with no user action and no Refresh click — "
            "an auto-refresh may have been added."
        )
        assert home.wip_refresh_btn.is_visible(), "Manual Refresh button is gone."
```

### 14. TC-018 — Switching Processing Area reloads the aggregated table

Former source: `tests/ui/supervisor/test_02_processing_area_selector.py` → `test_switching_processing_area_reloads_table`.

Previous status: Enabled with conditional data skips. Current status: deferred.

```python
    @allure.title("TC-018 — Switching Processing Area reloads the aggregated table")
    def test_switching_processing_area_reloads_table(self, supervisor_page):
        """
        ID     : TC-018
        Title  : Selecting a different Processing Area reloads the WIP table
        Reason : Stale data after a switch would have the supervisor acting on
                 the wrong floor's inventory.
        """
        home = SupervisorHomePage(supervisor_page)
        options = home.open_processing_area_dropdown()
        home.close_dropdown()

        if len(options) < 2:
            pytest.skip(
                f"Supervisor device '{TestData.sup_device_name}' is bound to a "
                f"single processing area {options} — nothing to switch to. "
                f"Rebind it to 2+ areas in Execution Source Config to enable "
                f"this case (same limitation as requester/test_02)."
            )

        home.go_to_wip_inventory()
        first = home.bound_processing_area_text()
        other = next(o for o in options if o != first)
        home.select_processing_area(other)
        assert home.bound_processing_area_text() == other, (
            f"Selector still reads {home.bound_processing_area_text()!r} after "
            f"choosing {other!r}."
        )
        # The table must have re-rendered (headers still present, no crash).
        assert home.wip_column_headers(), "WIP table did not re-render after PA switch."
```

### 15. TC_PA_TAB_004 — 'WIP Inventory' tab is visible and enabled

Former source: `tests/ui/admin/processing_area/test_02_area_tabs_visibility.py` → `test_wip_inventory_tab_visible`.

Previous status: Enabled. Current status: deferred.

```python
    @allure.title("TC_PA_TAB_004 — 'WIP Inventory' tab is visible and enabled")
    def test_wip_inventory_tab_visible(self, admin_page):
        """
        ID     : TC_PA_TAB_004
        Title  : WIP Inventory tab is present inside the Processing Area
        Reason : WIP tracking depends on this tab being accessible to admins.
        """
        with allure.step("Check 'WIP Inventory' tab is visible and not disabled"):
            tab = admin_page.get_by_role("tab", name="WIP Inventory")
            expect(tab).to_be_visible(timeout=8_000)
            expect(tab).not_to_have_attribute("aria-disabled", "true")
```

### 16. TC_MAT_003 — Deleting a Material referenced by WIP or open task

Former source: `tests/ui/admin/processing_area/test_04_material_container_validation.py` → `test_delete_material_referenced_by_wip_or_open_task`.

Previous status: Expected failure, not executed (xfail run=False). Current status: deferred.

```python
    @allure.title("TC_MAT_003 — Deleting a Material referenced by WIP or open task")
    @pytest.mark.xfail(
        reason="No safe path to the precondition in this environment. To "
               "reference a material from WIP or an open task it must have real "
               "physical stock and be orderable — verified live 2026-09-04 that "
               "this suite's throwaway materials (DSW* family in test_9707) have "
               "no stock and cannot be ordered via the requester wizard, and the "
               "real orderable SKU (DGT15A0666-01) is not a material this suite "
               "may delete. Needs test data where a suite-owned material carries "
               "real WIP.",
        run=False,
        strict=False,
    )
    def test_delete_material_referenced_by_wip_or_open_task(self, processing_area):
        """
        ID     : TC_MAT_003
        Title  : Deleting a Material referenced by WIP or an open task
        Reason : In-flight task whose material was deleted becomes stuck.
        """
```

### 17. TC_CON_003 — A container cannot be assigned to two locations at once

Former source: `tests/ui/admin/processing_area/test_04_material_container_validation.py` → `test_container_cannot_be_in_two_locations_at_once`.

Previous status: Expected failure, not executed (xfail run=False). Current status: deferred.

```python
    @allure.title("TC_CON_003 — A container cannot be assigned to two locations at once")
    @pytest.mark.xfail(
        reason="Container location is set only by WIP / task assignment, and "
               "there is no admin UI to place a container into two locations to "
               "test the guard (WIP tab is read-only — re-verified live "
               "2026-09-04). Same blocker as TC_MAT_003: no suite-owned entity "
               "can be driven into task state. Needs a task-placing fixture "
               "against real-stock data.",
        run=False,
        strict=False,
    )
    def test_container_cannot_be_in_two_locations_at_once(self, processing_area):
        """
        ID     : TC_CON_003
        Title  : A container cannot be assigned to two locations at once
        """
```

## WIP portions removed from shared checks

| Shared check | Restore in the next version | Current retained coverage |
|---|---|---|
| Admin `TC_PA_TAB_ALL` | Include WIP Inventory in the visible tab list | Other six tabs |
| Supervisor `TC_SUP_SHELL_001` | Assert WIP navigation entry presence | Other navigation entries; WIP label excluded from comparison |
| Supervisor `TC_SUP_SHELL_002` | Open WIP and assert `/opsinventory` route | Staging Area and Auto Trips routes |
| Supervisor `TC-038` | Include WIP entry in navigation scope assertion | Role, assigned areas, and other navigation entries |
| Notifications `TC-006/TC-007` | Compare notification feed on Staging Area and WIP | Compare Staging Area and Auto Trips |

## Scope retained in the current suite

Requester stock selection/quantity validation, request submission, dispatch,
Fleet Manager trip verification, staging-area management, and Auto Trips tests
remain. Using stock as a prerequisite does not make these WIP dashboard tests.
WIP page-object helpers and configuration values remain available for restoration;
they do not collect or execute tests by themselves.

## Reintroduction checklist

1. Confirm the released WIP requirements and prepare deterministic inventory data.
2. Implement the deferred cases using current page objects; replace historical
   placeholders and weak/volatile assertions rather than copying blindly.
3. Restore the WIP portions of shared checks and verify unrelated coverage remains.
4. Run collection, isolated WIP tests, and the combined role suites.
5. Update coverage documentation with actual results, including skips and blockers.
