"""
Public (non-admin) read endpoints.

Happy path:
  - /api/health always returns healthy
  - /api/categories returns the seeded categories
  - /api/prizes/wheel-display returns every active prize, including
    disabled ones (the wheel still shows them, just not spinnable)
  - /api/config reflects an active special event's theme when one is
    running, and omits it when none is
Failure path:
  - /api/prizes/wheel-display with an unparsable date query param
    returns 400/500 cleanly rather than crashing past a stack trace
    into a raw 500 with internals exposed
"""
from datetime import datetime, timedelta

from app.database import execute_sql


def test_health(client):
    resp = client.get('/api/health')
    assert resp.status_code == 200
    assert resp.get_json()['status'] == 'healthy'


def test_categories_returns_seeded_categories(client):
    resp = client.get('/api/categories')
    assert resp.status_code == 200
    names = {c['name'] for c in resp.get_json()['categories']}
    assert names == {'ultra_rare', 'rare', 'common'}


def test_wheel_display_includes_disabled_prizes(client, make_prize):
    enabled = make_prize(is_enabled=True, name='Enabled Wheel Prize')
    disabled = make_prize(is_enabled=False, name='Disabled Wheel Prize')

    resp = client.get('/api/prizes/wheel-display')
    assert resp.status_code == 200
    ids = {p['prize_id'] for p in resp.get_json()['prizes']}
    assert enabled['id'] in ids
    assert disabled['id'] in ids  # shown but not spinnable


def test_wheel_display_with_malformed_date_does_not_500_with_internals(client):
    resp = client.get('/api/prizes/wheel-display?date=not-a-date')
    assert resp.status_code in (400, 500)
    body = resp.get_json()
    # Whatever the status, it must be a clean JSON error, not a stack trace
    assert isinstance(body, dict)
    assert 'success' in body


def test_config_reflects_active_special_event_theme(client, admin_headers, make_prize):
    now = datetime.utcnow()
    create = client.post('/api/admin/special-events', json={
        'name': 'Live Themed Event',
        'start_datetime': (now - timedelta(hours=1)).isoformat() + 'Z',
        'end_datetime': (now + timedelta(hours=1)).isoformat() + 'Z',
        'event_type': 'festival',
        'theme_config': {'primaryColor': '#123456'},
    }, headers=admin_headers)
    assert create.status_code == 200

    resp = client.get('/api/config')
    assert resp.status_code == 200
    body = resp.get_json()
    assert body['theme'] is not None
    assert body['theme']['primaryColor'] == '#123456'
    assert body['event']['is_active'] is True
    assert body['event']['name'] == 'Live Themed Event'


def test_config_has_no_theme_when_no_event_is_active(client):
    resp = client.get('/api/config')
    assert resp.status_code == 200
    body = resp.get_json()
    assert body['theme'] is None
    assert body['event']['is_active'] is False
