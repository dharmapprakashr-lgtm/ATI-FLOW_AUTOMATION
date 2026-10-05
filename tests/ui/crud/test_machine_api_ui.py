"""Verify machine changes persist across the API and a reloaded admin browser."""
import re

import pytest

from config.data import TestData
from playwright.sync_api import expect

from pages.admin.admin_navigation import AdminDashboardPage
from utils.machine_api import BASE, ID, assert_machine, check

pytestmark = [pytest.mark.admin, pytest.mark.admin_pa, pytest.mark.integration, pytest.mark.crud]


def machine_row(page, name):
    return page.get_by_role('row').filter(has=page.get_by_role('cell', name=name, exact=True))


def refresh(page, area_page):
    page.reload(wait_until='domcontentloaded')
    area_page.go_to_machine_names()


@pytest.mark.parametrize('point_type,label', [
    (TestData.crud_api_production_point_type, TestData.crud_api_production_label),
    (TestData.crud_api_consumption_point_type, TestData.crud_api_consumption_label),
])
def test_ui_create_persists_in_api_and_after_reload(machine_api, machine_ui_area, admin_page, point_type, label):
    area_page, area = machine_ui_area
    payload = machine_api.payload(area['id'], point_type=point_type)
    area_page.add_machine_name(payload['machine_name'], label)
    records = machine_api.by_area(area['id'])
    assert len(records) == 1
    assert_machine(records[0], payload)
    refresh(admin_page, area_page)
    expect(machine_row(admin_page, payload['machine_name'])).to_have_count(1)
    expect(machine_row(admin_page, payload['machine_name'])).to_contain_text(label)


def test_api_create_update_delete_reflected_in_ui(machine_api, machine_ui_area, admin_page):
    area_page, area = machine_ui_area
    machine = machine_api.create(machine_api.payload(area['id']))
    refresh(admin_page, area_page)
    expect(machine_row(admin_page, machine['machine_name'])).to_have_count(1)
    payload = machine_api.payload(area['id'], point_type=TestData.crud_api_consumption_point_type)
    assert_machine(check(machine_api.request('PUT', BASE + str(machine[ID]), json=payload)).json(), payload)
    refresh(admin_page, area_page)
    expect(machine_row(admin_page, machine['machine_name'])).to_have_count(0)
    expect(machine_row(admin_page, payload['machine_name'])).to_have_count(1)
    expect(machine_row(admin_page, payload['machine_name'])).to_contain_text(TestData.crud_api_consumption_label)
    check(machine_api.request('DELETE', BASE + str(machine[ID])), (200, 204))
    refresh(admin_page, area_page)
    expect(machine_row(admin_page, payload['machine_name'])).to_have_count(0)
    check(machine_api.get(machine[ID]), 404)


def test_ui_delete_persists_in_api_and_after_reload(machine_api, machine_ui_area, admin_page):
    area_page, area = machine_ui_area
    machine = machine_api.create(machine_api.payload(area['id']))
    refresh(admin_page, area_page)
    expect(machine_row(admin_page, machine['machine_name'])).to_have_count(1)
    assert AdminDashboardPage(admin_page).delete_device_if_exists(machine['machine_name'])
    check(machine_api.get(machine[ID]), 404)
    refresh(admin_page, area_page)
    expect(machine_row(admin_page, machine['machine_name'])).to_have_count(0)


def test_cancel_creation_does_not_persist(machine_api, machine_ui_area, admin_page):
    area_page, area = machine_ui_area
    payload = machine_api.payload(area['id'])
    admin_page.locator('button').filter(has_text='Add').first.click()
    admin_page.get_by_placeholder('e.g. Machine A').fill(payload['machine_name'])
    admin_page.locator('.MuiDialog-container .MuiSelect-select').first.click()
    admin_page.get_by_role('option', name=TestData.crud_api_production_label, exact=True).click()
    admin_page.get_by_role('button', name=re.compile('^cancel$', re.IGNORECASE)).click()
    expect(admin_page.locator('.MuiDialog-container')).not_to_be_visible()
    assert machine_api.by_area(area['id']) == []
    refresh(admin_page, area_page)
    expect(machine_row(admin_page, payload['machine_name'])).to_have_count(0)


def test_machine_table_is_scoped_to_selected_area(machine_api, machine_ui_area, admin_page):
    area_page, area = machine_ui_area
    first = machine_api.create(machine_api.payload(area['id']))
    other_area = machine_api.area()
    second = machine_api.create(machine_api.payload(other_area['id']))
    refresh(admin_page, area_page)
    expect(machine_row(admin_page, first['machine_name'])).to_have_count(1)
    expect(machine_row(admin_page, second['machine_name'])).to_have_count(0)
    area_page.navigate_to_existing_area(other_area['processing_area_name'])
    area_page.go_to_machine_names()
    expect(machine_row(admin_page, second['machine_name'])).to_have_count(1)
    expect(machine_row(admin_page, first['machine_name'])).to_have_count(0)
