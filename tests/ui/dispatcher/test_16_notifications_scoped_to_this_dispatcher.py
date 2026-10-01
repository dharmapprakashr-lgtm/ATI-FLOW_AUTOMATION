"""Dispatcher - Notifications scoping.

The scaffold's ideal - "prove the feed contains only alerts for this
dispatcher's bound stations/devices and nothing global" - can't be asserted
from a single logged-in device (there is no second device here to diff
against, and some alerts, e.g. "MES Unreachable", are legitimately
system-wide).

What IS verifiable, and what this test checks: the feed is tied to the
**dispatcher device**, not to whichever station is currently selected in the
sidebar. Switching the bound-station scope must not change the notification
list. Verified live 2026-08-28: the panel showed the same alert before and
after switching from auto2_gg to auto1_gg.
"""

import re

import allure
import pytest

from config.data import TestData
from pages.dashboards.dispatcher_dashboard_page import DispatcherHomePage

pytestmark = [pytest.mark.dispatcher, pytest.mark.smoke]

_NOISE = re.compile(r"^\d+$|^\d{1,2}:\d{2}$|ago$")


def _notification_lines(home):
    """Meaningful lines of the panel - alert titles and bodies, with the
    heading, the 'Clear all' action, badge counts and timestamps filtered
    out so the comparison is about *which alerts* are shown, not their
    (drifting) relative times."""
    lines = []
    for raw in home.notifications_panel_text().splitlines():
        ln = raw.strip()
        if not ln or ln in ("Clear all", "Notifications") or _NOISE.search(ln):
            continue
        lines.append(ln)
    return lines


@allure.title("Notifications are scoped to the device, not the selected station")
def test_notifications_scoped_to_this_dispatcher(dispatcher_page):
    home = DispatcherHomePage(dispatcher_page)

    with allure.step("Read the feed on the default station"):
        home.open_notifications()
        before = _notification_lines(home)
        home.close_notifications()

    if not before:  # no alert cards in the feed
        pytest.skip("No notifications in the feed right now - nothing to scope-check.")

    with allure.step(f"Switch to {TestData.disp_req_alt_station} and re-read the feed"):
        home.select_station(TestData.disp_req_alt_station)
        home.open_notifications()
        after = _notification_lines(home)
        home.close_notifications()

    with allure.step("The feed is unchanged by the station switch (device-scoped)"):
        assert after == before, (
            f"Notification feed changed when the station changed:\n"
            f"  before: {before}\n  after:  {after}"
        )

    home.select_station(TestData.disp_req_default_station)
