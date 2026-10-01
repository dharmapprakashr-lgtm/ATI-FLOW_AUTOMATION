"""Requester dashboard resilience, state rendering and timestamp contracts.

Only history GET responses are intercepted. No orders are submitted or changed.
Recovery is verified by reopening history after restoring network access; this
is not a claim that the product supports automatic websocket reconnection.
"""

from datetime import datetime
import os
import re
from zoneinfo import ZoneInfo

import allure
import pytest
from playwright.sync_api import expect

from pages.dashboards.requester_dashboard_page import RequesterHomePage

pytestmark = [pytest.mark.dashboards]
HISTORY = '**/mts/requester/requests_history/**'


def _record(identifier, created='2026-09-25T20:45:00Z'):
    return dict(request_id=identifier, requester_id='dashboard_contract_test',
                requested_quantity=[1], request_created_at=created,
                request_status='Cancelled', requested_component_id=['TEST_COMPONENT'],
                requested_component_type=['TEST_MATERIAL'], last_updated_at=created,
                MHE=[], workflow='TEST_WORKFLOW', request_machine='TEST_MACHINE',
                is_empty_container=False, empty_container_material_type='',
                empty_container_type='Trolley', request_material_route=[],
                request_container_route=None)


def _reply(route, records):
    import json
    route.fulfill(status=200, content_type='application/json', body=json.dumps(
        dict(total=len(records), page=1, page_size=10, data=records)))


def _history(page):
    home = RequesterHomePage(page)
    home.staging_area_nav.click()
    home.request_history_nav.click()
    expect(home.make_new_request_btn).to_be_visible(timeout=10000)


def _row(page, identifier):
    return page.locator('tbody tr').filter(
        has=page.get_by_text(f'Req-{identifier}', exact=True))


@allure.feature('Dashboards')
@allure.story('Common: network resilience')
class TestDashboardNetworkResilience:
    @allure.title('TC_DASH_ALL_001 — History recovers after an interrupted request and reopening')
    def test_live_updates_survive_network_interruption(self, requester_page):
        page = requester_page
        state = {'offline': False, 'aborted': 0}
        record = _record(990001)

        def intercept(route):
            if state['offline']:
                state['aborted'] += 1
                route.abort('internetdisconnected')
            else:
                _reply(route, [record])

        page.route(HISTORY, intercept)
        try:
            _history(page)
            expect(_row(page, 990001)).to_be_visible(timeout=10000)
            state['offline'] = True
            with page.expect_event('requestfailed', predicate=lambda r: '/mts/requester/requests_history/' in r.url):
                _history(page)
            assert state['aborted'] > 0, 'No history request was interrupted'
            expect(page.locator('#operator-sidebar-nav')).to_be_visible()
            state['offline'] = False
            record = _record(990002)
            _history(page)
            expect(_row(page, 990002)).to_be_visible(timeout=10000)
            expect(_row(page, 990001)).to_have_count(0)
        finally:
            page.unroute(HISTORY, intercept)


@allure.feature('Dashboards')
@allure.story('Common: state rendering')
class TestDashboardStateRendering:
    @allure.title('TC_DASH_ALL_002 — History shows loading, empty and request-error states')
    def test_empty_loading_and_error_states_render_correctly(self, requester_page):
        page = requester_page
        state = {'mode': 'loading'}
        pending = []

        def intercept(route):
            if state['mode'] == 'loading':
                pending.append(route)
            elif state['mode'] == 'error':
                route.fulfill(status=500, content_type='application/json',
                              body='{"detail":"Dashboard contract test: history unavailable"}')
            else:
                _reply(route, [])

        page.route(HISTORY, intercept)
        try:
            _history(page)
            loading = page.locator('[role="progressbar"], .MuiSkeleton-root').or_(
                page.get_by_text(re.compile(r'loading', re.I)))
            expect(loading.filter(visible=True).first).to_be_visible(timeout=10000)
            assert pending, 'No history request was held for the loading check'
            state['mode'] = 'empty'
            while pending:
                _reply(pending.pop(), [])
            expect(page.get_by_text(re.compile(r'no requests|no history|no records', re.I)).first).to_be_visible(timeout=10000)
            expect(loading.filter(visible=True)).to_have_count(0)
            state['mode'] = 'error'
            with page.expect_response(lambda r: '/mts/requester/requests_history/' in r.url and r.status == 500):
                _history(page)
            error = page.locator('[role="alert"], [data-sonner-toast], .Toastify__toast--error, .MuiAlert-standardError').filter(
                has_text=re.compile(r'error|failed|unable|unavailable|retry|try again', re.I))
            expect(
                error.filter(visible=True).first,
                'A failed history request must display an error, not an empty queue',
            ).to_be_visible(timeout=10000)
            expect(page.locator('#operator-sidebar-nav')).to_be_visible()
        finally:
            state['mode'] = 'empty'
            while pending:
                _reply(pending.pop(), [])
            page.unroute(HISTORY, intercept)


@allure.feature('Dashboards')
@allure.story('Common: timestamp format')
class TestDashboardTimestamps:
    @allure.title('TC_DASH_ALL_003 — UTC history timestamps render in the expected local timezone')
    def test_timestamps_use_correct_timezone_and_format(self, requester_page):
        page = requester_page
        zone = ZoneInfo(os.getenv('DASHBOARD_TIMEZONE', 'Asia/Kolkata'))
        records = [_record(990003), _record(990004, '2026-09-26T06:35:00Z')]
        def intercept(route):
            _reply(route, records)
        page.route(HISTORY, intercept)
        try:
            _history(page)
            for record in records:
                row = _row(page, record['request_id'])
                expect(row).to_be_visible(timeout=10000)
                expected = datetime.fromisoformat(record['request_created_at'].replace('Z','+00:00')).astimezone(zone)
                cell = row.locator('td').nth(2)
                expect(cell).to_contain_text(expected.strftime('%I:%M %p').lower())
                expect(cell).to_contain_text(expected.strftime('%m/%d/%y'))
                allure.attach(cell.inner_text(), f'Timestamp {record["request_id"]} ({zone.key})', allure.attachment_type.TEXT)
        finally:
            page.unroute(HISTORY, intercept)
