"""Fleet Manager - login, fleet ("Map") switch, and the Manage Trips grid.

A completely separate application from AtiFlow (different host: 192.168.6.12,
own login) - AtiFlow only ever talks to it indirectly (a Dispatcher's
"Dispatch" click tasks a real AMR through it). This page object exists solely
so tests/ui/e2e/test_full_workflow_admin_to_supervisor.py can prove that a
dispatch really did create a trip, not just that the AtiFlow UI stopped
showing "Dispatch".

DOM confirmed live 2026-08-28 (config.fm_base_url = https://192.168.6.12/fm):

- Login: plain inputs, `#login-user-name` / `#login-password`, a "Log In"
  button. Lands on `/fm/dashboard`.
- The fleet/"Map" switcher (top-left, `#fleets_menu`) is an MUI Autocomplete.
  Picking a different one raises a confirmation dialog ("Are you sure you
  want to change the Fleet?") with a "Yes" button that must be clicked too.
- A **recurring** connectivity alert ("Lost connection to pivot-scrapyard,
  sherpa doing trip: NNN", `#alertModalDialog`) pops up unpredictably and
  its backdrop covers the *entire* viewport (blocks clicks anywhere, not
  just near the box) until dismissed. It has nothing to do with our trip and
  must be swallowed before/around every interaction - `dismiss_error_alerts`
  is called defensively throughout this page object.
- "Manage trips" (bottom nav) -> `/fm/manage-trips`, defaulting to the
  "Active" tab. The grid is an MUI X DataGrid (`role="row"`/`.MuiDataGrid-row`,
  no real `<table>`), one `.MuiDataGrid-cell[data-field=...]` per column:
  `id` (Trip ID), `booking_id`, `sherpa_name`, `route`, `booking_time`,
  `start_time`, `end_time`, `route_progress`, `status`, `Actions`.
- A row's `route` cell reads e.g. "auto2_gg >... AH_stage_B1Show all" - the
  literal text has no space before the "Show all" link, and a leg that ends
  at the shared staging area resolves to a specific cell at trip-creation
  time (AH_stage_A1/B1/C1/...), not the bare "AH_stage" name from
  config/test_data.toml's workflow specs. `route_matches` accounts for that
  with a prefix check on "AH_stage" and an exact match on every other
  station id.
"""

from datetime import datetime

from config.environment import config


class FleetManagerPage:
    def __init__(self, page):
        self.page = page

        # Login
        self.username_input = page.locator("#login-user-name")
        self.password_input = page.locator("#login-password")
        self.login_button = page.get_by_role("button", name="Log In")

        # Chrome
        self.fleet_select = page.locator("#fleets_menu")
        self.manage_trips_nav = page.get_by_text("Manage trips", exact=True)

    # ── Login / navigation ───────────────────────────────────────────────────

    def login(self, username=None, password=None):
        self.page.goto(config.fm_base_url, wait_until="domcontentloaded", timeout=30000)
        self.page.wait_for_timeout(1000)
        self.username_input.fill(username or config.fm_user)
        self.password_input.fill(password or config.fm_pass)
        self.login_button.click()
        self.page.wait_for_load_state("networkidle", timeout=30000)
        self.page.wait_for_timeout(1500)
        self.dismiss_error_alerts()

    def dismiss_error_alerts(self, tries=6):
        """Best-effort dismiss of the recurring 'Lost connection ...' alert -
        an unrelated live fleet-health notice whose backdrop otherwise blocks
        every later click. Scoped by text so the *different*, intentional
        "Are you sure ...?" confirmation dialogs are never touched here."""
        for _ in range(tries):
            dlg = self.page.locator("#alertModalDialog").filter(has_text="Lost connection")
            if dlg.count() and dlg.first.is_visible():
                dlg.first.get_by_role("button", name="OK").click(force=True)
                self.page.wait_for_timeout(400)
            else:
                return

    def select_fleet(self, name):
        """Switch the active fleet/"Map". No-op if already selected. Confirms
        the "Are you sure you want to change the Fleet?" dialog MUI raises."""
        self.dismiss_error_alerts()
        if self.fleet_select.input_value() == name:
            return
        self.fleet_select.click()
        self.page.wait_for_timeout(700)
        self.dismiss_error_alerts()
        listbox = self.page.locator("ul[role='listbox']").first
        listbox.get_by_text(name, exact=True).first.click()
        self.page.wait_for_timeout(600)
        self.dismiss_error_alerts()

        confirm = self.page.get_by_role("button", name="Yes")
        if confirm.count() and confirm.first.is_visible():
            confirm.first.click(force=True)
            self.page.wait_for_timeout(1500)
        self.dismiss_error_alerts()

        assert self.fleet_select.input_value() == name, (
            f"Fleet selector still reads {self.fleet_select.input_value()!r} "
            f"after trying to switch to {name!r}"
        )

    # Manage Trips status tabs. The grid opens on "Active"; a freshly-booked
    # trip that no AMR has picked up yet sits under "Scheduled" (and a very
    # fast one can already be under "Completed"), so a search that only ever
    # reads the default tab misses real trips.
    TRIP_TABS = ("Active", "Scheduled", "Completed")

    def open_manage_trips(self):
        self.dismiss_error_alerts()
        self.manage_trips_nav.first.click(force=True)
        self.page.wait_for_load_state("networkidle", timeout=20000)
        self.page.wait_for_timeout(1500)
        self.dismiss_error_alerts()

    # ── Manage Trips grid (read-only) ────────────────────────────────────────

    def _select_trip_tab(self, name):
        """Switch the Manage Trips status tab. Best-effort: returns True if the
        tab was found and clicked, False if this build has no such tab."""
        self.dismiss_error_alerts()
        tab = self.page.get_by_role("tab", name=name, exact=True)
        if not tab.count():
            tab = self.page.get_by_role("button", name=name, exact=True)
        if not tab.count():
            tab = self.page.locator("[role='tab'], .MuiTab-root").filter(has_text=name)
        if not tab.count():
            return False
        try:
            tab.first.click(force=True)
            self.page.wait_for_timeout(1200)
            self.dismiss_error_alerts()
            return True
        except Exception:
            return False

    def _read_rows(self):
        """Read every row of the MUI X DataGrid on the current tab.

        The grid virtualises: only the rows near the viewport are in the DOM at
        any moment. Scroll the virtual scroller top-to-bottom, collecting rows
        by their data-id, so a match that is not in the first screenful is
        still seen.
        """
        self.dismiss_error_alerts()
        scroller = self.page.locator(".MuiDataGrid-virtualScroller").first
        seen = {}

        def harvest():
            rows = self.page.locator(".MuiDataGrid-row")
            for i in range(rows.count()):
                row = rows.nth(i)
                key = row.get_attribute("data-id") or f"idx-{len(seen)}-{i}"
                if key in seen:
                    continue
                cells = row.locator(".MuiDataGrid-cell")
                data = {}
                for j in range(cells.count()):
                    field = cells.nth(j).get_attribute("data-field")
                    data[field] = cells.nth(j).inner_text().strip()
                seen[key] = data

        harvest()
        if scroller.count():
            last_top = -1
            for _ in range(20):
                try:
                    top = scroller.evaluate(
                        "el => { el.scrollTop += el.clientHeight; return el.scrollTop; }"
                    )
                except Exception:
                    break
                self.page.wait_for_timeout(200)
                harvest()
                if top == last_top:      # hit the bottom
                    break
                last_top = top
        return list(seen.values())

    @staticmethod
    def _station_matches(actual, expected):
        """"AH_stage" resolves to a specific cell at trip-creation time
        (e.g. "AH_stage_B1"), so it gets a prefix match; every other real
        station id must match exactly."""
        if expected == "AH_stage":
            return actual.startswith("AH_stage")
        return actual == expected

    def route_matches(self, route_text, pickup_station, drop_station):
        """True when a row's ``route`` cell runs pickup -> drop.

        The cell separates the two ends with ``>...`` on a truncated multi-leg
        route (with a trailing "Show all"), but a short/direct route can render
        ``A > B``, ``A -> B``, ``A → B`` or just ``A   B``. Accept them all.
        """
        clean = route_text.replace("Show all", "").replace("\n", " ").strip()
        if not clean:
            return False
        pickup_part = drop_part = None
        for sep in (">...", "->", "→", "»", ">", "...", "…"):
            if sep in clean:
                pickup_part, _, drop_part = clean.partition(sep)
                break
        if pickup_part is None:
            parts = clean.split()
            if len(parts) < 2:
                return False
            pickup_part, drop_part = parts[0], parts[-1]
        return self._station_matches(
            pickup_part.strip(), pickup_station
        ) and self._station_matches(drop_part.strip(), drop_station)

    @staticmethod
    def booking_time(row):
        """Parse a row's `booking_time` cell to a datetime, or None. Accepts
        "25-Aug-2026 16:30:15" and a few near variants seen live."""
        raw = (row.get("booking_time") or "").strip()
        for fmt in ("%d-%b-%Y %H:%M:%S", "%d-%b-%Y %H:%M", "%d/%m/%Y %H:%M:%S",
                    "%Y-%m-%d %H:%M:%S", "%d-%b-%Y %I:%M:%S %p"):
            try:
                return datetime.strptime(raw, fmt)
            except ValueError:
                continue
        return None

    def find_trip(self, pickup_station, drop_station, since=None,
                  attempts=6, gap_ms=1500, tabs=None):
        """Poll the (already-open) Manage Trips grid for a row whose route
        runs pickup_station -> drop_station, booked at/after ``since``.

        Scans every status tab in ``tabs`` (default: Active, Scheduled,
        Completed) on each attempt. Read-only - never clicks a row or its
        "Cancel" action. Returns the row dict, or None if nothing matched
        within the budget, after printing every distinct row it saw.
        """
        tabs = tabs or self.TRIP_TABS
        scanned = {}
        for _ in range(attempts):
            for tab in tabs:
                self._select_trip_tab(tab)
                for row in self._read_rows():
                    scanned[(tab, row.get("id"), row.get("booking_time"))] = (tab, row)
                    if not self.route_matches(row.get("route", ""), pickup_station, drop_station):
                        continue
                    if since is None:
                        return row
                    booked_at = self.booking_time(row)
                    if booked_at is None or booked_at >= since:
                        return row
            self.page.wait_for_timeout(gap_ms)

        print(
            f"\n[find_trip] NO match for {pickup_station} -> {drop_station} "
            f"since {since:%d-%b-%Y %H:%M:%S}. Distinct rows seen:"
            if since else
            f"\n[find_trip] NO match for {pickup_station} -> {drop_station}. Rows seen:"
        )
        for tab, row in scanned.values():
            print(f"  [{tab:9}] id={row.get('id')!r} status={row.get('status')!r} "
                  f"booked={row.get('booking_time')!r} route={row.get('route')!r}")
        if not scanned:
            print("  (grid was empty on every tab)")
        return None
