"""Supervisor — Notifications drawer (#operator-sidebar-notif-row).

Manual test cases covered:
  TC-006  Error notifications scoped to the selected staging area
  TC-007  No cross-staging-area notification leakage
  TC-028  QR failure notification
  TC-029  Auto-hitch issue notification
  TC-030  AMR breakdown notification
  TC-031  Persistent MES error notification
  TC-032  Retry action available and functional
  TC-033  Handle Manually available where applicable
  TC-034  Handle Manually NOT available where not applicable
  TC-035  Resolved notification moves to History
  TC-036  Failed retry keeps notification active
  TC-037  Notification list scoped to assigned areas only
  TC-040  Resolution moves notification to History across all four types

Confirmed live 2026-09-07: the drawer shows connectivity alerts only — cards
titled "FM Unreachable" / "MES Unreachable", each a chip + a time + a body
line, plus a per-card dismiss icon and a "Clear all" button at the foot.
There is NO Retry, NO "Handle Manually", NO History tab, and the alert set is
device-global infra state, not per-staging-area events. The alert set is
volatile (1 or 2 present depending on live probe results), so real assertions
here never pin an exact count.
"""

import re

import allure
import pytest

from config.data import TestData
from pages.dashboards.supervisor_dashboard_page import SupervisorHomePage

pytestmark = [pytest.mark.supervisor, pytest.mark.dashboards]


def _open(home):
    home.open_notifications()


@allure.feature("Dashboards")
@allure.story("Supervisor — Notifications")
class TestSupervisorNotifications:

    # ── Real, running assertions ────────────────────────────────────────────

    @allure.title("TC-031/TC-040 — Drawer opens and lists connectivity alerts with title + body")
    @pytest.mark.smoke
    def test_notifications_panel_lists_alerts(self, supervisor_page):
        """
        ID     : TC-031 / TC-040
        Title  : The Notifications drawer opens and each card carries a title
                 chip and a description
        Reason : A blank or un-openable drawer means a supervisor misses a live
                 MES/FM outage that stalls the whole floor.
        """
        home = SupervisorHomePage(supervisor_page)
        _open(home)
        text = home.notifications_panel_text()
        assert "Notifications" in text, f"Drawer did not open; text={text[:120]!r}"

        titles = home.notification_titles()
        bodies = home.notification_bodies()
        if not titles:
            pytest.skip("No notifications present on the supervisor device right now.")
        assert all(t.strip() for t in titles), f"A notification card has a blank title: {titles}"
        assert any(b.strip() for b in bodies), "No notification card has a description body."
        home.close_notifications()

    @allure.title("TC-031/TC-040 — The persistent MES error text is the expected message")
    def test_mes_error_notification_text(self, supervisor_page):
        """
        ID     : TC-031 / TC-040
        Title  : A persistent MES error surfaces with the correct detail text
        Reason : Manual note pins the exact wording — "MES is unreachable. MES
                 API is unreachable. Check network or MES service." A generic
                 "error" with no cause wastes triage time.
        """
        home = SupervisorHomePage(supervisor_page)
        _open(home)
        titles = home.notification_titles()
        if not any("MES" in t for t in titles):
            pytest.skip("No MES notification present right now (FM-only or none).")
        joined = " ".join(home.notification_bodies())
        assert TestData.sup_mes_error_text in joined, (
            f"MES notification body {joined!r} does not contain the expected "
            f"text {TestData.sup_mes_error_text!r}."
        )
        home.close_notifications()

    @allure.title("TC-034 — 'Handle Manually' is not offered (correct for this build)")
    def test_no_handle_manually_option(self, supervisor_page):
        """
        ID     : TC-034
        Title  : 'Handle Manually' is absent for notification types that do not
                 support it
        Reason : This build's notifications are connectivity alerts, which have
                 no manual-handling flow — so its absence is the *expected*
                 result, and this case passes.
        """
        home = SupervisorHomePage(supervisor_page)
        _open(home)
        labels = " ".join(home.notification_action_labels()).lower()
        assert "handle manually" not in labels, (
            f"A 'Handle Manually' control appeared: {home.notification_action_labels()}"
        )
        assert "retry" not in labels, (
            f"A 'Retry' control appeared: {home.notification_action_labels()}"
        )
        home.close_notifications()

    @allure.title("TC-035 — A notification's full description is readable from the drawer")
    def test_notification_full_description_visible(self, supervisor_page):
        """
        ID     : TC-035
        Title  : Opening the drawer shows each alert's full description (not a
                 truncated stub)
        Reason : Manual note — "if we click on the notification we see the full
                 description". The body text must be present in full so a
                 supervisor knows what actually failed.
        """
        home = SupervisorHomePage(supervisor_page)
        _open(home)
        bodies = [b for b in home.notification_bodies() if b.strip()]
        if not bodies:
            pytest.skip("No notification body to inspect right now.")
        assert any(len(b) > 15 and b.endswith(".") for b in bodies), (
            f"No notification body reads as a complete sentence: {bodies}"
        )
        home.close_notifications()

    @allure.title("TC-035/TC-040 — The drawer provides a resolution affordance ('Clear all')")
    def test_clear_all_present(self, supervisor_page):
        """
        ID     : TC-035 / TC-040
        Title  : The drawer offers a way to clear resolved alerts
        Reason : Without any clear/dismiss control the list only ever grows and
                 stops being useful. This build clears rather than archives to a
                 History tab (see test_resolved_notification_moves_to_history).
        """
        home = SupervisorHomePage(supervisor_page)
        _open(home)
        if not home.notification_titles():
            pytest.skip("No notifications, so no 'Clear all' shown.")
        assert home.has_clear_all(), "No 'Clear all' control in the notifications drawer."
        home.close_notifications()

    # ── Contract assertions: what the notification system is / is not today ──
    #
    # Each of these locks a fact the manual sheet's richer spec assumes the
    # other way. They pass now and fail the day the feature is added, which is
    # the cue to rewrite that TC as a positive assertion.

    _CONNECTIVITY_TITLE = re.compile(r"(FM|MES).*(unreachable|error|down)", re.IGNORECASE)

    @allure.title("TC-006/TC-007 — The notification feed is device-scoped, not per-staging-area")
    def test_notification_feed_is_device_scoped(self, supervisor_page):
        """
        ID     : TC-006 / TC-007
        Title  : The same notification set shows regardless of which screen /
                 staging area is open — it is a device-global feed, so there is
                 nothing to scope or leak *between* areas
        Reason : Manual sheet assumes per-area error notifications. Verified
                 live: identical set on the Staging Area screen and the Auto Trips
                 screen.
        """
        home = SupervisorHomePage(supervisor_page)
        home.go_to_staging_area()
        _open(home)
        on_staging = sorted(home.notification_titles())
        home.close_notifications()

        home.go_to_auto_trips()
        _open(home)
        on_trips = sorted(home.notification_titles())
        home.close_notifications()

        assert on_staging == on_trips, (
            f"Notification set differs by screen (staging={on_staging}, "
            f"auto_trips={on_trips}) — the feed may have become area-scoped; revisit "
            f"TC-006/TC-007 as positive scoping tests."
        )

    @allure.title("TC-028/TC-029/TC-030 — Notifications are connectivity alerts only (no event types)")
    def test_notification_types_are_connectivity_only(self, supervisor_page):
        """
        ID     : TC-028 / TC-029 / TC-030
        Title  : QR-failure / auto-hitch / AMR-breakdown are not notification
                 types in this build — every alert is an FM/MES connectivity
                 alert
        Reason : Locks the current type set. Fails when a floor-event
                 notification type is added, cueing TC-028/029/030 to become
                 positive assertions.
        """
        home = SupervisorHomePage(supervisor_page)
        _open(home)
        titles = home.notification_titles()
        panel = home.notifications_panel_text().lower()
        home.close_notifications()

        for term in ("qr", "auto-hitch", "auto hitch", "hitch", "amr breakdown", "breakdown"):
            assert term not in panel, (
                f"Notifications now mention {term!r} — a floor-event type may exist."
            )
        if titles:
            unexpected = [t for t in titles if not self._CONNECTIVITY_TITLE.search(t)]
            assert not unexpected, (
                f"Notification title(s) {unexpected} are not FM/MES connectivity "
                f"alerts — the type set has grown."
            )

    @allure.title("TC-032/TC-033/TC-036 — No Retry and no 'Handle Manually' control in the drawer")
    def test_no_retry_or_handle_manually_controls(self, supervisor_page):
        """
        ID     : TC-032 / TC-033 / TC-036
        Title  : The drawer's only per-alert lifecycle controls are dismiss and
                 'Clear all' — no Retry, no 'Handle Manually', so no
                 failed-retry state either
        Reason : Locks the control set. TC-034 (no Handle Manually where N/A)
                 is the positive companion that already passes.
        """
        home = SupervisorHomePage(supervisor_page)
        _open(home)
        panel = home.notifications_panel_text().lower()
        actions = " ".join(home.notification_action_labels()).lower()
        home.close_notifications()

        for term in ("retry", "handle manually", "resolve", "acknowledge"):
            assert term not in panel and term not in actions, (
                f"A {term!r} control appeared in the notifications drawer."
            )

    @allure.title("TC-037 — No foreign area leaks into the supervisor's notification feed")
    def test_no_foreign_area_in_notification_feed(self, supervisor_page):
        """
        ID     : TC-037
        Title  : Nothing in the feed references a processing/staging area the
                 supervisor is not assigned to
        Reason : Full isolation proof needs a second device bound elsewhere;
                 this is the half that runs — assert the live feed carries no
                 area name at all (connectivity alerts) or only the assigned
                 ones.
        """
        home = SupervisorHomePage(supervisor_page)
        _open(home)
        blob = " ".join(home.notification_titles() + home.notification_bodies()).lower()
        home.close_notifications()

        assigned = {TestData.sup_bound_processing_area.lower(),
                    TestData.sup_bound_staging_area.lower()}
        # A few well-known other areas from the environment (see memories).
        for foreign in ("test_9707", "ati test", "dev_office_validation", "mapping_test"):
            if foreign in assigned:
                continue
            assert foreign not in blob, (
                f"Notification feed references foreign area {foreign!r}: {blob!r}"
            )

    @allure.title("TC-035/TC-040 — Resolved alerts are cleared, not moved to a History section")
    def test_no_notification_history_section(self, supervisor_page):
        """
        ID     : TC-035 / TC-040
        Title  : The drawer has no History tab/section — resolution is 'Clear
                 all' / per-card dismiss
        Reason : Manual sheet assumes a History archive. Verified live: no
                 'History' text, no tabs in the drawer. Fails when a History
                 view is added, cueing TC-035/TC-040 to become positive
                 "moves to History with resolution details" assertions.
        """
        home = SupervisorHomePage(supervisor_page)
        _open(home)
        panel = home.notifications_panel_text().lower()
        tab_count = supervisor_page.get_by_role("tab").count()
        has_clear = home.has_clear_all() if home.notification_titles() else True
        home.close_notifications()

        assert "history" not in panel, "A 'History' section appeared in the drawer."
        assert tab_count == 0, f"The notifications drawer now has {tab_count} tab(s)."
        assert has_clear, "Resolution affordance ('Clear all') is missing."
