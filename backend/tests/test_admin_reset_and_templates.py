"""
Reset Daily Wins, prize templates, and date-range assignment validation.

Happy path:
  - reset-daily-wins wipes today's win transactions and restores
    inventory to initial_quantity, and writes an audit_log entry
    (regression: it used to be two separate commits with no audit trail)
  - populate-all fills a template with every active prize
  - a valid date range assignment succeeds
Failure path:
  - reset-daily-wins requires the exact confirmation string
  - assigning a date range with start after end is rejected
  - assigning a date range over 366 days is rejected
"""
from datetime import date, timedelta

from app.database import execute_sql


def test_reset_daily_wins_happy_path_is_atomic_with_audit(client, admin_headers, make_prize):
    prize = make_prize(quantity=10, daily_limit=5)
    client.post('/api/spin', json={'user_id': 'to-be-reset', 'prize_id': prize['id']})
    assert execute_sql(
        'SELECT remaining_quantity FROM prize_inventory WHERE prize_id = :id', {'id': prize['id']}
    )[0]['remaining_quantity'] == 9

    resp = client.post('/api/admin/reset-daily-wins', json={'confirmation': 'RESET'}, headers=admin_headers)
    assert resp.status_code == 200
    body = resp.get_json()
    assert body['details']['transactions_deleted'] == 1
    assert body['details']['inventory_records_reset'] == 1

    restored = execute_sql(
        'SELECT remaining_quantity FROM prize_inventory WHERE prize_id = :id', {'id': prize['id']}
    )[0]['remaining_quantity']
    assert restored == 10

    tx_count = execute_sql(
        "SELECT COUNT(*) AS n FROM transactions WHERE prize_id = :id", {'id': prize['id']}
    )[0]['n']
    assert tx_count == 0

    audit_count = execute_sql(
        "SELECT COUNT(*) AS n FROM audit_log WHERE action = 'reset_daily_wins'"
    )[0]['n']
    assert audit_count == 1


def test_reset_daily_wins_requires_exact_confirmation_string(client, admin_headers, make_prize):
    prize = make_prize(quantity=10, daily_limit=5)
    client.post('/api/spin', json={'user_id': 'not-reset', 'prize_id': prize['id']})

    resp = client.post('/api/admin/reset-daily-wins', json={'confirmation': 'yes please'}, headers=admin_headers)
    assert resp.status_code == 400

    # Nothing was touched
    remaining = execute_sql(
        'SELECT remaining_quantity FROM prize_inventory WHERE prize_id = :id', {'id': prize['id']}
    )[0]['remaining_quantity']
    assert remaining == 9


def test_reset_daily_wins_requires_confirmation_field(client, admin_headers):
    resp = client.post('/api/admin/reset-daily-wins', json={}, headers=admin_headers)
    assert resp.status_code == 400


def test_populate_template_with_all_prizes(client, admin_headers, wheel_of_prizes):
    template = client.post('/api/admin/templates', json={'name': 'Full Rotation'}, headers=admin_headers)
    template_id = template.get_json()['template']['id']

    resp = client.post(f'/api/admin/templates/{template_id}/populate-all',
                        json={'quantity': 3}, headers=admin_headers)
    assert resp.status_code == 200
    assert resp.get_json()['added_count'] == len(wheel_of_prizes)

    count = execute_sql(
        'SELECT COUNT(*) AS n FROM template_prizes WHERE template_id = :id', {'id': template_id}
    )[0]['n']
    assert count == len(wheel_of_prizes)


def test_assign_date_range_happy_path(client, admin_headers):
    template = client.post('/api/admin/templates', json={'name': 'Range Template'}, headers=admin_headers)
    template_id = template.get_json()['template']['id']

    start = date.today() + timedelta(days=1)
    end = start + timedelta(days=5)
    resp = client.post('/api/admin/date-assignments', json={
        'template_id': template_id,
        'start_date': start.isoformat(),
        'end_date': end.isoformat(),
    }, headers=admin_headers)
    assert resp.status_code == 200
    assert resp.get_json()['count'] == 6  # inclusive of both ends


def test_assign_date_range_rejects_start_after_end(client, admin_headers):
    template = client.post('/api/admin/templates', json={'name': 'Backwards Range'}, headers=admin_headers)
    template_id = template.get_json()['template']['id']

    start = date.today() + timedelta(days=10)
    end = date.today() + timedelta(days=1)
    resp = client.post('/api/admin/date-assignments', json={
        'template_id': template_id,
        'start_date': start.isoformat(),
        'end_date': end.isoformat(),
    }, headers=admin_headers)
    assert resp.status_code == 400


def test_assign_date_range_rejects_over_366_days(client, admin_headers):
    template = client.post('/api/admin/templates', json={'name': 'Huge Range'}, headers=admin_headers)
    template_id = template.get_json()['template']['id']

    start = date.today()
    end = start + timedelta(days=400)
    resp = client.post('/api/admin/date-assignments', json={
        'template_id': template_id,
        'start_date': start.isoformat(),
        'end_date': end.isoformat(),
    }, headers=admin_headers)
    assert resp.status_code == 400
