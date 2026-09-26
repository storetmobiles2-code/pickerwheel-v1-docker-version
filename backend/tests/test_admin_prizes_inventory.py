"""
Admin prize and inventory management.

Happy path:
  - add-prize honors the admin-entered quantity/daily_limit (regression:
    these used to be silently dropped in favor of category defaults)
  - set-inventory updates quantity and daily_limit together in one call
  - toggle/update/delete a prize
  - replenish resets remaining_quantity back to initial_quantity
Failure path:
  - add-prize rejects a missing name/category_id
  - add-prize rejects a negative/non-numeric quantity or daily_limit
  - set-inventory rejects a negative/non-numeric quantity
  - set-inventory on a prize with no inventory row returns 404
"""
from datetime import date

from app.database import execute_sql


def test_add_prize_happy_path_honors_admin_quantity(client, admin_headers):
    resp = client.post('/api/admin/prizes', json={
        'name': 'Custom Quantity Prize',
        'category_id': 3,
        'initial_quantity': 17,
        'daily_limit': 6,
    }, headers=admin_headers)
    assert resp.status_code == 200
    body = resp.get_json()
    assert body['success'] is True
    prize_id = body['prize']['id']

    row = execute_sql(
        'SELECT initial_quantity, remaining_quantity, daily_limit FROM prize_inventory '
        'WHERE prize_id = :id AND available_date = :today',
        {'id': prize_id, 'today': date.today()}
    )[0]
    assert row['initial_quantity'] == 17
    assert row['remaining_quantity'] == 17
    assert row['daily_limit'] == 6


def test_add_prize_requires_name_and_category(client, admin_headers):
    resp = client.post('/api/admin/prizes', json={'category_id': 3}, headers=admin_headers)
    assert resp.status_code == 400

    resp2 = client.post('/api/admin/prizes', json={'name': 'No Category'}, headers=admin_headers)
    assert resp2.status_code == 400


def test_add_prize_rejects_negative_quantity(client, admin_headers):
    resp = client.post('/api/admin/prizes', json={
        'name': 'Bad Quantity Prize', 'category_id': 3, 'initial_quantity': -5,
    }, headers=admin_headers)
    assert resp.status_code == 400
    assert resp.get_json()['success'] is False


def test_add_prize_rejects_non_numeric_quantity(client, admin_headers):
    resp = client.post('/api/admin/prizes', json={
        'name': 'Bad Type Prize', 'category_id': 3, 'initial_quantity': 'lots',
    }, headers=admin_headers)
    assert resp.status_code == 400


def test_toggle_prize_enabled(client, admin_headers, make_prize):
    prize = make_prize(is_enabled=True)
    resp = client.post(f'/api/admin/prizes/{prize["id"]}/toggle',
                        json={'is_enabled': False}, headers=admin_headers)
    assert resp.status_code == 200
    row = execute_sql('SELECT is_enabled FROM prizes WHERE id = :id', {'id': prize['id']})[0]
    assert row['is_enabled'] is False


def test_toggle_nonexistent_prize_returns_404(client, admin_headers):
    resp = client.post('/api/admin/prizes/999999/toggle', json={'is_enabled': False}, headers=admin_headers)
    assert resp.status_code == 404


def test_delete_prize_soft_deletes(client, admin_headers, make_prize):
    prize = make_prize()
    resp = client.delete(f'/api/admin/prizes/{prize["id"]}', headers=admin_headers)
    assert resp.status_code == 200
    row = execute_sql('SELECT is_active FROM prizes WHERE id = :id', {'id': prize['id']})[0]
    assert row['is_active'] is False


def test_set_inventory_updates_quantity_and_daily_limit_together(client, admin_headers, make_prize):
    from app.models import Inventory
    prize = make_prize(quantity=10, daily_limit=5)
    current = Inventory.get_for_prize(prize['id'])
    resp = client.post(f'/api/admin/inventory/{prize["id"]}/set', json={
        'quantity': 3, 'daily_limit': 2,
        'expected_updated_at': current['updated_at'].isoformat(),
    }, headers=admin_headers)
    assert resp.status_code == 200
    row = execute_sql(
        'SELECT remaining_quantity, daily_limit FROM prize_inventory WHERE prize_id = :id',
        {'id': prize['id']}
    )[0]
    assert row['remaining_quantity'] == 3
    assert row['daily_limit'] == 2


def test_set_inventory_rejects_negative_quantity(client, admin_headers, make_prize):
    prize = make_prize()
    resp = client.post(f'/api/admin/inventory/{prize["id"]}/set',
                        json={'quantity': -1}, headers=admin_headers)
    assert resp.status_code == 400


def test_set_inventory_rejects_non_numeric_daily_limit(client, admin_headers, make_prize):
    prize = make_prize()
    resp = client.post(f'/api/admin/inventory/{prize["id"]}/set',
                        json={'daily_limit': 'unlimited'}, headers=admin_headers)
    assert resp.status_code == 400


def test_set_inventory_requires_at_least_one_field(client, admin_headers, make_prize):
    prize = make_prize()
    resp = client.post(f'/api/admin/inventory/{prize["id"]}/set', json={}, headers=admin_headers)
    assert resp.status_code == 400


def test_set_inventory_on_prize_with_no_inventory_row_returns_404(client, admin_headers):
    # A prize row with no matching prize_inventory row for today
    from app.models import Prize
    from datetime import datetime, timezone
    prize = Prize.create('No Inventory Prize', 3)
    resp = client.post(f'/api/admin/inventory/{prize["id"]}/set', json={
        'quantity': 5,
        'expected_updated_at': datetime.now(timezone.utc).isoformat(),
    }, headers=admin_headers)
    assert resp.status_code == 404


def test_replenish_resets_remaining_to_initial(client, admin_headers, make_prize):
    prize = make_prize(quantity=10, daily_limit=5)
    # spin it down
    client.post('/api/spin', json={'user_id': 'depleter', 'prize_id': prize['id']})
    depleted = execute_sql(
        'SELECT remaining_quantity FROM prize_inventory WHERE prize_id = :id', {'id': prize['id']}
    )[0]['remaining_quantity']
    assert depleted == 9

    resp = client.post('/api/admin/inventory/replenish', json={}, headers=admin_headers)
    assert resp.status_code == 200

    restored = execute_sql(
        'SELECT remaining_quantity FROM prize_inventory WHERE prize_id = :id', {'id': prize['id']}
    )[0]['remaining_quantity']
    assert restored == 10
