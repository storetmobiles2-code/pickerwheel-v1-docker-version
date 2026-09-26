"""Sanity check that the test harness itself works before trusting any
other test file: right database, clean state, fixtures wire up."""


def test_health_endpoint(client):
    resp = client.get('/api/health')
    assert resp.status_code == 200
    assert resp.get_json()['status'] == 'healthy'


def test_db_is_the_test_database(app):
    assert 'pickerwheel_test' in app.config['DATABASE_URL']


def test_db_reset_gives_a_clean_slate(app):
    from app.database import execute_sql
    with app.app_context():
        count = execute_sql('SELECT COUNT(*) AS n FROM prizes')[0]['n']
    assert count == 0


def test_make_prize_fixture_creates_spinnable_inventory(make_prize, app):
    prize = make_prize(category_id=3, quantity=7, daily_limit=3)
    from app.database import execute_sql
    with app.app_context():
        row = execute_sql(
            'SELECT remaining_quantity, daily_limit FROM prize_inventory WHERE prize_id = :id',
            {'id': prize['id']}
        )[0]
    assert row['remaining_quantity'] == 7
    assert row['daily_limit'] == 3
