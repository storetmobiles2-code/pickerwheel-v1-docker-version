# Backend tests

Integration tests against a real Flask app + a real, isolated
PostgreSQL database. See `../../TEST_PLAN.md` for the full scenario
list and what's deliberately not covered yet.

**Never point these at the development database.** `db_reset` in
`conftest.py` truncates tables before every single test.

## One-time setup

Run these against the same Postgres server the dev stack uses (the
`postgres` service in `docker-compose.yml`):

```bash
docker exec pickerwheel-db psql -U pickerwheel -d pickerwheel -c \
  "CREATE DATABASE pickerwheel_test OWNER pickerwheel;"

for f in backend/schema/*.sql; do
  docker exec -i pickerwheel-db psql -U pickerwheel -d pickerwheel_test \
    -v ON_ERROR_STOP=1 < "$f"
done
```

Install test dependencies (in addition to `backend/requirements.txt`):

```bash
docker exec pickerwheel-app pip install -r backend/requirements-test.txt
```

## Running

From inside the app container (it already has `DB_HOST=postgres` etc.
set, matching the test database's host/user/password):

```bash
docker exec -e FLASK_ENV=testing pickerwheel-app python3 -m pytest tests/ -v
```

`FLASK_ENV=testing` selects `TestingConfig` in `app/config.py`, which
points `DATABASE_URL` at `pickerwheel_test` - the `app` fixture
actively refuses to run (`pytest.exit`) if that database name isn't in
the resolved connection string, as a last-resort guard against ever
running this against `pickerwheel`.

Run a single file or test:

```bash
docker exec -e FLASK_ENV=testing pickerwheel-app python3 -m pytest tests/test_spin_flow.py -v
docker exec -e FLASK_ENV=testing pickerwheel-app python3 -m pytest tests/test_spin_flow.py::test_spin_fails_when_prize_has_zero_remaining -v
```

## Notes for adding tests

- Use the `make_prize(category_id=..., quantity=..., daily_limit=...)`
  fixture to seed a spinnable prize with today's inventory row rather
  than inserting rows by hand - it keeps tests readable and consistent.
- `wheel_of_prizes` gives you one prize per category if a test just
  needs "a working wheel" and doesn't care about specifics.
- `admin_headers` / `wrong_admin_headers` are ready-made
  `X-Admin-Password` header dicts.
- If a test needs a timestamp inserted via raw SQL (not through a
  route that parses an ISO string itself), use a timezone-**aware**
  Python datetime (`datetime.now(timezone.utc)`), never
  `datetime.utcnow()`. The test database session's timezone is
  Asia/Kolkata; a naive datetime gets silently interpreted as IST wall
  clock instead of UTC, which can shift the stored instant by 5:30 and
  make an "active now" row register as already expired. This bit the
  first draft of `test_special_event_boost.py`.
