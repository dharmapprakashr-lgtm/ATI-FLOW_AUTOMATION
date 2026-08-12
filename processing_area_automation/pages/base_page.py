"""
BasePage
--------
Common helpers shared by every page object. Keep locator strategy and
generic waits here so individual page objects stay focused on their
own screen's elements.
"""

from playwright.sync_api import Page, expect


class BasePage:
    def __init__(self, page: Page, base_url: str):
        self.page = page
        self.base_url = base_url.rstrip("/")

    def goto(self, path: str = ""):
        self.page.goto(f"{self.base_url}{path}")

    def click(self, selector: str):
        self.page.locator(selector).click()

    def fill(self, selector: str, value: str):
        self.page.locator(selector).fill(value)

    def select_option(self, selector: str, value: str):
        self.page.locator(selector).select_option(value)

    def is_visible(self, selector: str) -> bool:
        return self.page.locator(selector).is_visible()

    def text_of(self, selector: str) -> str:
        return self.page.locator(selector).inner_text()

    def wait_for_toast(self, expected_text: str = None, timeout: int = 5000):
        toast = self.page.locator("[data-testid='toast']")
        expect(toast).to_be_visible(timeout=timeout)
        if expected_text:
            expect(toast).to_contain_text(expected_text)

    def confirm_dialog(self, confirm_selector: str = "[data-testid='confirm-btn']"):
        self.page.locator(confirm_selector).click()

    def cancel_dialog(self, cancel_selector: str = "[data-testid='cancel-btn']"):
        self.page.locator(cancel_selector).click()
