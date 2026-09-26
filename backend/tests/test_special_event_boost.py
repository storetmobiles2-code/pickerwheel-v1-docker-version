"""
Special-event weight_multiplier boosts on spin selection.

This is inherently probabilistic (selection is weighted random), so
instead of asserting an exact outcome, the happy-path test asserts a
boosted prize is picked dramatically more often than an unboosted peer
with identical inventory, over a large sample - matching how this was
manually verified earlier in the project (a 20x boost picked ~17-20x
more often over 3000 samples).

Failure/edge path:
  - a boost on a prize with zero remaining inventory has no effect
    (it must never be selectable regardless of how boosted it is)
"""
from datetime import datetime, timedelta, timezone
from collections import Counter

from app.services import SpinService
from app.database import execute_sql


def _activate_boost(app, prize_id, multiplier):
    # Must be timezone-AWARE: the DB session's TZ is Asia/Kolkata, and a
    # naive datetime gets silently interpreted as IST wall-clock time
    # rather than UTC, shifting the stored instant by 5:30 - enough to
    # make an event that should be "active now" register as already
    # ended. This bit our first draft of this exact test.
    now = datetime.now(timezone.utc)
    with app.app_context():
        event = execute_sql("""
            INSERT INTO special_events (name, description, event_type, start_datetime, end_datetime, is_active)
            VALUES ('Boost Test', 'test', 'promotion', :start, :end, TRUE)
            RETURNING id
        """, {'start': now - timedelta(hours=1), 'end': now + timedelta(hours=1)})[0]['id']
        execute_sql("""
            INSERT INTO special_event_prizes (special_event_id, prize_id, boost_enabled, weight_multiplier)
            VALUES (:event_id, :prize_id, TRUE, :multiplier)
        """, {'event_id': event, 'prize_id': prize_id, 'multiplier': multiplier})
        return event


def test_boosted_prize_is_selected_far_more_often_than_unboosted_peers(app, make_prize):
    boosted = make_prize(category_id=3, quantity=50, daily_limit=50, name='Boosted')
    peers = [make_prize(category_id=3, quantity=50, daily_limit=50, name=f'Peer {i}') for i in range(3)]
    _activate_boost(app, boosted['id'], multiplier=20.0)

    with app.app_context():
        counts = Counter()
        for _ in range(1500):
            prize = SpinService.select_winning_prize(event_id=1, user_identifier=None)
            if prize and prize['category_name'] == 'common':
                counts[prize['prize_id']] += 1

    boosted_count = counts[boosted['id']]
    peer_counts = [counts[p['id']] for p in peers]
    avg_peer_count = sum(peer_counts) / len(peer_counts) if peer_counts else 1

    assert boosted_count > avg_peer_count * 5, (
        f'boosted={boosted_count} avg_peer={avg_peer_count} - expected the '
        'boosted prize to dominate selection'
    )


def test_boost_on_depleted_prize_never_selects_it(app, make_prize):
    depleted = make_prize(category_id=3, quantity=0, daily_limit=5, name='Depleted Boosted')
    healthy = make_prize(category_id=3, quantity=10, daily_limit=5, name='Healthy Unboosted')
    _activate_boost(app, depleted['id'], multiplier=999.0)  # near the column's max (NUMERIC(5,2)), must still not matter

    with app.app_context():
        for _ in range(50):
            prize = SpinService.select_winning_prize(event_id=1, user_identifier=None)
            assert prize is not None
            assert prize['prize_id'] != depleted['id']
            assert prize['prize_id'] == healthy['id']
