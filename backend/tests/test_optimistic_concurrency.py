"""
Optimistic concurrency control on the "edit a record" admin routes:
prizes, inventory, special events, templates, guaranteed wins, special-
event theme config, and template-prize rows.

This exists because the admin panel is moving to production usage from
multiple devices at once. Before this, every update() blindly did
`UPDATE ... SET ... WHERE id = :id` with no version check - two admins
on two devices editing the same record would silently overwrite each
other with no warning. See the "Multi-device readiness" board section.

Happy path:
  - an update sent with the current expected_updated_at succeeds
Failure path:
  - an update sent with a STALE expected_updated_at (someone else's
    edit landed first) is rejected with 409, and that someone else's
    change survives untouched
  - expected_updated_at is required - omitting it is rejected (400)
  - updating a record that doesn't exist at all is still a clean 404,
    not a false-positive 409

Special-event theme config and template-prize rows were the last two
resources without this check (found during a production-hardening
review) - theme config used to go through a separate, unlocked
SpecialEvent.update_theme_config() method instead of the properly-locked
generic update(); template_prizes had no updated_at column at all.
"""
from datetime import datetime, timedelta, timezone

import pytest

from app.database import execute_sql


STALE_TIMESTAMP = (datetime.now(timezone.utc) - timedelta(days=365)).isoformat()


# ---- Prizes ----

def test_prize_update_happy_path_with_correct_expected_updated_at(client, admin_headers, make_prize):
    prize = make_prize()
    resp = client.put(f'/api/admin/prizes/{prize["id"]}', json={
        'name': 'Renamed Prize',
        'expected_updated_at': prize['updated_at'],
    }, headers=admin_headers)
    assert resp.status_code == 200
    assert resp.get_json()['prize']['name'] == 'Renamed Prize'


def test_prize_update_conflict_when_stale(client, admin_headers, make_prize):
    prize = make_prize()
    # Someone else's edit lands first
    client.put(f'/api/admin/prizes/{prize["id"]}', json={
        'name': 'First Device Wins',
        'expected_updated_at': prize['updated_at'],
    }, headers=admin_headers)

    # This device is still holding the original (now stale) updated_at
    resp = client.put(f'/api/admin/prizes/{prize["id"]}', json={
        'name': 'Second Device Overwrite Attempt',
        'expected_updated_at': prize['updated_at'],
    }, headers=admin_headers)
    assert resp.status_code == 409

    row = execute_sql('SELECT name FROM prizes WHERE id = :id', {'id': prize['id']})[0]
    assert row['name'] == 'First Device Wins'  # not silently overwritten


def test_prize_update_requires_expected_updated_at(client, admin_headers, make_prize):
    prize = make_prize()
    resp = client.put(f'/api/admin/prizes/{prize["id"]}', json={'name': 'No Version Sent'}, headers=admin_headers)
    assert resp.status_code == 400


def test_prize_update_on_missing_prize_is_404_not_409(client, admin_headers):
    resp = client.put('/api/admin/prizes/999999', json={
        'name': 'Ghost', 'expected_updated_at': STALE_TIMESTAMP,
    }, headers=admin_headers)
    assert resp.status_code == 404


# ---- Inventory ----

def test_inventory_update_happy_path_with_correct_expected_updated_at(client, admin_headers, make_prize):
    from app.models import Inventory
    prize = make_prize(quantity=10, daily_limit=5)
    current = Inventory.get_for_prize(prize['id'])
    resp = client.post(f'/api/admin/inventory/{prize["id"]}/set', json={
        'quantity': 7,
        'expected_updated_at': current['updated_at'].isoformat(),
    }, headers=admin_headers)
    assert resp.status_code == 200


def test_inventory_update_conflict_when_stale(client, admin_headers, make_prize):
    from app.models import Inventory
    prize = make_prize(quantity=10, daily_limit=5)
    current = Inventory.get_for_prize(prize['id'])
    stale_value = current['updated_at'].isoformat()

    client.post(f'/api/admin/inventory/{prize["id"]}/set', json={
        'quantity': 3, 'expected_updated_at': stale_value,
    }, headers=admin_headers)

    resp = client.post(f'/api/admin/inventory/{prize["id"]}/set', json={
        'quantity': 999, 'expected_updated_at': stale_value,
    }, headers=admin_headers)
    assert resp.status_code == 409

    row = execute_sql(
        'SELECT remaining_quantity FROM prize_inventory WHERE prize_id = :id', {'id': prize['id']}
    )[0]
    assert row['remaining_quantity'] == 3


# ---- Special events ----

def test_special_event_update_happy_path_with_correct_expected_updated_at(client, admin_headers):
    now = datetime.now(timezone.utc)
    create = client.post('/api/admin/special-events', json={
        'name': 'Concurrency Test Event',
        'start_datetime': now.isoformat(),
        'end_datetime': (now + timedelta(days=1)).isoformat(),
    }, headers=admin_headers)
    event = create.get_json()['event']

    resp = client.put(f'/api/admin/special-events/{event["id"]}', json={
        'name': 'Renamed Event',
        'expected_updated_at': event['updated_at'],
    }, headers=admin_headers)
    assert resp.status_code == 200


def test_special_event_update_conflict_when_stale(client, admin_headers):
    now = datetime.now(timezone.utc)
    create = client.post('/api/admin/special-events', json={
        'name': 'Concurrency Test Event 2',
        'start_datetime': now.isoformat(),
        'end_datetime': (now + timedelta(days=1)).isoformat(),
    }, headers=admin_headers)
    event = create.get_json()['event']
    stale_value = event['updated_at']

    client.put(f'/api/admin/special-events/{event["id"]}', json={
        'name': 'First Device Name', 'expected_updated_at': stale_value,
    }, headers=admin_headers)

    resp = client.put(f'/api/admin/special-events/{event["id"]}', json={
        'name': 'Second Device Name', 'expected_updated_at': stale_value,
    }, headers=admin_headers)
    assert resp.status_code == 409

    row = execute_sql('SELECT name FROM special_events WHERE id = :id', {'id': event['id']})[0]
    assert row['name'] == 'First Device Name'


# ---- Templates ----

def test_template_update_happy_path_with_correct_expected_updated_at(client, admin_headers):
    create = client.post('/api/admin/templates', json={'name': 'Concurrency Template'}, headers=admin_headers)
    template = create.get_json()['template']

    resp = client.put(f'/api/admin/templates/{template["id"]}', json={
        'name': 'Renamed Template',
        'expected_updated_at': template['updated_at'],
    }, headers=admin_headers)
    assert resp.status_code == 200


def test_template_update_conflict_when_stale(client, admin_headers):
    create = client.post('/api/admin/templates', json={'name': 'Concurrency Template 2'}, headers=admin_headers)
    template = create.get_json()['template']
    stale_value = template['updated_at']

    client.put(f'/api/admin/templates/{template["id"]}', json={
        'name': 'First Device Template', 'expected_updated_at': stale_value,
    }, headers=admin_headers)

    resp = client.put(f'/api/admin/templates/{template["id"]}', json={
        'name': 'Second Device Template', 'expected_updated_at': stale_value,
    }, headers=admin_headers)
    assert resp.status_code == 409

    row = execute_sql(
        'SELECT name FROM daily_prize_templates WHERE id = :id', {'id': template['id']}
    )[0]
    assert row['name'] == 'First Device Template'


# ---- Guaranteed wins ----

def test_guaranteed_win_update_happy_path_with_correct_expected_updated_at(client, admin_headers, make_prize):
    prize = make_prize(quantity=5, daily_limit=5)
    create = client.post('/api/admin/guaranteed-wins', json={
        'prize_id': prize['id'], 'reason': 'concurrency test',
    }, headers=admin_headers)
    win = create.get_json()['win']

    resp = client.put(f'/api/admin/guaranteed-wins/{win["id"]}', json={
        'reason': 'renamed reason',
        'expected_updated_at': win['updated_at'],
    }, headers=admin_headers)
    assert resp.status_code == 200


def test_guaranteed_win_update_conflict_when_stale(client, admin_headers, make_prize):
    prize = make_prize(quantity=5, daily_limit=5)
    create = client.post('/api/admin/guaranteed-wins', json={
        'prize_id': prize['id'], 'reason': 'concurrency test 2',
    }, headers=admin_headers)
    win = create.get_json()['win']
    stale_value = win['updated_at']

    client.put(f'/api/admin/guaranteed-wins/{win["id"]}', json={
        'reason': 'first device reason', 'expected_updated_at': stale_value,
    }, headers=admin_headers)

    resp = client.put(f'/api/admin/guaranteed-wins/{win["id"]}', json={
        'reason': 'second device reason', 'expected_updated_at': stale_value,
    }, headers=admin_headers)
    assert resp.status_code == 409

    row = execute_sql('SELECT reason FROM guaranteed_wins WHERE id = :id', {'id': win['id']})[0]
    assert row['reason'] == 'first device reason'


# ---- Special event theme config ----

def test_theme_update_happy_path_with_correct_expected_updated_at(client, admin_headers):
    now = datetime.now(timezone.utc)
    create = client.post('/api/admin/special-events', json={
        'name': 'Theme Concurrency Event',
        'start_datetime': now.isoformat(),
        'end_datetime': (now + timedelta(days=1)).isoformat(),
    }, headers=admin_headers)
    event = create.get_json()['event']

    resp = client.put(f'/api/admin/special-events/{event["id"]}/theme', json={
        'theme_config': {'primaryColor': '#ff00ff'},
        'expected_updated_at': event['updated_at'],
    }, headers=admin_headers)
    assert resp.status_code == 200
    assert resp.get_json()['event']['theme_config'] == {'primaryColor': '#ff00ff'}


def test_theme_update_conflict_when_stale(client, admin_headers):
    now = datetime.now(timezone.utc)
    create = client.post('/api/admin/special-events', json={
        'name': 'Theme Concurrency Event 2',
        'start_datetime': now.isoformat(),
        'end_datetime': (now + timedelta(days=1)).isoformat(),
    }, headers=admin_headers)
    event = create.get_json()['event']
    stale_value = event['updated_at']

    client.put(f'/api/admin/special-events/{event["id"]}/theme', json={
        'theme_config': {'primaryColor': '#111111'}, 'expected_updated_at': stale_value,
    }, headers=admin_headers)

    resp = client.put(f'/api/admin/special-events/{event["id"]}/theme', json={
        'theme_config': {'primaryColor': '#222222'}, 'expected_updated_at': stale_value,
    }, headers=admin_headers)
    assert resp.status_code == 409

    row = execute_sql('SELECT theme_config FROM special_events WHERE id = :id', {'id': event['id']})[0]
    assert row['theme_config'] == {'primaryColor': '#111111'}


def test_theme_update_requires_expected_updated_at(client, admin_headers):
    now = datetime.now(timezone.utc)
    create = client.post('/api/admin/special-events', json={
        'name': 'Theme No Version Event',
        'start_datetime': now.isoformat(),
        'end_datetime': (now + timedelta(days=1)).isoformat(),
    }, headers=admin_headers)
    event = create.get_json()['event']

    resp = client.put(f'/api/admin/special-events/{event["id"]}/theme', json={
        'theme_config': {'primaryColor': '#333333'},
    }, headers=admin_headers)
    assert resp.status_code == 400


# ---- Template prizes ----

def _create_template_with_prize(client, admin_headers, prize_id):
    template = client.post('/api/admin/templates', json={'name': 'Template Prize Concurrency'},
                            headers=admin_headers).get_json()['template']
    added = client.post(f'/api/admin/templates/{template["id"]}/prizes', json={
        'prize_id': prize_id, 'quantity': 3, 'daily_limit': 2,
    }, headers=admin_headers).get_json()['template_prize']
    return template, added


def test_template_prize_update_happy_path_with_correct_expected_updated_at(client, admin_headers, make_prize):
    prize = make_prize()
    template, tp = _create_template_with_prize(client, admin_headers, prize['id'])

    resp = client.put(f'/api/admin/templates/{template["id"]}/prizes/{tp["id"]}', json={
        'quantity': 9,
        'expected_updated_at': tp['updated_at'],
    }, headers=admin_headers)
    assert resp.status_code == 200
    assert resp.get_json()['template_prize']['quantity'] == 9


def test_template_prize_update_conflict_when_stale(client, admin_headers, make_prize):
    prize = make_prize()
    template, tp = _create_template_with_prize(client, admin_headers, prize['id'])
    stale_value = tp['updated_at']

    client.put(f'/api/admin/templates/{template["id"]}/prizes/{tp["id"]}', json={
        'quantity': 5, 'expected_updated_at': stale_value,
    }, headers=admin_headers)

    resp = client.put(f'/api/admin/templates/{template["id"]}/prizes/{tp["id"]}', json={
        'quantity': 999, 'expected_updated_at': stale_value,
    }, headers=admin_headers)
    assert resp.status_code == 409

    row = execute_sql('SELECT quantity FROM template_prizes WHERE id = :id', {'id': tp['id']})[0]
    assert row['quantity'] == 5


def test_template_prize_update_requires_expected_updated_at(client, admin_headers, make_prize):
    prize = make_prize()
    template, tp = _create_template_with_prize(client, admin_headers, prize['id'])

    resp = client.put(f'/api/admin/templates/{template["id"]}/prizes/{tp["id"]}', json={'quantity': 5},
                       headers=admin_headers)
    assert resp.status_code == 400


def test_template_prize_add_as_edit_conflict_when_stale(client, admin_headers, make_prize):
    """add_prize_to_template doubles as an edit (ON CONFLICT DO UPDATE) -
    expected_updated_at is optional there (a brand-new add has nothing to
    conflict with), but once supplied it must still be honored."""
    prize = make_prize()
    template, tp = _create_template_with_prize(client, admin_headers, prize['id'])
    stale_value = tp['updated_at']

    # Someone else edits it via the plain update route first
    client.put(f'/api/admin/templates/{template["id"]}/prizes/{tp["id"]}', json={
        'quantity': 5, 'expected_updated_at': stale_value,
    }, headers=admin_headers)

    # This device retries the add-as-edit endpoint with its now-stale copy
    resp = client.post(f'/api/admin/templates/{template["id"]}/prizes', json={
        'prize_id': prize['id'], 'quantity': 999, 'daily_limit': 2,
        'expected_updated_at': stale_value,
    }, headers=admin_headers)
    assert resp.status_code == 409

    row = execute_sql('SELECT quantity FROM template_prizes WHERE id = :id', {'id': tp['id']})[0]
    assert row['quantity'] == 5


def test_template_prize_add_without_expected_updated_at_is_a_plain_upsert(client, admin_headers, make_prize):
    """Adding a genuinely new prize to a template has nothing to conflict
    with - expected_updated_at is optional and omitting it just works."""
    prize = make_prize()
    template = client.post('/api/admin/templates', json={'name': 'Fresh Add Template'},
                            headers=admin_headers).get_json()['template']

    resp = client.post(f'/api/admin/templates/{template["id"]}/prizes', json={
        'prize_id': prize['id'], 'quantity': 4, 'daily_limit': 2,
    }, headers=admin_headers)
    assert resp.status_code == 200
    assert resp.get_json()['template_prize']['quantity'] == 4
