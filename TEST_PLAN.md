# PickerWheel Test Plan

Identifies the happy-path and failure-path scenarios covered by the
automated test suite, and what's deliberately out of scope for now.
Two suites, run separately:

- **Backend integration tests** (`backend/tests/`, pytest) - hit the
  real Flask app + a real, isolated PostgreSQL database
  (`pickerwheel_test`) through the Flask test client and the
  Flask-SocketIO test client. Fast (~10s for 80 tests), fully isolated
  from the dev database.
- **Frontend E2E tests** (`tests/e2e/`, Playwright) - drive a real
  Chromium browser against a live, already-running instance (the
  docker-compose dev stack). Slower, exercises real HTTP + WebSocket +
  DOM + CSS animation behavior the backend suite can't see.

Run instructions are in `backend/tests/README.md` and `tests/e2e/README.md`.

## Why these two layers, and not more

This app has ~50 backend routes and a large, hand-rolled frontend with
no build step or component framework. Full exhaustive coverage of every
route and every UI interaction would be a multi-week project on its
own. This plan instead prioritizes:

1. Every area that had a **real, shipped bug this project already hit**
   (see the git history: guaranteed-win atomicity, the queue-jam bug,
   trigger-now not awarding anything, non-atomic writes, the reversed
   category mapping, missing WebSocket auth) - these get regression
   tests, not just happy-path smoke checks.
2. The **money-path**: spin selection, inventory consumption, daily
   limits, and anything that could double-award or lose a prize.
3. A **representative sample** of routine CRUD (prizes, templates,
   date assignments) - one or two happy/failure cases each, not every
   permutation of every field.

Explicitly **not** covered yet (documented, not silently skipped):
- Every admin route (there are ~50; see `backend/app/routes/admin.py`).
  Untested: theme reset endpoints, most GET-by-id/list routes, the
  `date-assignments` GET routes, `guaranteed-wins/expire-old`.
- Templates/date-assignment integration with actual spin selection -
  this was deliberately deferred as a product decision in
  `ADMIN_PANEL_BUGS.md` (#9), so there's nothing correct yet to write a
  regression test against.
- Admin panel happy-path login and any authenticated admin UI flow in
  Playwright - doing so needs the real admin password, which this
  session has a standing restriction against embedding in any file or
  command it executes. Only the login *failure* path is covered in
  `admin-login.spec.js`. The category-dropdown regression fix (loading
  categories from the API instead of a hardcoded, reversed mapping) was
  verified by direct code and data inspection instead, not by E2E.
- Load/performance testing, cross-browser testing (Playwright config
  only runs Chromium), accessibility testing.

## Backend scenarios (`backend/tests/`)

### Spin flow (`test_spin_flow.py`)
| Scenario | Type |
|---|---|
| Pre-spin returns a real prize when inventory exists | Happy |
| Spin consumes exactly one unit and records one transaction | Happy |
| Pre-spin with nothing in stock fails cleanly (400, not 500) | Failure |
| Spin rejected when a prize has zero remaining inventory | Failure |
| Spin rejected once `daily_limit` is reached, even with stock left | Failure |
| Spin rejected for a `prize_id` that doesn't exist | Failure |
| Spin rejected when `prize_id` is missing from the request | Failure |
| Two concurrent spins on the last unit: exactly one succeeds, inventory never negative | Failure (race) |
| A disabled prize is never returned by pre-spin | Failure |

### Guaranteed wins (`test_guaranteed_wins.py`)
| Scenario | Type |
|---|---|
| Create -> pre-spin offers it -> spin awards it atomically | Happy |
| Creating a next-spin win for an already-depleted prize is rejected | Failure |
| Creating a next-spin win for a prize already at its daily limit is rejected | Failure |
| A prize depleted *after* scheduling leaves the win `pending`, no phantom transaction (the original atomicity bug) | Failure |
| Replaying an already-triggered `guaranteed_win_id` is rejected, no bonus prize | Failure |
| An unfulfillable pending win doesn't block other spins from happening (the queue-jam bug) | Failure |
| "Trigger Now" actually awards the prize (inventory + transaction) | Happy |
| "Trigger Now" on an already-processed win returns 404 | Failure |
| Cancelling a pending win works, and it's never offered afterward | Happy |
| Creating a win without `prize_id` is rejected | Failure |

### Admin authentication (`test_admin_auth.py`)
| Scenario | Type |
|---|---|
| A representative sample of admin routes accepts the correct password | Happy |
| ...rejects a missing password (401) | Failure |
| ...rejects a wrong password (401) | Failure |
| WebSocket `admin:join` accepts the correct password | Happy |
| WebSocket `admin:join` rejects missing/wrong password | Failure |
| WebSocket `admin:add_prize` rejects a request with no password, and creates nothing | Failure |

### Prizes & inventory (`test_admin_prizes_inventory.py`)
| Scenario | Type |
|---|---|
| Add-prize honors the admin-entered quantity/daily_limit | Happy |
| Add-prize rejects missing name/category, negative or non-numeric quantity | Failure |
| Toggle/delete a prize | Happy |
| Toggle a nonexistent prize returns 404 | Failure |
| Set-inventory updates quantity + daily_limit together in one call | Happy |
| Set-inventory rejects negative/non-numeric values, and requires at least one field | Failure |
| Set-inventory on a prize with no inventory row returns 404 | Failure |
| Replenish resets remaining_quantity to initial_quantity | Happy |

### Special events (`test_admin_special_events.py`)
| Scenario | Type |
|---|---|
| Create with a theme and linked prizes lands atomically | Happy |
| A bad `prize_id` in the create payload rolls back the *entire* event | Failure |
| An invalid `event_type` is rejected, nothing created | Failure |
| The UI-offered types (`national_holiday`, `custom`) are accepted by the DB constraint | Happy |
| Missing required fields (name/dates) rejected | Failure |
| An invalid `start_datetime` on update is rejected (400), not silently written through | Failure |

### Reset & templates (`test_admin_reset_and_templates.py`)
| Scenario | Type |
|---|---|
| Reset Daily Wins wipes today's transactions, restores inventory, writes one audit_log row, atomically | Happy |
| Reset Daily Wins requires the exact confirmation string / the field at all | Failure |
| Populate-all fills a template with every active prize | Happy |
| A valid date-range assignment succeeds (inclusive count) | Happy |
| A date range with start after end is rejected | Failure |
| A date range over 366 days is rejected | Failure |

### Special-event weight boosts (`test_special_event_boost.py`)
| Scenario | Type |
|---|---|
| A boosted prize is selected far more often than unboosted peers with identical inventory (statistical, 1500 samples) | Happy |
| A boost on a depleted prize never makes it selectable, no matter how high the multiplier | Failure/edge |

### Public API (`test_api_public.py`)
| Scenario | Type |
|---|---|
| `/api/health`, `/api/categories` | Happy |
| `/api/prizes/wheel-display` includes disabled prizes (shown, not spinnable) | Happy |
| `/api/config` reflects an active special event's theme; omits it when none is active | Happy |
| `/api/prizes/wheel-display` with a malformed date query param fails cleanly, not a raw 500 | Failure |

## Frontend E2E scenarios (`tests/e2e/specs/`)

### Customer wheel page (`customer-wheel.spec.js`)
| Scenario | Type |
|---|---|
| Page loads, wheel renders with segments, Neon is the default | Happy |
| How It Works floats bottom-right on desktop, doesn't overlap the wheel | Happy |
| How It Works reverts to a static stacked card on a narrow viewport | Happy |
| Spinning the wheel end-to-end awards a real prize and shows the modal | Happy |
| Sound toggle persists across a reload | Happy |
| Design mode toggle switches to Material and persists across a reload | Happy |
| A spin request for a nonexistent prize_id is rejected cleanly (400, JSON error) | Failure |

### Admin login (`admin-login.spec.js`)
| Scenario | Type |
|---|---|
| Wrong password shows an error, never reveals admin content | Failure |
| Empty password doesn't crash the login flow | Failure |
