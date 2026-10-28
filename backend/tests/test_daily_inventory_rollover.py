"""
Daily inventory rollover: Inventory.ensure_for_date().

Inventory used to exist only for the 31 days the seed script created up
front, so on the first day after that the wheel returned "No prizes
available" for every spin. A day with no rows now gets them created on
first use, carried over from each prize's previous day.

Happy path:
  - pre-spin on a day with no rows yet creates them and awards a prize
  - the carried-over row starts full and keeps the previous daily_limit
  - the most recent earlier day is the one copied
  - the admin inventory view creates an upcoming day so it can be adjusted
Failure path:
  - a row that already exists for the day is left untouched
  - a prize with no inventory history is not stocked with made-up numbers
  - past days and days beyond the 30-day window are never created
  - repeated requests don't duplicate the day's rows
"""
from datetime import date, timedelta

from app.database import execute_sql
from app.models import Inventory, Prize


def _move_inventory_to(prize_id, day):
    execute_sql(
        'UPDATE prize_inventory SET available_date = :day WHERE prize_id = :id',
        {'day': day, 'id': prize_id}
    )


def _rows_on(prize_id, day):
    return execute_sql(
        """SELECT initial_quantity, remaining_quantity, daily_limit
           FROM prize_inventory WHERE prize_id = :id AND available_date = :day""",
        {'id': prize_id, 'day': day}
    ) or []


def test_prespin_creates_todays_inventory_from_previous_day(client, make_prize):
    yesterday = date.today() - timedelta(days=1)
    prize = make_prize(quantity=10, daily_limit=5, target_date=yesterday)
    execute_sql(
        'UPDATE prize_inventory SET remaining_quantity = 3 WHERE prize_id = :id',
        {'id': prize['id']}
    )

    resp = client.post('/api/pre-spin', json={'user_id': 'rollover-user'})

    assert resp.status_code == 200
    assert resp.get_json()['selected_prize']['id'] == prize['id']
    # Starts full (not yesterday's leftover 3) with yesterday's daily_limit
    assert _rows_on(prize['id'], date.today()) == [
        {'initial_quantity': 10, 'remaining_quantity': 10, 'daily_limit': 5}
    ]


def test_spin_after_rollover_consumes_from_the_new_day(client, make_prize):
    prize = make_prize(quantity=4, daily_limit=2,
                       target_date=date.today() - timedelta(days=1))

    client.post('/api/pre-spin', json={'user_id': 'rollover-spinner'})
    resp = client.post('/api/spin', json={'user_id': 'rollover-spinner', 'prize_id': prize['id']})

    assert resp.status_code == 200
    assert _rows_on(prize['id'], date.today())[0]['remaining_quantity'] == 3


def test_copies_the_most_recent_earlier_day(app, client, make_prize):
    today = date.today()
    prize = make_prize(quantity=10, daily_limit=5, target_date=today - timedelta(days=3))
    with app.app_context():
        Inventory.create_for_prize(prize['id'], 1, today - timedelta(days=1),
                                   initial_quantity=6, daily_limit=2)

    client.get('/api/prizes/wheel-display')

    assert _rows_on(prize['id'], today) == [
        {'initial_quantity': 6, 'remaining_quantity': 6, 'daily_limit': 2}
    ]


def test_admin_inventory_view_creates_an_upcoming_day(client, admin_headers, make_prize):
    prize = make_prize(quantity=5, daily_limit=2)
    tomorrow = date.today() + timedelta(days=1)

    resp = client.get(f'/api/admin/inventory?date={tomorrow.isoformat()}', headers=admin_headers)

    assert resp.status_code == 200
    assert [i['prize_id'] for i in resp.get_json()['inventory']] == [prize['id']]
    assert _rows_on(prize['id'], tomorrow) == [
        {'initial_quantity': 5, 'remaining_quantity': 5, 'daily_limit': 2}
    ]


def test_existing_row_for_the_day_is_left_untouched(app, client, make_prize):
    today = date.today()
    prize = make_prize(quantity=10, daily_limit=5, target_date=today - timedelta(days=1))
    with app.app_context():
        Inventory.create_for_prize(prize['id'], 1, today, initial_quantity=4, daily_limit=1)
    execute_sql(
        'UPDATE prize_inventory SET remaining_quantity = 2 WHERE prize_id = :id AND available_date = :day',
        {'id': prize['id'], 'day': today}
    )

    client.post('/api/pre-spin', json={'user_id': 'existing-row-user'})

    assert _rows_on(prize['id'], today) == [
        {'initial_quantity': 4, 'remaining_quantity': 2, 'daily_limit': 1}
    ]


def test_prize_without_inventory_history_is_not_stocked(app, client):
    with app.app_context():
        prize = Prize.create('Never Stocked', 3, emoji='🎁')

    resp = client.post('/api/pre-spin', json={'user_id': 'no-history-user'})

    assert resp.status_code == 400
    assert _rows_on(prize['id'], date.today()) == []


def test_past_and_out_of_window_days_are_never_created(client, make_prize):
    today = date.today()
    prize = make_prize(target_date=today - timedelta(days=5))
    past = today - timedelta(days=2)
    too_far = today + timedelta(days=31)

    client.get(f'/api/prizes/available?date={past.isoformat()}')
    client.get(f'/api/prizes/available?date={too_far.isoformat()}')

    assert _rows_on(prize['id'], past) == []
    assert _rows_on(prize['id'], too_far) == []


def test_repeated_requests_do_not_duplicate_the_days_rows(client, make_prize):
    prize = make_prize(target_date=date.today() - timedelta(days=1))

    for _ in range(3):
        client.get('/api/prizes/wheel-display')

    assert len(_rows_on(prize['id'], date.today())) == 1
