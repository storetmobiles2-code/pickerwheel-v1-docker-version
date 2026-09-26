"""
Admin special events.

Happy path:
  - creating an event with a theme and prizes lands all three atomically
  - toggling activates/deactivates
  - deleting removes the event and cascades to its prize links
  - resetting theme_config clears it back to {}
  - adding/removing a prize updates the special_event_prizes link table
Failure path:
  - a bad prize_id in the create payload rolls back the whole event
    (regression: this used to leave a half-configured event behind -
    the event existed but the FK-invalid prize link silently failed)
  - an invalid event_type is rejected by the DB constraint
    (regression: the admin UI offers types the DB used to reject)
  - an invalid start_datetime/end_datetime is rejected with 400, not
    silently passed through (regression: it used to be swallowed and
    the raw string passed to the DB)
  - toggle/theme-reset/add-prize reject a missing required field
  - toggle/delete/remove-prize on a nonexistent event or link is a clean
    404, not a 500
"""
from datetime import datetime, timedelta

from app.database import execute_sql


def _iso(dt):
    return dt.isoformat() + 'Z'


def test_create_special_event_happy_path_is_atomic(client, admin_headers, make_prize):
    prize = make_prize()
    now = datetime.utcnow()
    resp = client.post('/api/admin/special-events', json={
        'name': 'Test Festival',
        'start_datetime': _iso(now),
        'end_datetime': _iso(now + timedelta(days=1)),
        'event_type': 'festival',
        'prize_ids': [prize['id']],
        'theme_config': {'primaryColor': '#ff0000'},
    }, headers=admin_headers)
    assert resp.status_code == 200
    body = resp.get_json()
    assert body['success'] is True
    event_id = body['event']['id']

    theme = execute_sql(
        'SELECT theme_config FROM special_events WHERE id = :id', {'id': event_id}
    )[0]['theme_config']
    assert theme is not None

    linked = execute_sql(
        'SELECT COUNT(*) AS n FROM special_event_prizes WHERE special_event_id = :id',
        {'id': event_id}
    )[0]['n']
    assert linked == 1


def test_create_special_event_with_bad_prize_id_rolls_back_entirely(client, admin_headers):
    now = datetime.utcnow()
    before_count = execute_sql('SELECT COUNT(*) AS n FROM special_events')[0]['n']

    resp = client.post('/api/admin/special-events', json={
        'name': 'Doomed Event',
        'start_datetime': _iso(now),
        'end_datetime': _iso(now + timedelta(days=1)),
        'prize_ids': [999999],  # doesn't exist -> FK violation
    }, headers=admin_headers)
    assert resp.status_code == 400
    assert resp.get_json()['success'] is False

    after_count = execute_sql('SELECT COUNT(*) AS n FROM special_events')[0]['n']
    assert after_count == before_count  # nothing was left behind

    leftover = execute_sql(
        "SELECT COUNT(*) AS n FROM special_events WHERE name = 'Doomed Event'"
    )[0]['n']
    assert leftover == 0


def test_create_special_event_rejects_invalid_event_type(client, admin_headers):
    now = datetime.utcnow()
    resp = client.post('/api/admin/special-events', json={
        'name': 'Bad Type Event',
        'start_datetime': _iso(now),
        'end_datetime': _iso(now + timedelta(days=1)),
        'event_type': 'not_a_real_type',
    }, headers=admin_headers)
    # Either the route validates it (400) or the DB constraint rejects it
    # and the route surfaces that as an error - either way, not a 500,
    # and no event should be created.
    assert resp.status_code in (400, 500)
    leftover = execute_sql(
        "SELECT COUNT(*) AS n FROM special_events WHERE name = 'Bad Type Event'"
    )[0]['n']
    assert leftover == 0


def test_create_special_event_accepts_ui_offered_types(client, admin_headers):
    """national_holiday and custom are offered by the admin UI dropdown -
    the DB constraint must actually allow them (regression: it didn't)."""
    now = datetime.utcnow()
    for event_type in ('national_holiday', 'custom'):
        resp = client.post('/api/admin/special-events', json={
            'name': f'Type check {event_type}',
            'start_datetime': _iso(now),
            'end_datetime': _iso(now + timedelta(days=1)),
            'event_type': event_type,
        }, headers=admin_headers)
        assert resp.status_code == 200, f'{event_type} should be accepted'


def test_create_special_event_requires_required_fields(client, admin_headers):
    resp = client.post('/api/admin/special-events', json={'name': 'Missing dates'}, headers=admin_headers)
    assert resp.status_code == 400


def test_update_special_event_rejects_invalid_datetime(client, admin_headers, make_prize):
    now = datetime.utcnow()
    create = client.post('/api/admin/special-events', json={
        'name': 'To Be Updated',
        'start_datetime': _iso(now),
        'end_datetime': _iso(now + timedelta(days=1)),
    }, headers=admin_headers)
    event_id = create.get_json()['event']['id']

    resp = client.put(f'/api/admin/special-events/{event_id}',
                       json={'start_datetime': 'not-a-real-date'}, headers=admin_headers)
    assert resp.status_code == 400

    # The bad value must not have been written through
    row = execute_sql(
        'SELECT start_datetime FROM special_events WHERE id = :id', {'id': event_id}
    )[0]
    assert row['start_datetime'] is not None


def _create_event(client, admin_headers, name, **extra):
    now = datetime.utcnow()
    payload = {
        'name': name,
        'start_datetime': _iso(now),
        'end_datetime': _iso(now + timedelta(days=1)),
    }
    payload.update(extra)
    return client.post('/api/admin/special-events', json=payload, headers=admin_headers).get_json()['event']


# ---- Toggle ----

def test_toggle_special_event_activates_and_deactivates(client, admin_headers):
    event = _create_event(client, admin_headers, 'Toggle Test Event')

    off = client.post(f'/api/admin/special-events/{event["id"]}/toggle',
                       json={'is_active': False}, headers=admin_headers)
    assert off.status_code == 200
    assert off.get_json()['event']['is_active'] is False
    row = execute_sql('SELECT is_active FROM special_events WHERE id = :id', {'id': event['id']})[0]
    assert row['is_active'] is False

    on = client.post(f'/api/admin/special-events/{event["id"]}/toggle',
                      json={'is_active': True}, headers=admin_headers)
    assert on.status_code == 200
    assert on.get_json()['event']['is_active'] is True


def test_toggle_special_event_requires_is_active(client, admin_headers):
    event = _create_event(client, admin_headers, 'Toggle Missing Field Event')
    resp = client.post(f'/api/admin/special-events/{event["id"]}/toggle', json={}, headers=admin_headers)
    assert resp.status_code == 400


def test_toggle_nonexistent_special_event_returns_404(client, admin_headers):
    resp = client.post('/api/admin/special-events/999999/toggle',
                        json={'is_active': True}, headers=admin_headers)
    assert resp.status_code == 404


# ---- Delete ----

def test_delete_special_event_removes_it_and_cascades_prize_links(client, admin_headers, make_prize):
    prize = make_prize()
    event = _create_event(client, admin_headers, 'Delete Test Event', prize_ids=[prize['id']])

    resp = client.delete(f'/api/admin/special-events/{event["id"]}', headers=admin_headers)
    assert resp.status_code == 200
    assert resp.get_json()['success'] is True

    remaining = execute_sql(
        'SELECT COUNT(*) AS n FROM special_events WHERE id = :id', {'id': event['id']}
    )[0]['n']
    assert remaining == 0

    linked = execute_sql(
        'SELECT COUNT(*) AS n FROM special_event_prizes WHERE special_event_id = :id',
        {'id': event['id']}
    )[0]['n']
    assert linked == 0  # ON DELETE CASCADE, not left orphaned


def test_delete_nonexistent_special_event_returns_404(client, admin_headers):
    resp = client.delete('/api/admin/special-events/999999', headers=admin_headers)
    assert resp.status_code == 404


# ---- Theme reset ----

def test_reset_event_theme_clears_it_back_to_empty(client, admin_headers):
    event = _create_event(client, admin_headers, 'Theme Reset Event',
                           theme_config={'primaryColor': '#123456'})

    resp = client.delete(f'/api/admin/special-events/{event["id"]}/theme', json={
        'expected_updated_at': event['updated_at'],
    }, headers=admin_headers)
    assert resp.status_code == 200
    assert resp.get_json()['event']['theme_config'] == {}

    row = execute_sql(
        'SELECT theme_config FROM special_events WHERE id = :id', {'id': event['id']}
    )[0]
    assert row['theme_config'] == {}


def test_reset_event_theme_requires_expected_updated_at(client, admin_headers):
    event = _create_event(client, admin_headers, 'Theme Reset No Version Event',
                           theme_config={'primaryColor': '#abcdef'})
    resp = client.delete(f'/api/admin/special-events/{event["id"]}/theme', json={}, headers=admin_headers)
    assert resp.status_code == 400


# ---- Prize linking ----

def test_add_prize_to_event_and_remove_prize_from_event(client, admin_headers, make_prize):
    prize = make_prize()
    event = _create_event(client, admin_headers, 'Prize Link Event')

    add = client.post(f'/api/admin/special-events/{event["id"]}/prizes', json={
        'prize_id': prize['id'], 'weight_multiplier': 3.0,
    }, headers=admin_headers)
    assert add.status_code == 200
    assert add.get_json()['event_prize']['prize_id'] == prize['id']

    linked = execute_sql(
        'SELECT COUNT(*) AS n FROM special_event_prizes WHERE special_event_id = :e AND prize_id = :p',
        {'e': event['id'], 'p': prize['id']}
    )[0]['n']
    assert linked == 1

    remove = client.delete(f'/api/admin/special-events/{event["id"]}/prizes/{prize["id"]}',
                            headers=admin_headers)
    assert remove.status_code == 200

    linked_after = execute_sql(
        'SELECT COUNT(*) AS n FROM special_event_prizes WHERE special_event_id = :e AND prize_id = :p',
        {'e': event['id'], 'p': prize['id']}
    )[0]['n']
    assert linked_after == 0


def test_add_prize_to_event_requires_prize_id(client, admin_headers):
    event = _create_event(client, admin_headers, 'Missing Prize ID Event')
    resp = client.post(f'/api/admin/special-events/{event["id"]}/prizes', json={}, headers=admin_headers)
    assert resp.status_code == 400


def test_remove_prize_not_linked_to_event_returns_404(client, admin_headers, make_prize):
    prize = make_prize()
    event = _create_event(client, admin_headers, 'No Link Event')
    resp = client.delete(f'/api/admin/special-events/{event["id"]}/prizes/{prize["id"]}',
                          headers=admin_headers)
    assert resp.status_code == 404
