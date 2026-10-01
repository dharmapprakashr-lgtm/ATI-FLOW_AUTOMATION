from __future__ import annotations

from playwright.sync_api import expect


class StagingAreaPage:
    """Backward-compatible page object for the legacy standalone runner.

    The repo no longer ships dedicated modules for this class name, but the
    standalone runner still imports it. This shim keeps that import path alive
    and exposes the methods the legacy script expects using the current live
    selectors already confirmed in the project.
    """

    CELL_STATE_SELECT_ID = "#manage-dialog-cell-state-select"

    def __init__(self, page, base_url=None):
        self.page = page
        self.base_url = base_url

    def open(self, area_name: str):
        """Open the named processing area and the Staging Area sub-tab."""
        self.page.get_by_text(area_name, exact=True).first.click(force=True)
        self.page.get_by_role("tab", name="Staging Area", exact=True).click(force=True)
        self.page.locator("#staging-area-view-grid-inner").wait_for(state="visible", timeout=15000)

    def get_card(self, name: str):
        return self.page.get_by_text(name, exact=True).first

    def open_grid(self, name: str):
        self.open(name)
        grid = self.page.locator("#staging-area-view-grid-inner")
        grid.wait_for(state="visible", timeout=15000)
        return grid

    def switch_to_view_mode(self):
        self.page.locator("#staging-area-view-mode-view-btn").click(force=True)

    def switch_to_manage_mode(self):
        self.page.locator("#staging-area-view-mode-manage-btn").click(force=True)

    def click_cell(self, index: int):
        cells = self.page.locator("#staging-area-view-grid-inner div:has(> div[color]):not([disabled])")
        cell = cells.nth(index)
        cell.click(force=True)
        self.page.locator("#manage-cell-dialog-content").wait_for(state="visible", timeout=10000)

    def trolley_option_visible(self):
        option = self.page.get_by_role("option", name="Trolley", exact=True)
        return option.count() > 0 and option.first.is_visible()

    def set_cell_status(self, new_state: str):
        select = self.page.locator(self.CELL_STATE_SELECT_ID)
        select.click(force=True)
        self.page.get_by_role("option", name=new_state, exact=True).first.click(force=True)

    def fill_material(self, category: str, code: str, mhe_number: str):
        self.page.locator("#manage-cell-dialog-filled-with-select").click(force=True)
        self.page.get_by_role("option", name="Material", exact=True).click(force=True)
        self.page.locator("#manage-cell-dialog-sku-autocomplete").fill(code)
        self.page.wait_for_timeout(300)
        self.page.locator("#manage-cell-dialog-mhe-number-autocomplete").fill(mhe_number)
        self.page.locator("#manage-cell-dialog-quantity-input").fill("1")

    def save(self):
        self.page.locator("#manage-cell-dialog-save-btn").click(force=True)

    def cancel(self):
        self.page.locator("#manage-cell-dialog-cancel-btn").click(force=True)

    def close_panel(self):
        self.page.get_by_role("button", name="Close", exact=True).click(force=True)

    def close_details_dialog(self):
        self.close_panel()

    def view_cell_details(self):
        return {
            "cell_location": self.page.get_by_text("Cell Location", exact=True).first,
            "sku": self.page.get_by_text("SKU", exact=True).first,
            "sub_sku": self.page.get_by_text("Sub-SKU", exact=True).first,
            "quantity": self.page.get_by_text("Qty", exact=True).first,
        }

    def __repr__(self):
        return f"StagingAreaPage(page={self.page!r})"
