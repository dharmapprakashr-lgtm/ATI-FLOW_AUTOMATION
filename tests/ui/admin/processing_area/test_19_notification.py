"""Admin notification drawer checks based on the shared FM/MES alert UI.

Checks are read-only: individual dismiss and Clear all are never clicked.
Alert-detail cases skip when the corresponding live alert is absent.
"""

import re

import allure
import pytest
from playwright.sync_api import expect

pytestmark = [pytest.mark.admin]


def _open_notifications(page):
    page.get_by_text("Notifications", exact=True).first.click()
    panel = page.locator(
        ".MuiDrawer-paper, .MuiPopover-paper, [role='dialog']"
    ).filter(has=page.get_by_text("Notifications", exact=True)).filter(visible=True).last
    expect(panel).to_be_visible(timeout=10_000)
    expect(panel.get_by_text("Notifications", exact=True)).to_be_visible()
    return panel


def _capture(panel):
    allure.attach(panel.inner_text(), "Admin notifications", allure.attachment_type.TEXT)
    allure.attach(panel.screenshot(), "Admin notification panel", allure.attachment_type.PNG)


@allure.feature("Admin Console")
@allure.story("Notifications")
class TestAdminNotifications:
    @pytest.mark.smoke
    @allure.title("TC_ADMIN_NOTIF_001 — Sidebar Notifications opens the drawer")
    def test_notifications_panel_opens(self, admin_page):
        panel = _open_notifications(admin_page)
        _capture(panel)

    @allure.title("TC_ADMIN_NOTIF_002 — Notifications drawer closes with Escape")
    def test_notifications_panel_closes(self, admin_page):
        panel = _open_notifications(admin_page)
        admin_page.keyboard.press("Escape")
        expect(panel).to_be_hidden(timeout=5_000)
        expect(admin_page.get_by_text("Notifications", exact=True).first).to_be_visible()

    @pytest.mark.xfail(reason="UI bug: notification count badge mismatch with cards/popover")
    @allure.title("TC_ADMIN_NOTIF_003 — Badge count matches the listed notifications")
    def test_notification_count_matches_cards(self, admin_page):
        panel = _open_notifications(admin_page)
        # Read both values in one DOM snapshot to avoid a new alert arriving
        # between separate count and text calls. Timestamps do not match digits.
        snapshot = panel.evaluate("""panel => ({
            count: panel.querySelectorAll('.MuiChip-label').length,
            badges: Array.from(panel.querySelectorAll('*'))
                .filter(el => el.children.length === 0 && el.getClientRects().length)
                .map(el => el.textContent.trim())
                .filter(text => /^\\d+\\+?$/.test(text))
        })""")
        _capture(panel)
        badges = snapshot['badges']
        count = snapshot['count']
        if count == 0 and not badges:
            # MUI may hide a zero badge; ensure this is an actual empty state.
            expect(panel.get_by_text(re.compile(r"no notifications|all caught up", re.I))).to_be_visible()
            return
        assert len(badges) == 1, f"Expected one notification count badge: {snapshot}"
        badge = badges[0]
        expected = int(badge.rstrip('+'))
        assert (count > expected if badge.endswith('+') else count == expected), (
            f"Notification badge {badge!r} does not match {count} listed alerts"
        )

    @pytest.mark.parametrize("service", ["FM", "MES"], ids=["fleet_manager", "mes"])
    @allure.title("TC_ADMIN_NOTIF_004 — {service} unreachable alert includes details and time")
    def test_unreachable_alert_details(self, admin_page, service):
        panel = _open_notifications(admin_page)
        chips = panel.locator('.MuiChip-label').filter(has_text=re.compile(rf"^{service} Unreachable$", re.I))
        _capture(panel)
        if chips.count() == 0:
            pytest.skip(f"No {service} Unreachable notification is currently present")
        expected_body = f"{service} is unreachable. {service} API is unreachable. Check network or {service} service."
        for index in range(chips.count()):
            # Select the nearest card containing the description, not the chip wrapper.
            card = chips.nth(index).locator(
                f"xpath=ancestor::div[.//p[contains(., '{service} is unreachable.')]][1]"
            )
            expect(card).to_be_visible()
            text = re.sub(r"\s+", " ", card.inner_text()).strip()
            assert expected_body in text, f"Incomplete {service} alert: {text!r}"
            assert re.search(r"\b(?:[01]?\d|2[0-3]):[0-5]\d\b", text), (
                f"Missing HH:MM timestamp on {service} alert: {text!r}"
            )

    @allure.title("TC_ADMIN_NOTIF_005 — Clear all is available when notifications exist")
    def test_clear_all_control(self, admin_page):
        panel = _open_notifications(admin_page)
        if panel.locator('.MuiChip-label').count() == 0:
            pytest.skip("No notifications present; Clear all may be hidden or disabled")
        clear_all = panel.get_by_role("button", name="Clear all", exact=True)
        expect(clear_all).to_be_visible()
        expect(clear_all).to_be_enabled()
        _capture(panel)
