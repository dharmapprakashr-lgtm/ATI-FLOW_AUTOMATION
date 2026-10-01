"""Isolated machine API data shared by API and browser consistency tests."""
import os
from pathlib import Path
from uuid import uuid4

import requests

from config.environment import ROOT_DIR, config

BASE = '/mts/processing-area-machines/'
AREA_BASE = '/mts/processing-area/'
ID = 'id_processing_area_machines'


def check(response, expected=200):
    allowed = (expected,) if isinstance(expected, int) else expected
    assert response.status_code in allowed, (
        f'{response.request.method} {response.request.path_url}: '
        f'expected {allowed}, got {response.status_code}: {response.text[:1500]}'
    )
    return response


def rows(response):
    data = check(response).json()
    assert isinstance(data, list), f'Expected a list, got {type(data).__name__}'
    assert all(isinstance(row, dict) for row in data), data
    return data


def assert_machine(data, expected=None):
    assert isinstance(data, dict), data
    assert {ID, 'processing_area_id', 'machine_name', 'point_type'} <= data.keys(), data
    assert type(data[ID]) is int and data[ID] > 0, data
    assert type(data['processing_area_id']) is int, data
    assert isinstance(data['machine_name'], str), data
    assert data['point_type'] in ('production_type', 'consumption_type'), data
    for field, value in (expected or {}).items():
        assert data[field] == value, f'{field}: expected {value!r}, got {data[field]!r}'
    return data


class MachineAPI:
    def __init__(self, token=None, base_url=None):
        self.base_url = (base_url or os.getenv('MTS_BASE_URL') or config.app_url).removesuffix('/login').rstrip('/')
        token = token or os.getenv('MTS_TOKEN') or os.getenv('API_BEARER_TOKEN', '')
        if not token:
            explicit = os.getenv('MTS_TOKEN_FILE')
            paths = [Path(explicit)] if explicit else [ROOT_DIR / '.mts_token', ROOT_DIR / 'tests/api/.mts_token']
            token = next((p.read_text().strip() for p in paths if p.is_file()), '')
        if not token.strip():
            raise RuntimeError('API setup requires MTS_TOKEN, API_BEARER_TOKEN, or MTS_TOKEN_FILE')
        token = token.strip()
        self.session = requests.Session()
        self.session.verify = not config.ignore_https_errors
        self.session.headers.update(Authorization=token if token.lower().startswith('bearer ') else f'Bearer {token}')
        self.areas = []
        self.machine_ids = set()

    def request(self, method, path=BASE, **kwargs):
        response = self.session.request(method, self.base_url + path, timeout=20, **kwargs)
        # Track even unexpectedly accepted negative-test records before assertions.
        if method.upper() == 'POST' and path == BASE and response.ok:
            data = response.json()
            if isinstance(data, dict) and ID in data:
                self.machine_ids.add(data[ID])
        return response

    def area(self):
        payload = dict(processing_area_name=f'AUTO_PAM_{uuid4().hex[:12]}',
                       processing_area_description='Temporary automated API/UI test')
        data = check(self.request('POST', AREA_BASE, json=payload), 201).json()
        self.areas.append(data['id'])
        assert all(data[k] == v for k, v in payload.items()), data
        return data

    def payload(self, area_id=None, **changes):
        if area_id is None:
            area_id = self.areas[0] if self.areas else self.area()['id']
        data = dict(processing_area_id=area_id, machine_name=f'AUTO_MACHINE_{uuid4().hex[:12]}',
                    point_type='production_type')
        data.update(changes)
        return data

    def create(self, payload=None):
        payload = self.payload() if payload is None else payload
        data = check(self.request('POST', json=payload), 201).json()
        return assert_machine(data, payload)

    def get(self, machine_id):
        return self.request('GET', BASE + str(machine_id))

    def by_area(self, area_id):
        return rows(self.request('GET', BASE + f'by-area/{area_id}'))

    def close(self):
        failures = []
        # Try all cleanup actions even if one fails; never touch pre-existing areas.
        actions = [(BASE + str(mid)) for mid in self.machine_ids]
        for area_id in reversed(self.areas):
            actions.extend([BASE + f'by-area/{area_id}', AREA_BASE + str(area_id)])
        try:
            for path in actions:
                try:
                    check(self.request('DELETE', path), (200, 204, 404))
                except (AssertionError, requests.RequestException) as exc:
                    failures.append(str(exc))
        finally:
            self.session.close()
        assert not failures, 'Test data cleanup failed:\n' + '\n'.join(failures)
