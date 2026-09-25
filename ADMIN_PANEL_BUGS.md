# Admin Panel Bugs and Recommended Fixes

Generated: 2026-09-26T02:03:45.226+05:30

Prepared by: AI assistant using Copilot SDK in VS Code

This document collects the admin-panel and scheduling/event/guaranteed-win bugs discovered during the end-to-end review of the PickerWheel application. Each row lists a concise description, severity, files/locations, reproduction notes, impact and recommended fix.

---

| # | Severity | Bug | Files / Locations | Reproduction / Evidence | Impact | Recommended fix (short) |
|---|----------|-----|-------------------|-------------------------|--------|-------------------------|
| 1 | 🔴 Critical | Category ID mapping mismatch: frontend category values map to wrong DB IDs (Common/Rare/Ultra Rare reversed) | frontend/admin.html (lines ~1034), backend/schema/004_seed_data.sql, backend/app/services/inventory_service.py | Create prize using each category → stored category is wrong; inventory defaults wrong | New prizes get wrong default inventory/daily limits; confusion and incorrect odds | Load categories from API in frontend; remove hardcoded IDs; change services to use category name lookup or configuration rather than numeric IDs. |
| 2 | 🔴 Critical | Guaranteed-win replay / depletion bug: quantity=1 guaranteed prize can reappear on subsequent spin even after awarded; final confirm fails with 400 | frontend console logs (provided), backend/app/services/spin_service.py (execute_spin: triggers GuaranteedWin before consume_prize) | Reproduced sequence in logs (first spin awards, second spin shows same, final confirm returns 400) | Players may see same prize twice; inconsistent state, user-facing error | Make guaranteed-win trigger and inventory consumption atomic: call consume_prize first (or in same transaction) and only mark guaranteed as triggered after successful consumption. Add tests for quantity=1 cases and concurrency. |
| 3 | 🔴 Critical | Admin WebSocket mutation handlers unauthenticated | backend/app/routes/websocket.py (admin:join, admin:add_prize, admin:remove_prize, admin:toggle_prize) | Connect a Socket.IO client and call admin events without HTTP auth (review shows no auth checks) | Unauthorized state changes via WebSocket; security breach | Require admin authentication for Socket.IO: session tokens, signed cookies, or token handshake. Reject events from unauthenticated sockets. |
| 4 | 🔴 Critical | Add-prize quantity and daily-limit fields ignored; inventory init uses category defaults | frontend/admin.html (addPrize submit ~1883), backend/app/routes/admin.py (add_prize), backend/app/services/inventory_service.py | Create prize with custom initial_quantity/daily_limit → inventory initialized with category defaults | Admin-entered values not honored; unexpected inventory | Pass admin-entered values through to InventoryService.initialize_inventory_for_prize and make prize + inventory initialization transactional; rollback on failure. |
| 5 | 🔴 Critical | Reset Daily Wins is destructive, non-atomic, and global (not event-scoped) | backend/app/routes/admin.py (reset daily wins ~1533-1609) | Trigger reset → transactions deleted, inventory reset separately; no audit | Loss of historical transactions, inconsistent inventory | Replace with transactional, event-scoped operation that uses compensating adjustments and creates audit records. Require explicit confirmation and admin audit entry. |
| 6 | 🟠 High | Inventory quantity input not validated on backend; may cause 500 | frontend/admin.html (setQuantity, parseInt usage), backend/app/routes/admin.py and InventoryService.set_quantity | Send malformed quantity via API → server type/conversion errors | Server errors, potential exploit surface | Validate integers server-side (int(), check >=0, <=max). Return 400 on invalid input. |
| 7 | 🟠 High | Quantity and daily-limit updates are non-atomic (two-step) | backend/app/routes/admin.py (set_inventory updates quantity then limit separately) | Update both fields; fail on second step → partial state | Inconsistent inventory vs template default | Combine into a single DB transaction; validate inputs first. |
| 8 | 🟠 High | Replenish broadcasts wrong data shape (Prize.get_all instead of date-aware wheel prizes) | backend/app/routes/admin.py (replenish_all), backend/app/services/SpinService | Replenish → connected clients not updated with remaining quantities | Frontend wheels stale until reload | Broadcast SpinService.get_wheel_prizes(event_id, target_date) instead. |
| 9 | 🟠 High | Templates and date assignments don't affect spin selection (runtime ignores template_prizes) | backend/app/models/schedule.py, backend/schema/006_prize_scheduling.sql, backend/app/services/spin_service.py | Modify template quantity/assign dates → spin selections unchanged | Admin changes appear ineffective; customer-facing mismatch | Either: (A) change selection SQL/functions to incorporate template_prizes/date assignments, or (B) materialize templates into prize_inventory rows at assignment time. Choose one authoritative approach and implement atomically. |
| 10 | 🟡 Medium | Daily-limit zero semantics inconsistent between UI and backend | frontend/admin.html (min=1, render uses `prize.daily_limit || 5`), backend allows daily_limit=0, DB daily_limit >=0 | Save daily_limit=0 → UI shows 5 or '∞' | Misrepresentation, editing confusion, unexpected spin behavior | Adopt single policy: `0 = disabled` or `NULL = unlimited`. Render explicitly (e.g., show '0' or '∞') and validate in API. |
| 11 | 🟡 Medium | Template populate/clear operations can leave partial state (not transactionally safe) | backend/app/routes/admin.py (populate-all ~972-1034), schedule.py | Run populate-all and cause an insert failure → template partially populated | Broken templates, inconsistent admin view | Wrap clear-and-populate in DB transaction; pre-validate prize list. |
| 12 | 🟡 Medium | Date-assignment range validation missing (start > end allowed) | backend/app/routes/admin.py (assign_template_to_dates), backend/app/models/schedule.py | Post start_date > end_date → no assignments or weird behavior | Silent failures, admin confusion | Validate ranges at API level; return 400 if invalid. Enforce limits for maximum range. |
| 13 | 🟡 Medium | Special-event types mismatch between UI and DB constraint | frontend/admin.html (eventType options), backend/schema/005_special_events.sql (check constraint) | Create event with `national_holiday`/`custom` → DB check constraint error | Event creation fails with DB error | Map UI types to DB types or extend DB constraint. Validate input in API and return friendly 400 errors. |
| 14 | 🟡 Medium | Special-event boosts (weight_multiplier, quantity_override) not applied by spin selection | backend/app/models/special_event.py (get_boosted_prize_ids), backend/app/services/spin_service.py | Active event with boosted prizes → spin odds unchanged | Events appear to do nothing; ROI lost | Integrate active special events into selection path: apply weight_multiplier to prize weights and honor quantity_override. Update stored functions or selection logic and test. |
| 15 | 🟡 Medium | Event create/update not atomic (create → theme → prizes) | backend/app/routes/admin.py (create_special_event ~481), special_event.py | Fail adding prize after event created → partial event | Incomplete event configuration | Wrap event creation, theme update and prize additions in one transaction. |
| 16 | 🟡 Medium | Invalid datetime parsing in update endpoints silently swallowed | backend/app/routes/admin.py (update_special_event ~572-584) | Submit invalid ISO date → API silently continues or stores invalid value | Database errors or inconsistent values | Return HTTP 400 on parse errors; do not pass invalid strings to model. |
| 17 | ⚪ Low | Admin UI rendering uses innerHTML with unescaped values (XSS risk) | frontend/admin.html (~multiple locations: prize names, event descriptions, templates) | Insert a name with HTML/script → admin UI executes script | Stored XSS risk for admins | Replace innerHTML insertion with DOM/textContent or sanitized escaping function. Avoid inline onclick interpolation. |
| 18 | ⚪ Low | Admin password stored in global JS variable and sent on each request | frontend/admin.html (auth flow ~1513-1565) | Login then inspect window.authPassword → password is plaintext in memory and sent in headers/body | Password exposed to extensions, XSS, proxies | Implement secure session/auth token flow. Remove password retention. |
| 19 | ⚪ Low | Admin WebSocket join event does not verify session | backend/app/routes/websocket.py (admin:join) | Socket event allows joining admin room without proof | Unauthorized clients can subscribe to admin channel | Require server-side session/token verification before joining admin rooms. |
| 20 | ⚪ Low | Frontend uses UTC toISOString for date-only values → business timezone mismatch | frontend/admin.html (date assignment uses toISOString().split('T')[0]) | Create assignment near midnight IST → wrong date used | Template/date assigned to wrong day | Use business timezone handling (server-side conversion or libs) and send explicit local date strings. |

---

Notes and next steps

- The highest priority fixes are those marked Critical (🔴). They should be implemented before any public release or production risk acceptance: category mapping, guaranteed-win replay/atomic consumption, WebSocket auth, prize inventory initialization and the destructive reset.

- The recommended test strategy (unit + PostgreSQL integration + API + small browser smoke tests) is recorded in the session tasks and should run before push to production. The guaranteed-win quantity=1 scenario should be added as an inner-loop regression test.

- For template/scheduling, pick a single authoritative model: either selection-time resolution (SQL/functions read template_prizes) or materialize templates into prize_inventory rows on assignment. The codebase currently mixes both approaches; choose one and adapt services and stored functions accordingly.

- For guaranteed-win fixes: avoid marking guaranteed wins as triggered before inventory is successfully consumed. Prefer an atomic database operation (stored procedure) that both decrements inventory (if available) and marks the guaranteed-win triggered/consumed in the same transaction.

If you'd like, next steps I can take for you:
- Create the ADMIN_PANEL_BUGS.md file in the repository (already created here).
- Open a draft PR with the PRODUCTION_HARDENING.md and ADMIN_PANEL_BUGS.md documented and link the todos.
- Implement a minimal failing unit/integration test for the guaranteed-win replay bug to demonstrate the failure and then implement the code fix and show the test passing.

— AI assistant using Copilot SDK in VS Code

---

## Resolution

**Fixed in [PR #15](https://github.com/storetmobiles2-code/pickerwheel-v1-docker-version/pull/15)** (merged):
- #2 Guaranteed-win replay/depletion bug — `consume_prize()` now completes a guaranteed win atomically with the inventory it consumes.

**Fixed in this branch** (`fix/admin-panel-bugs`):
- #1 Category ID mapping — admin panel now loads categories from `/admin/categories` instead of hardcoded `<option>` values.
- #3, #19 Admin WebSocket mutations unauthenticated — now require the same admin password as the HTTP routes. (No part of the current UI actually calls these events; they were reachable only by a raw Socket.IO client.)
- #4 Add-prize quantity/daily-limit ignored — now passed through to inventory initialization instead of silently using category defaults.
- #5 Reset Daily Wins destructive/non-atomic — now one transaction with an `audit_log` entry. Still testing-only and still deletes transaction history rather than using compensating adjustments; that redesign is a separate, larger decision.
- #6 Inventory quantity not validated — now rejected with 400 instead of risking a 500 or silent bad state.
- #7 Quantity + daily-limit updates non-atomic — now one `UPDATE`.
- #8 Replenish broadcasts wrong data shape — now broadcasts date-aware wheel prizes.
- #10 Daily-limit zero semantics — `0` is now shown and editable as `0` (disabled today), not masked as `5` or hidden behind `min="1"`.
- #11 Template populate/clear non-transactional — now one transaction.
- #12 Date-assignment range validation — rejects `start_date > end_date` and ranges over 366 days.
- #13 Special-event type mismatch — DB constraint extended to include `national_holiday` and `custom`, matching the admin UI's options.
- #15 Event create/update not atomic — create + theme + prizes now land in one transaction; a bad `prize_id` rolls back the whole event instead of leaving a partial one.
- #16 Invalid datetime silently swallowed — now returns 400 instead of passing the raw string through.
- #17 innerHTML XSS — admin-entered free text (prize/event/template names, descriptions, guaranteed-win reason/target) is now escaped before being interpolated into innerHTML or inline `onclick` attributes.
- #20 UTC date-only mismatch — date and datetime-local fields now use local-time formatting instead of `toISOString()`, which reported the wrong calendar day/time for part of every IST business day. (Extended beyond the original bug to also cover `datetime-local` event/guaranteed-win scheduling fields, which had the same root cause.)

**New bugs found and fixed** (surfaced during the guaranteed-win scenario testing that produced PR #15, not in the original list above):
- An unfulfillable pending guaranteed win (prize sold out or hit its daily limit) permanently blocked the spin queue for every customer and every other guaranteed win, since `get_pending_guaranteed_win()` never checked fulfillability. It now skips unfulfillable candidates instead of jamming on them.
- The "Trigger Now" admin action only flipped the guaranteed win's status without ever consuming inventory or creating a transaction - it awarded nothing. It now goes through the same atomic `execute_spin()` path a real spin uses.
- Pre-spin always reported a hardcoded `remaining_quantity: 1` for a guaranteed win regardless of actual inventory. It now reports the real value.

**Deferred** (needs a larger design/product decision, not attempted here):
- #9 Templates and date assignments don't affect spin selection — the deepest item on this list. `template_prizes` / `date_template_assignments` are a fully separate system from the `prize_inventory` rows that selection actually reads; reconciling them (materializing on assignment vs. selection-time resolution) also needs a per-day `is_enabled` concept that the schema doesn't have yet. Attempting a partial fix risked changing live prize odds without adequate test coverage.
- #14 Special-event boosts not applied — **the `weight_multiplier` half of this is now fixed** (selection multiplies a boosted prize's weight within its category). `quantity_override` is intentionally left unimplemented - its exact intended semantics (cap vs. floor vs. replace the selection-weight input) aren't specified anywhere, and guessing wrong risked a new, subtler bug.
- #18 Admin password in JS var / sent every request — needs real session/token authentication (see `PRODUCTION_HARDENING.md` §4.1), not a patch on top of the current shared-password model.

