"""
Guaranteed wins: creation, atomic fulfillment, and the admin lifecycle
routes. This is the area with the most history of real bugs this
project has hit, so these are written as regression tests for each one,
not just fresh happy-path coverage.

Happy path:
  - creating a next-spin guaranteed win, then spinning, awards it
    atomically (inventory + transaction + win status all move together)
  - "Trigger Now" actually awards the prize (regression: it used to only
    flip a status flag with nothing to show for it)
  - cancelling a pending win works
Failure path:
  - creating a next-spin win for a prize with no stock is rejected up
    front (regression: this is what let bug below happen in the first
    place)
  - a prize that sells out normally AFTER a guaranteed win was scheduled
    for it leaves the win pending, not silently spent (regression: this
    was the original atomicity bug - trigger committed before consume)
  - replaying an already-triggered guaranteed_win_id is rejected, not
    treated as a free bonus prize
  - an unfulfillable pending win doesn't block every other spin from
    happening (regression: the "queue jam" bug)
  - trigger-now on an already-processed win returns 404, not a crash
"""
from app.database import execute_sql


def _create_guaranteed_win(client, admin_headers, prize_id, **overrides):
    payload = {'prize_id': prize_id, 'reason': 'test'}
    payload.update(overrides)
    return client.post('/api/admin/guaranteed-wins', json=payload, headers=admin_headers)


def test_guaranteed_win_happy_path_is_atomic(client, admin_headers, make_prize):
    prize = make_prize(quantity=5, daily_limit=5)
    create_resp = _create_guaranteed_win(client, admin_headers, prize['id'])
    assert create_resp.status_code == 200
    win_id = create_resp.get_json()['win']['id']

    pre = client.post('/api/pre-spin', json={'user_id': 'gw-user'})
    assert pre.get_json()['is_guaranteed'] is True
    assert pre.get_json()['guaranteed_win_id'] == win_id

    spin = client.post('/api/spin', json={
        'user_id': 'gw-user', 'prize_id': prize['id'], 'guaranteed_win_id': win_id
    })
    assert spin.status_code == 200
    assert spin.get_json()['was_guaranteed'] is True

    win_row = execute_sql(
        'SELECT status, triggered_count FROM guaranteed_wins WHERE id = :id', {'id': win_id}
    )[0]
    assert win_row['status'] == 'triggered'
    assert win_row['triggered_count'] == 1

    remaining = execute_sql(
        'SELECT remaining_quantity FROM prize_inventory WHERE prize_id = :id',
        {'id': prize['id']}
    )[0]['remaining_quantity']
    assert remaining == 4


def test_creating_guaranteed_win_for_depleted_prize_is_rejected(client, admin_headers, make_prize):
    prize = make_prize(quantity=0, daily_limit=5)
    resp = _create_guaranteed_win(client, admin_headers, prize['id'])
    assert resp.status_code in (400, 409)
    assert resp.get_json()['success'] is False


def test_creating_guaranteed_win_at_daily_limit_is_rejected(client, admin_headers, make_prize):
    prize = make_prize(quantity=5, daily_limit=1)
    # use up today's only allowed win normally first
    ok = client.post('/api/spin', json={'user_id': 'first-winner', 'prize_id': prize['id']})
    assert ok.status_code == 200

    resp = _create_guaranteed_win(client, admin_headers, prize['id'])
    assert resp.status_code in (400, 409)
    assert resp.get_json()['success'] is False


def test_prize_depleted_after_scheduling_leaves_guaranteed_win_pending(client, admin_headers, make_prize):
    """The core regression test for the original bug: a guaranteed win
    is created while the prize is available, then a normal spin (or
    direct inventory change) depletes it before the guaranteed win
    fires. The win must stay 'pending' with no phantom transaction -
    never get marked triggered without actually awarding anything."""
    prize = make_prize(quantity=1, daily_limit=5)
    win_id = _create_guaranteed_win(client, admin_headers, prize['id']).get_json()['win']['id']

    # Deplete it out from under the guaranteed win (simulates a race
    # with a normal customer spin, or an admin manually zeroing stock)
    execute_sql(
        'UPDATE prize_inventory SET remaining_quantity = 0 WHERE prize_id = :id',
        {'id': prize['id']}
    )

    spin = client.post('/api/spin', json={
        'user_id': 'gw-user', 'prize_id': prize['id'], 'guaranteed_win_id': win_id
    })
    assert spin.status_code == 400
    assert spin.get_json()['success'] is False

    win_row = execute_sql(
        'SELECT status, triggered_count FROM guaranteed_wins WHERE id = :id', {'id': win_id}
    )[0]
    assert win_row['status'] == 'pending'
    assert win_row['triggered_count'] == 0

    tx_count = execute_sql(
        "SELECT COUNT(*) AS n FROM transactions WHERE prize_id = :id", {'id': prize['id']}
    )[0]['n']
    assert tx_count == 0


def test_prize_disabled_after_scheduling_leaves_guaranteed_win_pending(client, admin_headers, make_prize):
    """Regression test for a real bug: consume_prize() checked stock and
    daily_limit but never is_enabled, so a guaranteed win pointed at a
    prize an admin disabled after scheduling (e.g. via the budget-tier
    master toggle) still fired and awarded it. Same shape as the
    depletion regression above, but for is_enabled instead of stock."""
    prize = make_prize(quantity=5, daily_limit=5)
    win_id = _create_guaranteed_win(client, admin_headers, prize['id']).get_json()['win']['id']

    # Disable it out from under the guaranteed win (simulates an admin
    # disabling the prize, or its whole budget tier, after scheduling)
    execute_sql('UPDATE prizes SET is_enabled = FALSE WHERE id = :id', {'id': prize['id']})

    spin = client.post('/api/spin', json={
        'user_id': 'gw-user', 'prize_id': prize['id'], 'guaranteed_win_id': win_id
    })
    assert spin.status_code == 400
    assert spin.get_json()['success'] is False

    win_row = execute_sql(
        'SELECT status, triggered_count FROM guaranteed_wins WHERE id = :id', {'id': win_id}
    )[0]
    assert win_row['status'] == 'pending'
    assert win_row['triggered_count'] == 0

    tx_count = execute_sql(
        "SELECT COUNT(*) AS n FROM transactions WHERE prize_id = :id", {'id': prize['id']}
    )[0]['n']
    assert tx_count == 0

    remaining = execute_sql(
        'SELECT remaining_quantity FROM prize_inventory WHERE prize_id = :id', {'id': prize['id']}
    )[0]['remaining_quantity']
    assert remaining == 5  # untouched


def test_replaying_a_triggered_guaranteed_win_is_rejected(client, admin_headers, make_prize):
    prize = make_prize(quantity=5, daily_limit=5)
    win_id = _create_guaranteed_win(client, admin_headers, prize['id']).get_json()['win']['id']

    first = client.post('/api/spin', json={
        'user_id': 'gw-user', 'prize_id': prize['id'], 'guaranteed_win_id': win_id
    })
    assert first.status_code == 200

    replay = client.post('/api/spin', json={
        'user_id': 'replay-user', 'prize_id': prize['id'], 'guaranteed_win_id': win_id
    })
    assert replay.status_code == 400
    assert replay.get_json()['success'] is False

    # No bonus prize was handed out on the replay
    remaining = execute_sql(
        'SELECT remaining_quantity FROM prize_inventory WHERE prize_id = :id',
        {'id': prize['id']}
    )[0]['remaining_quantity']
    assert remaining == 4  # only the first spin consumed a unit


def test_unfulfillable_guaranteed_win_does_not_block_other_spins(client, admin_headers, make_prize):
    """Regression test for the queue-jam bug: an unfulfillable pending
    win used to be returned by get_pending_guaranteed_win() forever,
    so every subsequent spin (guaranteed or normal) failed."""
    dead_prize = make_prize(quantity=1, daily_limit=5, name='dead-end prize')
    win_id = _create_guaranteed_win(client, admin_headers, dead_prize['id']).get_json()['win']['id']
    execute_sql(
        'UPDATE prize_inventory SET remaining_quantity = 0 WHERE prize_id = :id',
        {'id': dead_prize['id']}
    )

    healthy_prize = make_prize(quantity=5, daily_limit=5, name='healthy prize')

    pre = client.post('/api/pre-spin', json={'user_id': 'unblocked-user'})
    assert pre.status_code == 200
    body = pre.get_json()
    # Should have skipped the dead guaranteed win and fallen through to
    # the healthy prize via normal selection
    assert body['selected_prize']['id'] == healthy_prize['id']
    assert not body.get('is_guaranteed')

    # The dead win is still visibly pending for an admin to deal with
    win_row = execute_sql(
        'SELECT status FROM guaranteed_wins WHERE id = :id', {'id': win_id}
    )[0]
    assert win_row['status'] == 'pending'


def test_trigger_now_actually_awards_the_prize(client, admin_headers, make_prize):
    """Regression test: trigger-now used to just flip a status flag
    without calling consume_prize, so it never actually created a
    transaction or touched inventory."""
    prize = make_prize(quantity=5, daily_limit=5)
    win_id = _create_guaranteed_win(client, admin_headers, prize['id']).get_json()['win']['id']

    resp = client.post(f'/api/admin/guaranteed-wins/{win_id}/trigger-now',
                        json={'triggered_by': 'admin-test'}, headers=admin_headers)
    assert resp.status_code == 200
    body = resp.get_json()
    assert body['success'] is True
    assert 'transaction_id' in body

    remaining = execute_sql(
        'SELECT remaining_quantity FROM prize_inventory WHERE prize_id = :id',
        {'id': prize['id']}
    )[0]['remaining_quantity']
    assert remaining == 4

    tx_count = execute_sql(
        "SELECT COUNT(*) AS n FROM transactions WHERE prize_id = :id", {'id': prize['id']}
    )[0]['n']
    assert tx_count == 1


def test_trigger_now_on_already_processed_win_returns_404(client, admin_headers, make_prize):
    prize = make_prize(quantity=5, daily_limit=5)
    win_id = _create_guaranteed_win(client, admin_headers, prize['id']).get_json()['win']['id']
    client.post(f'/api/admin/guaranteed-wins/{win_id}/trigger-now',
                json={}, headers=admin_headers)

    resp = client.post(f'/api/admin/guaranteed-wins/{win_id}/trigger-now',
                        json={}, headers=admin_headers)
    assert resp.status_code == 404
    assert resp.get_json()['success'] is False


def test_cancel_pending_guaranteed_win(client, admin_headers, make_prize):
    prize = make_prize(quantity=5, daily_limit=5)
    win_id = _create_guaranteed_win(client, admin_headers, prize['id']).get_json()['win']['id']

    resp = client.post(f'/api/admin/guaranteed-wins/{win_id}/cancel', headers=admin_headers)
    assert resp.status_code == 200

    win_row = execute_sql(
        'SELECT status FROM guaranteed_wins WHERE id = :id', {'id': win_id}
    )[0]
    assert win_row['status'] == 'cancelled'

    # A cancelled win must never be offered to a customer
    pre = client.post('/api/pre-spin', json={'user_id': 'after-cancel-user'})
    assert not pre.get_json().get('is_guaranteed')


def test_create_guaranteed_win_requires_prize_id(client, admin_headers):
    resp = client.post('/api/admin/guaranteed-wins', json={'reason': 'no prize'}, headers=admin_headers)
    assert resp.status_code == 400
    assert resp.get_json()['success'] is False
