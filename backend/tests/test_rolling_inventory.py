"""
Rolling daily inventory: the wheel must keep working after the initial
seeded window of days runs out.

Regression for the "No prizes available" outage: inventory is one row per
prize per day and the initial load only seeds ~60 days, so once today fell
past the last seeded day there were no rows for today and /pre-spin
returned 400 - the app effectively had an end date. Inventory.ensure_for_date
now fills in today from each prize's most recent earlier row.
"""
from datetime import date, timedelta

from app.database import execute_sql
from app.models import Inventory

YESTERDAY = date.today() - timedelta(days=1)


def _today_row(prize_id):
    rows = execute_sql(
        'SELECT initial_quantity, remaining_quantity, daily_limit '
        'FROM prize_inventory WHERE prize_id = :id AND available_date = CURRENT_DATE',
        {'id': prize_id}
    )
    return rows[0] if rows else None


def test_pre_spin_works_after_seeded_window_runs_out(client, make_prize):
    """The reported outage: inventory only exists up to yesterday."""
    prize = make_prize(quantity=10, daily_limit=2, target_date=YESTERDAY)
    assert _today_row(prize['id']) is None

    resp = client.post('/api/pre-spin', json={'user_id': 'k'})
    assert resp.status_code == 200
    assert resp.get_json()['selected_prize']['id'] == prize['id']


def test_new_day_row_carries_config_forward_with_fresh_stock(app, make_prize):
    prize = make_prize(quantity=10, daily_limit=2, target_date=YESTERDAY)
    # Yesterday's stock was nearly sold out - today must start full again
    execute_sql(
        'UPDATE prize_inventory SET remaining_quantity = 1 WHERE prize_id = :id',
        {'id': prize['id']}
    )
    with app.app_context():
        assert Inventory.ensure_for_date() == 1

    row = _today_row(prize['id'])
    assert row['initial_quantity'] == 10
    assert row['remaining_quantity'] == 10
    assert row['daily_limit'] == 2


def test_carries_forward_from_most_recent_row_not_oldest(app, make_prize):
    prize = make_prize(quantity=5, daily_limit=1, target_date=YESTERDAY - timedelta(days=5))
    execute_sql(
        'INSERT INTO prize_inventory (prize_id, event_id, available_date, '
        'initial_quantity, remaining_quantity, daily_limit) '
        'VALUES (:id, 1, :d, 8, 8, 3)',
        {'id': prize['id'], 'd': YESTERDAY}
    )
    with app.app_context():
        Inventory.ensure_for_date()
    row = _today_row(prize['id'])
    assert (row['initial_quantity'], row['daily_limit']) == (8, 3)


def test_existing_row_for_today_is_never_overwritten(app, make_prize):
    prize = make_prize(quantity=10, daily_limit=2)  # today's row exists
    execute_sql(
        'UPDATE prize_inventory SET remaining_quantity = 4 '
        'WHERE prize_id = :id AND available_date = CURRENT_DATE',
        {'id': prize['id']}
    )
    with app.app_context():
        assert Inventory.ensure_for_date() == 0
    assert _today_row(prize['id'])['remaining_quantity'] == 4


def test_ensure_is_idempotent(app, make_prize):
    make_prize(quantity=10, daily_limit=2, target_date=YESTERDAY)
    with app.app_context():
        assert Inventory.ensure_for_date() == 1
        assert Inventory.ensure_for_date() == 0


def test_date_limited_prize_stays_unavailable(client, make_prize):
    """A prize that was out of stock on its last seeded day (how the data
    load marks "not available on this date") must not suddenly appear."""
    sold_out = make_prize(quantity=0, daily_limit=1, target_date=YESTERDAY, name='date-limited')
    healthy = make_prize(quantity=10, daily_limit=2, target_date=YESTERDAY, name='always')

    body = client.post('/api/pre-spin', json={'user_id': 'k'}).get_json()
    assert body['selected_prize']['id'] == healthy['id']
    assert _today_row(sold_out['id'])['remaining_quantity'] == 0


def test_prize_that_never_had_inventory_is_left_alone(app, make_prize):
    prize = make_prize(quantity=10, daily_limit=2)
    execute_sql('DELETE FROM prize_inventory WHERE prize_id = :id', {'id': prize['id']})
    with app.app_context():
        assert Inventory.ensure_for_date() == 0
    assert _today_row(prize['id']) is None


def test_inactive_prize_is_not_rolled_forward(app, make_prize):
    prize = make_prize(quantity=10, daily_limit=2, target_date=YESTERDAY)
    execute_sql('UPDATE prizes SET is_active = FALSE WHERE id = :id', {'id': prize['id']})
    with app.app_context():
        assert Inventory.ensure_for_date() == 0


def test_only_today_is_ever_filled_in(app, make_prize):
    make_prize(quantity=10, daily_limit=2, target_date=YESTERDAY)
    with app.app_context():
        assert Inventory.ensure_for_date(target_date=date.today() + timedelta(days=3)) == 0
        assert Inventory.ensure_for_date(target_date=YESTERDAY) == 0


def test_wheel_display_and_spin_work_end_to_end_on_a_rolled_day(client, make_prize):
    prize = make_prize(quantity=3, daily_limit=3, target_date=YESTERDAY)
    make_prize(quantity=3, daily_limit=3, target_date=YESTERDAY, name='second')

    wheel = client.get('/api/prizes/wheel-display').get_json()
    assert any(p['prize_id'] == prize['id'] for p in wheel['prizes'])

    pre = client.post('/api/pre-spin', json={'user_id': 'k'}).get_json()
    spin = client.post('/api/spin', json={
        'user_id': 'k', 'selected_prize_id': pre['selected_prize']['id']})
    assert spin.status_code == 200
    won = _today_row(pre['selected_prize']['id'])
    assert won['remaining_quantity'] == 2  # 3 fresh, one consumed
