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


# ---------------------------------------------------------------------------
# Long-horizon simulation: the wheel keeps working for over a year with no
# manual refresh, including prizes added by an admin part-way through (the
# admin "add prize" route only pre-seeds 30 days of rows for a new prize, a
# second hidden end date this has to cover).
# ---------------------------------------------------------------------------
import pytest
from app.models import Prize
from app.models import inventory as inventory_module

_RealDate = date


@pytest.fixture()
def fake_today(monkeypatch):
    """Lets a test move 'today' for Inventory.ensure_for_date, which reads
    date.today() from the inventory module."""
    class _FakeDate(_RealDate):
        current = _RealDate.today()

        @classmethod
        def today(cls):
            return cls.current

    monkeypatch.setattr(inventory_module, 'date', _FakeDate)
    return _FakeDate


def _names_available(app, day):
    with app.app_context():
        return {p['name'] for p in Prize.get_available_for_spin(1, day)}


def test_wheel_keeps_working_for_over_a_year_including_new_prizes(app, make_prize, fake_today):
    start = _RealDate.today()
    fake_today.current = start

    # Seeded the way the admin add-prize route does it: a fixed window only
    for name, qty, limit in (('always-A', 10, 2), ('always-B', 5, 1)):
        p = make_prize(quantity=qty, daily_limit=limit, name=name)
        with app.app_context():
            Inventory.create_for_prize_range(p['id'], start_date=start, days=30,
                                             initial_quantity=qty, daily_limit=limit)
    # A "only on specific dates" prize, stored as 0 stock on every other day
    make_prize(quantity=0, daily_limit=1, name='date-limited')

    added_c = False
    for offset in range(0, 420):
        day = start + timedelta(days=offset)
        fake_today.current = day

        if offset == 100 and not added_c:
            # admin adds a prize on day 100 - gets only 30 days pre-seeded
            c = make_prize(quantity=7, daily_limit=3, name='added-C', target_date=day)
            with app.app_context():
                Inventory.create_for_prize_range(c['id'], start_date=day, days=30,
                                                 initial_quantity=7, daily_limit=3)
            added_c = True

        got = _names_available(app, day)
        assert {'always-A', 'always-B'} <= got, f'day +{offset} ({day}): wheel lost its prizes: {got}'
        assert 'date-limited' not in got
        if offset >= 100:
            assert 'added-C' in got, f'day +{offset} ({day}): added prize vanished: {got}'

    # Config carried all the way through, with full fresh stock each day
    last = execute_sql(
        "SELECT p.name, pi.initial_quantity iq, pi.remaining_quantity rem, pi.daily_limit lim "
        "FROM prize_inventory pi JOIN prizes p ON p.id = pi.prize_id "
        "WHERE pi.available_date = :d AND p.name IN ('always-A','added-C') ORDER BY p.name",
        {'d': start + timedelta(days=419)}
    )
    assert [(r['name'], r['iq'], r['rem'], r['lim']) for r in last] == [
        ('added-C', 7, 7, 3), ('always-A', 10, 10, 2)]


def test_wheel_recovers_after_the_laptop_was_off_for_months(app, make_prize, fake_today):
    start = _RealDate.today()
    fake_today.current = start
    p = make_prize(quantity=4, daily_limit=2, name='gap-prize')
    with app.app_context():
        Inventory.create_for_prize_range(p['id'], start_date=start, days=30,
                                         initial_quantity=4, daily_limit=2)

    back = start + timedelta(days=200)  # nothing touched the app in between
    fake_today.current = back
    assert 'gap-prize' in _names_available(app, back)
