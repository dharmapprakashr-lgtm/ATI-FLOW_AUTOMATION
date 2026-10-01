"""Machine contracts: independent owned data, exact values, persistence and isolation."""
from urllib.parse import quote

import pytest

from utils.machine_api import BASE, ID, assert_machine, check, rows

pytestmark = pytest.mark.api


@pytest.fixture
def machine(machine_api):
    return machine_api.create()


def test_pam_get_001(machine_api):
    check(machine_api.request('GET'))


def test_pam_get_002(machine_api, machine):
    result = rows(machine_api.request('GET'))
    found = [r for r in result if r[ID] == machine[ID]]
    assert len(found) == 1
    assert_machine(found[0], machine)


def test_pam_get_003(machine_api, machine):
    for row in rows(machine_api.request('GET')):
        assert_machine(row)


def test_pam_post_001(machine_api):
    data = machine_api.create()
    assert_machine(check(machine_api.get(data[ID])).json(), data)


def test_pam_post_002(machine_api, machine):
    payload = {k: v for k, v in machine.items() if k != ID}
    check(machine_api.request('POST', json=payload), (400, 409, 422))
    assert machine_api.by_area(machine['processing_area_id']) == [machine]


@pytest.mark.parametrize('field', ['machine_name', 'processing_area_id', 'point_type'])
def test_pam_post_003(machine_api, field):
    payload = machine_api.payload()
    del payload[field]
    check(machine_api.request('POST', json=payload), 422)
    assert machine_api.by_area(machine_api.areas[0]) == []


def test_pam_post_004(machine_api):
    check(machine_api.request('POST', json=machine_api.payload(machine_name='')), 422)
    assert machine_api.by_area(machine_api.areas[0]) == []


def test_pam_post_005(machine_api):
    payload = machine_api.payload()
    payload['processing_area_id'] = 'invalid-integer'
    check(machine_api.request('POST', json=payload), 422)


def test_pam_post_006(machine_api):
    area_id = machine_api.area()['id']
    check(machine_api.request('DELETE', '/mts/processing-area/' + str(area_id)), (200, 204))
    check(machine_api.request('POST', json=machine_api.payload(area_id)), (400, 404, 422))


def paginated(api, page=1, limit=2):
    body = check(api.request('GET', BASE + 'paginated', params={'page': page, 'limit': limit})).json()
    assert isinstance(body, dict) and isinstance(body.get('items'), list), body
    assert body['page'] == page and body['limit'] == limit, body
    assert type(body['total']) is int and body['total'] >= len(body['items']), body
    assert len(body['items']) <= limit, body
    for item in body['items']:
        assert_machine(item)
    return body


def test_pam_page_001(machine_api, machine):
    paginated(machine_api)


def test_pam_page_002(machine_api):
    for _ in range(3):
        machine_api.create()
    assert len(paginated(machine_api, limit=2)['items']) == 2


def test_pam_page_003(machine_api):
    for _ in range(3):
        machine_api.create()
    first = paginated(machine_api, page=1)['items']
    second = paginated(machine_api, page=2)['items']
    assert first and second
    assert {r[ID] for r in first}.isdisjoint(r[ID] for r in second)


@pytest.mark.parametrize('params', [{'page': 'abc'}, {'page': 0}, {'limit': -1}, {'limit': 0}])
def test_pam_page_004(machine_api, params):
    check(machine_api.request('GET', BASE + 'paginated', params=params), (400, 422))


def test_pam_area_001(machine_api, machine):
    assert machine_api.by_area(machine['processing_area_id']) == [machine]


def test_pam_area_002(machine_api, machine):
    other = machine_api.create(machine_api.payload(machine_api.area()['id']))
    assert machine_api.by_area(machine['processing_area_id']) == [machine]
    assert machine_api.by_area(other['processing_area_id']) == [other]


def test_pam_area_003(machine_api):
    assert machine_api.by_area(machine_api.area()['id']) == []


def test_pam_area_004(machine_api):
    check(machine_api.request('GET', BASE + 'by-area/abc'), 422)


def test_pam_del_area_001(machine_api, machine):
    second = machine_api.create()
    other = machine_api.create(machine_api.payload(machine_api.area()['id']))
    check(machine_api.request('DELETE', BASE + f"by-area/{machine['processing_area_id']}"), (200, 204))
    for removed in (machine, second):
        check(machine_api.get(removed[ID]), 404)
    assert_machine(check(machine_api.get(other[ID])).json(), other)


def test_pam_del_area_002(machine_api, machine):
    check(machine_api.request('DELETE', BASE + f"by-area/{machine['processing_area_id']}"), (200, 204))
    assert machine_api.by_area(machine['processing_area_id']) == []


def test_pam_del_area_003(machine_api):
    area_id = machine_api.area()['id']
    check(machine_api.request('DELETE', BASE + f'by-area/{area_id}'), (200, 204))
    check(machine_api.request('DELETE', BASE + f'by-area/{area_id}'), (200, 204))


def test_pam_del_area_004(machine_api):
    check(machine_api.request('DELETE', BASE + 'by-area/abc'), 422)


@pytest.mark.parametrize('point_type', ['production_type', 'consumption_type'])
def test_pam_point_001(machine_api, point_type):
    machine = machine_api.create(machine_api.payload(point_type=point_type))
    result = rows(machine_api.request('GET', BASE + f'by-point-type/{point_type}'))
    assert machine in result
    assert all(r['point_type'] == point_type for r in result)


def test_pam_point_002(machine_api):
    production = machine_api.create()
    consumption = machine_api.create(machine_api.payload(point_type='consumption_type'))
    result = rows(machine_api.request('GET', BASE + 'by-point-type/production_type'))
    assert production in result and consumption not in result


def test_pam_point_003(machine_api):
    assert rows(machine_api.request('GET', BASE + 'by-point-type/nonexistent-point-type')) == []


def named_areas(api, name):
    return rows(api.request('GET', BASE + 'by-machine-name/' + quote(name, safe='')))


def test_pam_name_001(machine_api, machine):
    result = named_areas(machine_api, machine['machine_name'])
    assert len(result) == 1 and result[0]['processing_area_id'] == machine['processing_area_id']


def test_pam_name_002(machine_api):
    absent = 'absent_' + machine_api.payload()['machine_name']
    check(machine_api.request('GET', BASE + 'by-machine-name/' + absent), 404)


def test_pam_name_003(machine_api, machine):
    other = machine_api.create(machine_api.payload(machine_api.area()['id']))
    result = named_areas(machine_api, machine['machine_name'])
    assert {r['processing_area_id'] for r in result} == {machine['processing_area_id']}
    assert other['processing_area_id'] not in {r['processing_area_id'] for r in result}


def test_pam_name_004(machine_api):
    payload = machine_api.payload()
    payload['machine_name'] += ' space name'
    machine = machine_api.create(payload)
    assert {r['processing_area_id'] for r in named_areas(machine_api, machine['machine_name'])} == {machine['processing_area_id']}


def test_pam_id_001(machine_api, machine):
    assert_machine(check(machine_api.get(machine[ID])).json(), machine)


def test_pam_id_002(machine_api, machine):
    check(machine_api.request('DELETE', BASE + str(machine[ID])), (200, 204))
    check(machine_api.get(machine[ID]), 404)


def test_pam_id_003(machine_api):
    check(machine_api.get('abc'), 422)


def update(api, machine):
    payload = api.payload(machine['processing_area_id'], point_type='consumption_type')
    response = check(api.request('PUT', BASE + str(machine[ID]), json=payload))
    return assert_machine(response.json(), {ID: machine[ID], **payload})


def test_pam_put_001(machine_api, machine):
    update(machine_api, machine)


def test_pam_put_002(machine_api, machine):
    updated = update(machine_api, machine)
    assert_machine(check(machine_api.get(machine[ID])).json(), updated)
    assert machine_api.by_area(machine['processing_area_id']) == [updated]
    check(machine_api.request('GET', BASE + 'by-machine-name/' + machine['machine_name']), 404)


def test_pam_put_003(machine_api, machine):
    check(machine_api.request('DELETE', BASE + str(machine[ID])), (200, 204))
    check(machine_api.request('PUT', BASE + str(machine[ID]), json=machine_api.payload()), 404)


def test_pam_put_004(machine_api):
    check(machine_api.request('PUT', BASE + 'abc', json=machine_api.payload()), 422)


def test_pam_put_005(machine_api, machine):
    check(machine_api.request('PUT', BASE + str(machine[ID]), json={}), 422)
    assert_machine(check(machine_api.get(machine[ID])).json(), machine)


def test_pam_invalid_update_preserves_record(machine_api, machine):
    check(machine_api.request('PUT', BASE + str(machine[ID]), json={'processing_area_id': 'abc'}), 422)
    assert_machine(check(machine_api.get(machine[ID])).json(), machine)


def test_pam_del_001(machine_api, machine):
    check(machine_api.request('DELETE', BASE + str(machine[ID])), (200, 204))
    assert machine_api.by_area(machine['processing_area_id']) == []


def test_pam_del_002(machine_api, machine):
    check(machine_api.request('DELETE', BASE + str(machine[ID])), (200, 204))
    check(machine_api.get(machine[ID]), 404)


def test_pam_del_003(machine_api, machine):
    check(machine_api.request('DELETE', BASE + str(machine[ID])), (200, 204))
    check(machine_api.request('DELETE', BASE + str(machine[ID])), 404)


def test_pam_del_004(machine_api):
    check(machine_api.request('DELETE', BASE + 'abc'), 422)


def test_pam_auth_001(machine_api):
    check(machine_api.request('GET'))


@pytest.mark.parametrize('authorization', [None, 'Bearer invalid-or-expired-token'], ids=['missing', 'invalid'])
@pytest.mark.parametrize('operation', ['list', 'get', 'create', 'update', 'delete', 'delete_area'])
def test_pam_authentication(machine_api, machine, authorization, operation):
    method, path, payload = {
        'list': ('GET', BASE, None),
        'get': ('GET', BASE + str(machine[ID]), None),
        'create': ('POST', BASE, machine_api.payload()),
        'update': ('PUT', BASE + str(machine[ID]), {'machine_name': 'unauthorized_change'}),
        'delete': ('DELETE', BASE + str(machine[ID]), None),
        'delete_area': ('DELETE', BASE + f"by-area/{machine['processing_area_id']}", None),
    }[operation]
    response = machine_api.request(method, path, json=payload, headers={'Authorization': authorization})
    check(response, 401)
    assert machine_api.by_area(machine['processing_area_id']) == [machine]
