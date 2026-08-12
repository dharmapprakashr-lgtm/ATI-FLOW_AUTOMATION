"""
ProcessingAreaConfigPage
------------------------
Covers TC_PA_013 - TC_PA_016.
"""

from playwright.sync_api import Page, expect
from pages.base_page import BasePage


class ProcessingAreaConfigPage(BasePage):
    TABLE_ROW = "[data-testid='pac-row']"
    ADD_BTN = "[data-testid='pac-add-btn']"
    MACHINE_NAME_INPUT = "[data-testid='pac-machine-name']"
    CONSUMPTION_POINT_DROPDOWN = "[data-testid='pac-consumption-point']"
    ADD_POINT_BTN = "[data-testid='pac-add-point']"
    SAVE_BTN = "[data-testid='pac-save']"
    VALIDATION_ERROR = "[data-testid='pac-validation-error']"
    DELETE_ICON = "[data-testid='pac-delete']"
    SEARCH_INPUT = "[data-testid='pac-search']"
    PAGINATION = "[data-testid='pac-pagination']"

    def __init__(self, page: Page, base_url: str):
        super().__init__(page, base_url)

    def open(self, processing_area: str):
        self.goto(f"/processing-area/{processing_area}/config")

    def row_count(self) -> int:
        return self.page.locator(self.TABLE_ROW).count()

    def get_row(self, machine_name: str):
        return self.page.locator(self.TABLE_ROW).filter(has_text=machine_name)

    def add_config(self, machine_name: str, consumption_points: list[str]):
        self.click(self.ADD_BTN)
        self.fill(self.MACHINE_NAME_INPUT, machine_name)
        for point in consumption_points:
            self.select_option(self.CONSUMPTION_POINT_DROPDOWN, point)
            self.click(self.ADD_POINT_BTN)
        self.click(self.SAVE_BTN)

    def attempt_save_without_machine_name(self):
        self.click(self.ADD_BTN)
        self.click(self.SAVE_BTN)

    def assert_validation_error_shown(self):
        expect(self.page.locator(self.VALIDATION_ERROR)).to_be_visible()

    def delete_config(self, machine_name: str, confirm: bool = True):
        self.get_row(machine_name).locator(self.DELETE_ICON).click()
        if confirm:
            self.confirm_dialog()
        else:
            self.cancel_dialog()

    def search(self, area_name: str):
        self.fill(self.SEARCH_INPUT, area_name)

    def assert_row_visible(self, machine_name: str):
        expect(self.get_row(machine_name)).to_be_visible()

    def assert_row_not_present(self, machine_name: str):
        expect(self.get_row(machine_name)).to_have_count(0)
