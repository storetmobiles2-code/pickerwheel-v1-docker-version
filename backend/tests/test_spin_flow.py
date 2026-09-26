"""
Spin flow: /api/pre-spin and /api/spin.

Happy path:
  - pre-spin returns a real prize when inventory exists
  - spin consumes exactly one unit and records one transaction
  - repeated spins respect the daily_limit
Failure path:
  - pre-spin with nothing in stock returns a clean "no prizes" error, not a 500
  - spin is rejected for a prize with no remaining inventory
  - spin is rejected once daily_limit is reached, even with stock left
  - spin is rejected for a prize_id that doesn't exist
  - spin request missing prize_id is rejected with 400
  - two concurrent spins against the last unit: exactly one succeeds,
    inventory never goes negative (row-locking regression test)
"""
import threading

from app.database import execute_sql


def test_prespin_happy_path_returns_a_real_prize(client, wheel_of_prizes):
    resp = client.post('/api/pre-spin', json={'user_id': 'happy-path-user'})
    assert resp.status_code == 200
    body = resp.get_json()
    assert body['success'] is True
    assert body['selected_prize']['id'] in [p['id'] for p in wheel_of_prizes.values()]


def test_prespin_with_no_inventory_fails_cleanly(client):
    # No prizes seeded at all for this test
    resp = client.post('/api/pre-spin', json={'user_id': 'empty-wheel-user'})
    assert resp.status_code == 400
    body = resp.get_json()
    assert body['success'] is False
    assert 'error' in body


def test_spin_happy_path_consumes_one_unit_and_records_transaction(client, wheel_of_prizes):
    prize = wheel_of_prizes['common_a']
    resp = client.post('/api/spin', json={'user_id': 'spinner-1', 'prize_id': prize['id']})
    assert resp.status_code == 200
    body = resp.get_json()
    assert body['success'] is True
    assert body['prize']['id'] == prize['id']

    remaining = execute_sql(
        'SELECT remaining_quantity FROM prize_inventory WHERE prize_id = :id',
        {'id': prize['id']}
    )[0]['remaining_quantity']
    assert remaining == 9  # started at 10

    tx_count = execute_sql(
        "SELECT COUNT(*) AS n FROM transactions WHERE prize_id = :id AND transaction_type = 'win'",
        {'id': prize['id']}
    )[0]['n']
    assert tx_count == 1


def test_spin_fails_when_prize_has_zero_remaining(client, make_prize):
    prize = make_prize(quantity=0, daily_limit=5)
    resp = client.post('/api/spin', json={'user_id': 'unlucky-user', 'prize_id': prize['id']})
    assert resp.status_code == 400
    assert resp.get_json()['success'] is False


def test_spin_fails_once_daily_limit_is_reached(client, make_prize):
    prize = make_prize(quantity=10, daily_limit=1)
    first = client.post('/api/spin', json={'user_id': 'user-a', 'prize_id': prize['id']})
    assert first.status_code == 200

    second = client.post('/api/spin', json={'user_id': 'user-b', 'prize_id': prize['id']})
    assert second.status_code == 400
    assert second.get_json()['success'] is False

    # Inventory still has stock left - it's the daily limit that blocked it,
    # not depletion. Confirms the two checks are independent.
    remaining = execute_sql(
        'SELECT remaining_quantity FROM prize_inventory WHERE prize_id = :id',
        {'id': prize['id']}
    )[0]['remaining_quantity']
    assert remaining == 9


def test_spin_fails_for_nonexistent_prize_id(client, wheel_of_prizes):
    resp = client.post('/api/spin', json={'user_id': 'ghost-user', 'prize_id': 999999})
    assert resp.status_code == 400
    assert resp.get_json()['success'] is False


def test_spin_fails_when_prize_id_missing(client, wheel_of_prizes):
    resp = client.post('/api/spin', json={'user_id': 'no-prize-id-user'})
    assert resp.status_code == 400
    assert resp.get_json()['success'] is False


def test_concurrent_spins_on_last_unit_only_one_wins(app, make_prize):
    """Regression test for the row-locking guarantee verified manually
    earlier in the project: two simultaneous spins against a prize with
    exactly one unit left must never both succeed."""
    prize = make_prize(quantity=1, daily_limit=5)

    results = []

    def do_spin(user_id):
        with app.test_client() as c:
            resp = c.post('/api/spin', json={'user_id': user_id, 'prize_id': prize['id']})
            results.append(resp.get_json()['success'])

    t1 = threading.Thread(target=do_spin, args=('race-a',))
    t2 = threading.Thread(target=do_spin, args=('race-b',))
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    assert sorted(results) == [False, True]

    remaining = execute_sql(
        'SELECT remaining_quantity FROM prize_inventory WHERE prize_id = :id',
        {'id': prize['id']}
    )[0]['remaining_quantity']
    assert remaining == 0  # never went negative

    tx_count = execute_sql(
        "SELECT COUNT(*) AS n FROM transactions WHERE prize_id = :id AND transaction_type = 'win'",
        {'id': prize['id']}
    )[0]['n']
    assert tx_count == 1


def test_disabled_prize_is_never_selected_by_prespin(client, make_prize):
    make_prize(quantity=10, daily_limit=5, is_enabled=False)
    resp = client.post('/api/pre-spin', json={'user_id': 'disabled-prize-user'})
    # No enabled prizes exist, so pre-spin must fail rather than
    # returning a disabled prize
    assert resp.status_code == 400
    assert resp.get_json()['success'] is False


def test_spin_rejects_a_prize_disabled_after_prespin_selected_it(client, make_prize):
    """Regression test: pre-spin correctly excludes disabled prizes, but
    the wheel animation takes several seconds between pre-spin picking a
    prize and spin actually awarding it. If an admin disables that prize
    (or its whole budget tier, via the master toggle) during that
    window, consume_prize() used to have no reason to refuse - it only
    checked stock and daily_limit, never is_enabled - so the disabled
    prize was still awarded. Simulates that race directly: pre-spin
    would have selected this prize while it was enabled; by the time
    /spin fires, it no longer is."""
    prize = make_prize(quantity=10, daily_limit=5, is_enabled=True)

    execute_sql('UPDATE prizes SET is_enabled = FALSE WHERE id = :id', {'id': prize['id']})

    resp = client.post('/api/spin', json={'user_id': 'race-user', 'prize_id': prize['id']})
    assert resp.status_code == 400
    assert resp.get_json()['success'] is False

    remaining = execute_sql(
        'SELECT remaining_quantity FROM prize_inventory WHERE prize_id = :id',
        {'id': prize['id']}
    )[0]['remaining_quantity']
    assert remaining == 10  # untouched - no award happened

    tx_count = execute_sql(
        "SELECT COUNT(*) AS n FROM transactions WHERE prize_id = :id AND transaction_type = 'win'",
        {'id': prize['id']}
    )[0]['n']
    assert tx_count == 0
