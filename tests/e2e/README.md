# Frontend E2E tests

Playwright tests that drive a real Chromium browser against a live,
already-running PickerWheel instance. See `../../TEST_PLAN.md` for the
full scenario list.

**These hit the live dev stack, not an isolated database.** A "happy
path" spin test consumes real inventory, the same as a real customer
spinning the wheel would. Run them against a dev/staging instance you're
fine mutating, not production.

## Setup

```bash
cd tests/e2e
npm install
npx playwright install chromium   # only needed once per machine
```

## Running

Make sure the app is up first (`docker compose up -d` from the repo
root), then:

```bash
cd tests/e2e
npx playwright test              # headless
npx playwright test --headed     # watch it click through the browser
npx playwright test specs/customer-wheel.spec.js
```

Point at a different running instance with `PICKERWHEEL_BASE_URL`:

```bash
PICKERWHEEL_BASE_URL=http://localhost:9080 npx playwright test
```

## Why the admin suite only covers the login failure path

Testing the logged-in admin UI (or the category-dropdown regression fix
specifically) needs the real admin password. This project has a
standing rule against embedding that password in any file or command
run through an automated tool, even for testing - so `admin-login.spec.js`
only covers the wrong-password/empty-password failure path. The
happy-path login itself is a single `fetch` + two `style.display`
toggles (see `login()` in `frontend/admin.html`) and was verified by
direct code and data inspection instead of a browser test.

If you're running this yourself and are fine providing the real
password locally, you can extend `admin-login.spec.js` with a happy-path
test that fills `#adminPassword` and asserts `#adminContent` gets the
`show` class - just don't commit the password.
