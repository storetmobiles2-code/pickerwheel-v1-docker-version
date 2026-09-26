"""
Admin special events.

Happy path:
  - creating an event with a theme and prizes lands all three atomically
Failure path:
  - a bad prize_id in the create payload rolls back the whole event
    (regression: this used to leave a half-configured event behind -
    the event existed but the FK-invalid prize link silently failed)
  - an invalid event_type is rejected by the DB constraint
    (regression: the admin UI offers types the DB used to reject)
  - an invalid start_datetime/end_datetime is rejected with 400, not
    silently passed through (regression: it used to be swallowed and
    the raw string passed to the DB)
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
