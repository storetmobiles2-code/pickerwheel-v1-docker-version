"""
Accountability (multi-device P2): every mutating admin route should leave
an audit_log row naming who made the change, via log_audit()/_actor().

Only a representative sample of routes is covered here (one per resource
type, plus the actor-fallback behavior) rather than every single
instrumented route - the thing actually worth regression-testing is the
_actor()/log_audit() mechanism itself (header vs body vs missing), not
that each individual route remembered to call it.
"""
from app.database import execute_sql


def _last_audit_row(entity_type, entity_id):
    rows = execute_sql("""
        SELECT * FROM audit_log
        WHERE entity_type = :entity_type AND entity_id = :entity_id
        ORDER BY id DESC LIMIT 1
    """, {'entity_type': entity_type, 'entity_id': entity_id})
    return rows[0] if rows else None


def test_update_prize_logs_actor_from_header(client, admin_headers, make_prize):
    prize = make_prize()
    headers = {**admin_headers, 'X-Admin-Actor': 'Alice'}

    resp = client.put(f'/api/admin/prizes/{prize["id"]}', json={
        'name': 'Renamed Prize',
        'expected_updated_at': prize['updated_at'].isoformat(),
    }, headers=headers)
    assert resp.status_code == 200

    row = _last_audit_row('prize', prize['id'])
    assert row is not None
    assert row['action'] == 'update'
    assert row['performed_by'] == 'Alice'


def test_update_prize_logs_actor_from_body_when_no_header(client, admin_headers, make_prize):
    prize = make_prize()

    resp = client.put(f'/api/admin/prizes/{prize["id"]}', json={
        'name': 'Renamed Again',
        'expected_updated_at': prize['updated_at'].isoformat(),
        'admin_actor': 'Bob',
    }, headers=admin_headers)
    assert resp.status_code == 200

    row = _last_audit_row('prize', prize['id'])
    assert row['performed_by'] == 'Bob'


def test_update_prize_falls_back_to_unknown_actor(client, admin_headers, make_prize):
    prize = make_prize()

    resp = client.put(f'/api/admin/prizes/{prize["id"]}', json={
        'name': 'Anonymous Edit',
        'expected_updated_at': prize['updated_at'].isoformat(),
    }, headers=admin_headers)
    assert resp.status_code == 200

    row = _last_audit_row('prize', prize['id'])
    assert row['performed_by'] == 'unknown'


def test_create_special_event_logs_actor(client, admin_headers, make_prize):
    prize = make_prize()
    headers = {**admin_headers, 'X-Admin-Actor': 'Carol'}

    resp = client.post('/api/admin/special-events', json={
        'name': 'Test Event',
        'event_type': 'festival',
        'start_datetime': '2026-10-01T00:00:00+00:00',
        'end_datetime': '2026-10-02T00:00:00+00:00',
        'prize_ids': [prize['id']],
    }, headers=headers)
    assert resp.status_code == 200
    event_id = resp.get_json()['event']['id']

    row = _last_audit_row('special_event', event_id)
    assert row['action'] == 'create'
    assert row['performed_by'] == 'Carol'


def test_delete_template_logs_actor(client, admin_headers):
    headers = {**admin_headers, 'X-Admin-Actor': 'Dave'}
    create_resp = client.post('/api/admin/templates', json={'name': 'Deletable Template'}, headers=headers)
    assert create_resp.status_code == 200
    template_id = create_resp.get_json()['template']['id']

    del_resp = client.delete(f'/api/admin/templates/{template_id}', headers=headers)
    assert del_resp.status_code == 200

    row = _last_audit_row('template', template_id)
    assert row['action'] == 'delete'
    assert row['performed_by'] == 'Dave'


def test_reset_daily_wins_logs_actor(client, admin_headers):
    headers = {**admin_headers, 'X-Admin-Actor': 'Erin'}
    resp = client.post('/api/admin/reset-daily-wins', json={
        'confirmation': 'RESET',
    }, headers=headers)
    assert resp.status_code == 200

    rows = execute_sql("""
        SELECT * FROM audit_log WHERE action = 'reset_daily_wins'
        ORDER BY id DESC LIMIT 1
    """)
    assert rows[0]['performed_by'] == 'Erin'
