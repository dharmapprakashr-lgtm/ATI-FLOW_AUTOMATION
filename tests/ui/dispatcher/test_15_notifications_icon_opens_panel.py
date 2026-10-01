"""Dispatcher - Notifications (left sidebar).

Verified live 2026-08-28: clicking the "Notifications" row in the sidebar
(#operator-sidebar-notif-row) opens a slide-in panel headed "Notifications"
with a count badge, one card per alert (title chip + time + body, e.g.
"MES Unreachable ... Check network or MES service.") and a "Clear all" button
at the foot.
"""

import allure
import pytest

from pages.dashboards.dispatcher_dashboard_page import DispatcherHomePage

pytestmark = [pytest.mark.dispatcher, pytest.mark.smoke]


@allure.title("The Notifications sidebar item opens a panel of recent alerts")
def test_notifications_icon_opens_panel(dispatcher_page):
    home = DispatcherHomePage(dispatcher_page)

    with allure.step("Panel is not open initially"):
        assert not dispatcher_page.get_by_role("button", name="Clear all").is_visible()

    with allure.step("Click the Notifications row"):
        home.open_notifications()

    with allure.step("A panel headed 'Notifications' with a 'Clear all' action appears"):
        panel_text = home.notifications_panel_text()
        assert "Notifications" in panel_text, f"Panel text was: {panel_text!r}"
        assert dispatcher_page.get_by_role("button", name="Clear all").is_visible(), (
            "Expected a 'Clear all' button in the notifications panel"
        )
