from __future__ import annotations

from playwright.sync_api import expect


class ContainersPage:
    """Backward-compatible page object for the legacy standalone runner."""

    CONTAINER_TYPES = ["Trolley", "Pallet", "Bin"]

    def __init__(self, page, base_url=None):
        self.page = page
        self.base_url = base_url

    def open(self, area_name: str):
        self.page.get_by_text(area_name, exact=True).first.click(force=True)
        self.page.get_by_role("tab", name="Containers", exact=True).click(force=True)
        self.page.get_by_role("button", name="Add New Container", exact=True).wait_for(state="visible", timeout=15000)

    def open_add_modal(self):
        self.page.get_by_role("button", name="Add New Container", exact=True).click(force=True)
        self.page.locator(".MuiDialog-container").wait_for(state="visible", timeout=10000)

    def select_container_type(self, c_type: str):
        field = self.page.locator("#ctr-type")
        field.click(force=True)
        self.page.get_by_role("option", name=c_type, exact=True).first.click(force=True)

    def fill_subtype(self, value: str):
        self.page.locator("#ctr-sub-type").fill(value)

    def fill_dimensions(self, length: str, width: str, height: str, hitch_length: str):
        self.page.locator("#ctr-length").fill(str(length))
        self.page.locator("#ctr-width").fill(str(width))
        self.page.locator("#ctr-height").fill(str(height))
        self.page.locator("#ctr-hitch-length").fill(str(hitch_length))

    def cancel_modal(self):
        self.page.locator(".MuiDialog-container").get_by_role("button", name="CANCEL", exact=True).click(force=True)

    def attempt_save_missing_mandatory_fields(self):
        self.open_add_modal()
        self.page.locator(".MuiDialog-container").get_by_role("button", name="SAVE", exact=True).click(force=True)

    def assert_validation_blocked(self):
        expect(self.page.locator(".MuiDialog-container")).to_be_visible(timeout=5000)

    def add_container(self, c_type: str, c_subtype: str, length: str, width: str, height: str, hitch_length: str, qty: str = "1"):
        self.open_add_modal()
        self.select_container_type(c_type)
        self.fill_subtype(c_subtype)
        self.fill_dimensions(length, width, height, hitch_length)
        self.page.locator("#ctr-qty").fill(str(qty))
        self.page.locator(".MuiDialog-container").get_by_role("button", name="SAVE", exact=True).click(force=True)

    def add_container_legacy(self, container_type, sub_type, length, width, height, hitch_length, qty=1):
        self.add_container(
            c_type=container_type,
            c_subtype=sub_type,
            length=length,
            width=width,
            height=height,
            hitch_length=hitch_length,
            qty=str(qty),
        )

    def __repr__(self):
        return f"ContainersPage(page={self.page!r})"
