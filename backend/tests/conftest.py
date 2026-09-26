"""
Shared pytest fixtures for the backend test suite.

Runs against a real PostgreSQL database (TestingConfig -> pickerwheel_test,
see backend/app/config.py), never the development database - these tests
truncate tables between every test, so pointing this at the wrong
database would destroy real data.

Setup (one-time, see backend/tests/README.md for the exact commands):
  1. Create the pickerwheel_test database on the same Postgres server.
  2. Apply backend/schema/*.sql to it, in order.
  3. pip install -r backend/requirements-test.txt
  4. Run with FLASK_ENV=testing (set automatically by the `app` fixture).
"""
import os
import sys
from datetime import date, timedelta

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

os.environ.setdefault('FLASK_ENV', 'testing')

from app import create_app, socketio as flask_socketio  # noqa: E402
from app.database import execute_sql, execute_transaction  # noqa: E402

ADMIN_PASSWORD = 'myTAdmin2025'  # matches TestingConfig -> Config default

# Tables that accumulate per-test data. Order matters for FK dependencies
# (children before parents) - TRUNCATE ... CASCADE would work too, but
# listing them explicitly makes it obvious what a test run touches.
_TRUNCATE_TABLES = [
    'audit_log',
    'transactions',
    'guaranteed_wins',
    'special_event_prizes',
    'special_events',
    'date_template_assignments',
    'template_prizes',
    'daily_prize_templates',
    'prize_inventory',
    'prizes',
]


@pytest.fixture(scope='session')
def app():
    """One Flask app for the whole test session (see module docstring:
    the DB engine/session in app.database are process-level globals, so
    creating the app more than once is unnecessary and just re-registers
    Socket.IO handlers for no benefit)."""
    flask_app = create_app('testing')
    if 'pickerwheel_test' not in flask_app.config['DATABASE_URL']:
        pytest.exit(
            'Refusing to run: TestingConfig is not pointed at pickerwheel_test '
            f"(got {flask_app.config['DATABASE_URL']!r}). Check config.py / "
            'TEST_DATABASE_URL before running tests against a real database.'
        )
    return flask_app


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def socketio_client(app):
    """A Flask-SocketIO test client, for exercising the WebSocket admin
    handlers without a real network connection."""
    return flask_socketio.test_client(app)


@pytest.fixture(autouse=True)
def db_reset(app):
    """Runs before every test: wipes per-test tables so tests can't leak
    state into each other, regardless of order. prize_categories and
    events are seed data (from schema/004_seed_data.sql) and are never
    truncated."""
    with app.app_context():
        for table in _TRUNCATE_TABLES:
            execute_sql(f'TRUNCATE TABLE {table} RESTART IDENTITY CASCADE')
    yield


@pytest.fixture()
def today():
    return date.today()


@pytest.fixture()
def make_prize(app):
    """Factory fixture: make_prize(category_id=3, quantity=10, daily_limit=5)
    -> a prize dict with today's inventory already created, ready to spin."""
    def _make(category_id=3, name=None, quantity=10, daily_limit=5,
              is_enabled=True, target_date=None):
        with app.app_context():
            from app.models import Prize, Inventory
            target_date = target_date or date.today()
            label = name or f'Test Prize {category_id}-{quantity}-{daily_limit}'
            prize = Prize.create(label, category_id, emoji='🎁')
            if not is_enabled:
                Prize.toggle_enabled(prize['id'], False)
            Inventory.create_for_prize(
                prize['id'], event_id=1, target_date=target_date,
                initial_quantity=quantity, daily_limit=daily_limit
            )
            return prize
    return _make


@pytest.fixture()
def wheel_of_prizes(make_prize):
    """A small realistic wheel: one of each category, all in stock, so
    happy-path spin tests have real choices to land on."""
    return {
        'ultra_rare': make_prize(category_id=1, quantity=2, daily_limit=1),
        'rare': make_prize(category_id=2, quantity=5, daily_limit=2),
        'common_a': make_prize(category_id=3, quantity=10, daily_limit=5),
        'common_b': make_prize(category_id=3, quantity=10, daily_limit=5),
    }


@pytest.fixture()
def admin_headers():
    return {'X-Admin-Password': ADMIN_PASSWORD}


@pytest.fixture()
def wrong_admin_headers():
    return {'X-Admin-Password': 'definitely-not-the-password'}
