# PickerWheel Production Hardening Guide and Readiness Kanban

This document defines the work required to deploy PickerWheel safely for a real
prize campaign. It is written for the current Flask, Flask-SocketIO,
PostgreSQL, and Docker architecture.

Reviewed on 2026-09-27 against the current application tree (`f808b3f`), which
matches the source repository's `origin/main` tree at `c479325`. A follow-up
pass the same day (on a local-only `production` branch, not merged upstream)
closed several of the items this review found - see the updated snapshot
below and the kanban in §15 for what changed and what's still open. The
checklist below reflects the code as it exists now; it is not a claim that
every listed control has been implemented or that the app is ready to launch.

The application should not be exposed to the public internet until all **P0
release blockers** in the kanban have been completed and verified.

### Review snapshot

Already present in the current code:

- PostgreSQL `consume_prize` performs inventory consumption and guaranteed-win
  completion together; checks that the prize is enabled; and (as of the
  `production` branch) checks that a submitted `guaranteed_win_id` actually
  belongs to the submitted `prize_id` - closing a tampered-request gap where
  one prize's inventory could be consumed while an unrelated guaranteed win
  was marked triggered.
- Admin changes include optimistic-concurrency checks, live updates, and audit
  logging, now covering every field-edit route including special-event theme
  config and template-prize rows (the last two gaps, closed on the
  `production` branch). Backend integration tests and a Playwright E2E suite
  are present (116 backend tests as of this pass).
- Prize controls use budget tiers in place of the older admin-facing category
  concept.
- Production secrets now fail fast: `create_app()` refuses to start with
  `FLASK_ENV=production` if `SECRET_KEY`/`ADMIN_PASSWORD` are left at their
  insecure defaults. CORS is now an explicit, configurable `ALLOWED_ORIGINS`
  allowlist (wired into both Flask-CORS and Socket.IO) instead of a wildcard.
  A `Procfile` runs the app under gunicorn (`gthread`, pinned to exactly 1
  worker - see §7.1) instead of the Werkzeug dev server.

Still blocking production:

- Admin access still uses one shared password, including for WebSocket
  mutations, and the client supplies the audit actor name. Explicitly
  deferred pending a separate decision - see §4.
- Public spin endpoints accept a client-selected prize and there is no
  server-side reservation or idempotency enforcement.
- `frontend/wheel.js` contains reservation/finalization calls to
  `/api/spin/reserve` and `/api/spin/finalize` (confirmed dead code -
  `requestServerPrizeDecision`/`confirmReceiptAndFinalize` are never called
  from anywhere), but the backend does not define those routes. The active
  spin path instead calls `/api/pre-spin` and then `/api/spin`. See §5.1 -
  this is the single largest remaining item and needs its own dedicated plan,
  not a quick patch: it means new backend routes, rewiring `wheel.js`'s
  working `spin()` over to this currently-untested dead path, and rewriting
  roughly 23 existing tests keyed to the current contract.
- **New finding this pass:** the seeded event's `end_date` (`2026-03-21`, see
  `backend/schema/004_seed_data.sql`) has already passed relative to the
  current system date. If §6.2's "reject spins outside the active event
  period" is implemented using `start_date`/`end_date` literally, spins break
  immediately in this exact environment - the seed dates must be corrected in
  the same change, not as a follow-up.
- **New finding this pass:** `admin.html` has 65 inline `onclick=` handlers
  plus a large inline `<script>` block; `index.html` has inline handlers plus
  4 inline `<script>` blocks. A standard strict CSP (no `unsafe-inline`) per
  §9.2 would break most of the UI in both pages. Needs either `unsafe-inline`
  for scripts (weakens the CSP significantly) or a real frontend refactor
  (externalize scripts, replace `onclick=` with `addEventListener`, add
  nonces) - not currently scoped anywhere.
- The SQL files are initialization scripts, not a managed production
  migration workflow.
- A production CI workflow, rate limiting, separate readiness checks,
  backup/restore evidence, and operational alerting are not configured.

## 1. Current production shape

PickerWheel currently runs as one Docker image containing:

- Flask-rendered static frontend files
- REST APIs under `/api`
- Flask-SocketIO real-time updates
- PostgreSQL-backed prize inventory and audit data

Recommended initial production topology:

```text
Users
  |
  | HTTPS and Socket.IO
  v
One always-on application instance
  |
  | Private TLS/database connection
  v
Managed PostgreSQL
```

Use one application instance initially. Add Redis and horizontal scaling only
after cross-instance Socket.IO broadcasting has been tested.

## 2. Release blockers

The following are mandatory before launch. Treat each item as open until its
acceptance criteria are met against the production-like deployment:

- [ ] Remove all real or production-like credentials from Git history and
      configuration files.
- [ ] Require production secrets at startup; do not use insecure fallbacks.
- [ ] Replace repeated static admin-password authentication with a secure
      login/session or identity-provider integration.
- [ ] Make spin selection and finalization server-authoritative. Atomic
      inventory consumption and guaranteed-win completion are already present,
      but the request flow still trusts the client's selected prize.
- [ ] Prevent replay, duplicate finalization, and client-selected prize
      tampering.
- [ ] Verify the current atomic guaranteed-win/inventory implementation and
      regression coverage are present in the production schema and deployment.
- [ ] Restrict CORS to the production origin.
- [ ] Add rate limiting and request validation to public and admin endpoints.
- [ ] Run behind a production-supported WSGI/Socket.IO server rather than
      Werkzeug with `allow_unsafe_werkzeug=True`.
- [ ] Apply versioned database migrations to managed PostgreSQL.
- [ ] Configure PostgreSQL backups and verify a restore.
- [ ] Add automated tests for concurrency, authorization, and tampered spins.
- [ ] Configure HTTPS, security headers, health checks, centralized logging,
      and alerting.

## 3. Configuration and secrets

### 3.1 Required production environment variables

Configure these in the hosting provider's secret manager, not in Git:

```text
FLASK_ENV=production
PORT=<provider-assigned-port>
DATABASE_URL=<managed-postgresql-connection-string>
SECRET_KEY=<long-random-application-secret>
ADMIN_PASSWORD=<temporary-bootstrap-secret-only>
ALLOWED_ORIGINS=https://pickerwheel.example.com
BUSINESS_TIMEZONE=Asia/Kolkata
REALTIME_WHEEL_UPDATES=true
LOG_LEVEL=INFO
```

The current implementation still authenticates every administrator with the
same `ADMIN_PASSWORD`. Replace it with individually managed, securely hashed
accounts or an identity provider, then remove the shared password variable.

### 3.2 Configuration requirements

Update `backend/app/config.py` so that:

- [x] `SECRET_KEY` has no usable production fallback - `validate_production_config()`
      raises `RuntimeError` at startup if `FLASK_ENV=production` and it's still
      the known insecure literal. (The class-level fallback string itself still
      exists, since `development`/`testing` intentionally keep using it - this
      is fail-fast validation, not literal removal of the default.)
- [x] `ADMIN_PASSWORD` has no usable production fallback - same mechanism.
- [ ] `DATABASE_URL` is required in production - not yet enforced.
- [x] `ALLOWED_ORIGINS` is parsed as a list - wired into both Flask-CORS and
      Socket.IO's `cors_allowed_origins` in `create_app()`.
- [ ] Database pool sizes are configurable and sized for the hosting plan -
      configurable today, but not yet sized against any real hosting plan.
- [ ] Business timezone is explicit and consistently applied - not addressed.
- [x] Debug mode is impossible when `FLASK_ENV=production` - `ProductionConfig.DEBUG`
      is hardcoded `False` regardless of any env var (predates this pass).

Fail fast with a clear startup error if a required variable is absent or
invalid. Do not silently switch to development settings.

### 3.3 Credential cleanup

- [x] `docker-compose.yml` was mislabeled `FLASK_ENV=production` for what is
      actually the local dev stack - this would have tripped the new fail-fast
      check the moment it shipped, since that stack intentionally keeps simple
      shared local credentials. Relabeled to `FLASK_ENV=development`. The
      credentials themselves (`ADMIN_PASSWORD=myTAdmin2025`, etc.) were left
      in place by design - this file is not what a real deployment runs from
      (see the `Procfile` in §7.1 instead), so it doesn't need production-grade
      secrets, just an accurate label.
- [ ] `backend/app/config.py`'s hardcoded default literals themselves remain
      (intentionally, for `development`/`testing`) - only production startup
      is gated.
- [ ] Git history has not been scanned for credentials; none have been rotated.

Rotate any credential that has been used outside local development; deleting
it from the latest commit is not sufficient.

## 4. Authentication and authorization

### 4.1 Admin authentication

The current `X-Admin-Password`/JSON password approach is not suitable for
production. Optimistic locking and live multi-device updates are present, but
they do not provide secure individual identity or session revocation.
Implement:

- A dedicated admin login endpoint.
- Argon2id or bcrypt password hashing.
- Secure, HttpOnly, SameSite cookies or short-lived signed access tokens.
- Session expiration and server-side revocation.
- Login failure rate limiting and temporary lockout.
- CSRF protection for cookie-authenticated mutating requests.
- Authorization checks on every admin endpoint.
- Audit records for login, logout, failed login, and administrative changes.

Never return the password, password hash, or authentication token in API
responses or logs.

### 4.2 Admin authorization

Separate permissions where practical:

- View inventory and reports.
- Adjust inventory.
- Modify prizes.
- Manage events and guaranteed wins.
- Manage administrators.

At minimum, all mutating endpoints must require authenticated admin access and
must record a server-verified administrator identity and trusted source
address in the audit log. The current `X-Admin-Actor`/`admin_actor` value comes
from the client and can be forged.

## 5. Spin integrity and abuse prevention

### 5.1 Server-authoritative spin flow

The active browser flow calls `/api/pre-spin`, animates to the returned prize,
then submits `selected_prize_id` to `/api/spin`. The backend consumes inventory
atomically, but it does not bind that prize to a server-created reservation;
a caller can bypass the intended animation/selection and choose any otherwise
eligible prize. `SpinService.pre_spin` only returns a selection; it does not
persist a reservation.

There is also frontend code that requests `/api/spin/reserve` and
`/api/spin/finalize`, but those backend routes do not exist. Treat those client
helpers as unwired code, not as a security control.

Implement and wire one consistent flow:

1. The client requests a spin reservation. The server derives the user/session
   identity and active event/business date, selects the prize, and persists a
   one-time reservation containing an opaque ID, prize ID, expiry, and status.
2. The client receives only the reservation token and display information.
3. The client finalizes using the reservation token; it cannot choose or
   replace the prize ID.
4. The server verifies ownership, expiry, active event, reservation status,
   and idempotency key, then consumes inventory and finalizes the reservation
   in one database transaction.
5. A retry returns the original result or a safe conflict and never consumes
   inventory twice.

The server must reject:

- A client-supplied prize ID that differs from the reservation.
- A reservation belonging to another session.
- An expired reservation.
- A previously finalized reservation.
- A reservation for an inactive event or incorrect business date.

### 5.2 Idempotency

The frontend currently generates an idempotency key for its unused reservation
helper, but the active API path does not submit or enforce one. Store a
server-verified idempotency key for every finalization request and enforce a
unique constraint. A retry caused by a network timeout must return the
original result rather than consume inventory again.

### 5.3 Guaranteed wins

The current `consume_prize` SQL function already performs guaranteed-win
completion and inventory consumption in one database transaction, and (as of
migration `012_consume_prize_guaranteed_win_match_check.sql`) also verifies
that a submitted `guaranteed_win_id` actually belongs to the submitted
`prize_id` - closing a gap where a tampered request could consume one prize's
inventory while marking an unrelated guaranteed win triggered. Preserve these
invariants, ensure the latest function definition (`012`, not an earlier one)
is deployed, and keep the depleted-stock, daily-limit, disabled-prize,
mismatched-prize/win, replay, and rollback tests passing.

### 5.4 Abuse controls

Apply limits to:

- Pre-spin requests per IP and session.
- Finalization requests per reservation.
- Concurrent reservations per session.
- Admin login attempts.
- Request body size and input string length.
- Date and ID query parameters.

Do not rely on JavaScript, `sessionStorage`, disabled buttons, or service-worker
behavior as security controls.

## 6. Database and data integrity

### 6.1 Migrations

The SQL files under `backend/schema/` currently act primarily as initialization
scripts. Production requires a versioned migration process:

- Apply migrations in a deterministic order.
- Record the current schema version.
- Run migrations as a controlled pre-deploy step.
- Make migrations safe to retry.
- Back up the database before destructive migrations.
- Test migrations against a production-like database.

Do not rely on PostgreSQL container initialization mounts for a managed database.

### 6.2 Event lifecycle

Remove the hardcoded assumption that event ID `1` is always active. Enforce:

- Event start and end dates.
- Paused and ended states.
- Explicit `Asia/Kolkata` business-date behavior where applicable.
- Rejection of spins outside the active event period.
- Admin-controlled event configuration.
- Inventory generation for the full event period or a safe scheduled process.

Review the seed event dates in `backend/schema/004_seed_data.sql` before launch.

**Verified this pass:** the seeded event's `end_date` (`2026-03-21`) has
already passed relative to the current system date. This is not a future
concern - implementing "reject spins outside the active event period" using
`start_date`/`end_date` as literally described would break every spin in this
exact environment immediately. Update the seed dates in the same change that
adds the enforcement, not as a separate follow-up.

### 6.3 Transactional invariants

The database must guarantee:

- Inventory never becomes negative.
- Daily limits cannot be exceeded under concurrent requests.
- A successful win has exactly one transaction record.
- A successful win has a matching inventory decrement.
- Failed operations roll back all related changes.
- Audit records cannot be silently omitted.
- A finalized reservation cannot be consumed twice.

Use row-level locking and database constraints rather than application-only
checks.

### 6.4 Backups and recovery

Configure:

- Automated PostgreSQL backups.
- Point-in-time recovery where available.
- Retention appropriate to the campaign.
- Encrypted backups.
- A documented restore procedure.
- A restore test before launch and periodically thereafter.

Record the recovery point objective (RPO) and recovery time objective (RTO)
for the campaign.

## 7. Application runtime

### 7.1 Production server

A `Procfile` (repo root, `production` branch) now runs the app under gunicorn
(`--worker-class gthread --workers 1 --threads 4`) instead of the Werkzeug
dev server / `allow_unsafe_werkzeug=True`. `backend/main.py`'s
`if __name__ == '__main__':` block (`python main.py`) remains the local-dev
entry point only. Locally smoke-tested: the app boots under this exact
gunicorn command, and `/api/health`/`/api/pre-spin` respond correctly through
it.

`--workers` is deliberately pinned to **exactly 1** and must not be raised
without first adding Redis as the Socket.IO message queue (`SOCKETIO_MESSAGE_QUEUE`
exists in `backend/app/config.py` but is not wired to anything) - more than
one worker or instance would silently stop delivering real-time broadcasts to
some connected admins, with no error anywhere. This is enforced by convention
(the Procfile + this note) only, not by a runtime guard.

Not yet verified: WebSocket upgrades, long-polling fallback, graceful
shutdown, connection/request timeouts, and worker behavior through an actual
hosting platform's reverse proxy and health checks - only local smoke-testing
has been done so far.

Start with one application instance. If multiple instances are required,
configure Redis as the Socket.IO message queue and test broadcasts across
instances.

### 7.2 Health endpoints

Provide separate endpoints:

```text
/live   - process is running
/ready  - application can serve traffic
```

The current `/api/health` endpoint only returns a healthy response and does
not check database connectivity or schema readiness; `/live` and `/ready` are
not implemented yet.

`/ready` should verify database connectivity and required schema readiness.
Health responses must not expose connection strings or exception details.

### 7.3 Error handling

Replace raw `str(e)` responses with stable public error messages. Log the
complete exception server-side with a request ID.

Use consistent error responses such as:

```json
{
  "success": false,
  "error": {
    "code": "RESERVATION_EXPIRED",
    "message": "This spin is no longer available.",
    "request_id": "..."
  }
}
```

Do not return SQL errors, stack traces, filesystem paths, or secrets to users.

## 8. Container and hosting hardening

Update `Dockerfile` to:

- Run as a non-root user.
- Include only required runtime files.
- Add a `.dockerignore`.
- Avoid source bind mounts in production.
- Add a container health check.
- Use a production entrypoint.
- Keep build-only compilers out of the final image where practical.
- Pin base images and rebuild them regularly.
- Set explicit file permissions.
- Never copy environment files containing secrets.

The development volume mounts in `docker-compose.yml` must not be used by the
production service.

For a managed platform such as Render:

- Use one always-on web service initially.
- Attach managed PostgreSQL.
- Set the service health check to `/ready`.
- Configure the provider's HTTPS custom domain.
- Store secrets in the provider secret manager.
- Disable deploys from unprotected branches.
- Retain deploy and application logs for the campaign period.

## 9. Network and browser security

### 9.1 CORS

`backend/app/config.py`'s `ALLOWED_ORIGINS` (comma-separated, defaults to the
app's own dev-serving origins) is now wired into both Flask-CORS
(`resources={r"/api/*": ..., r"/socket.io/*": ...}`) and Socket.IO's
`cors_allowed_origins` in `create_app()`, replacing the previous wildcard. The
default value still only covers local dev - set `ALLOWED_ORIGINS` to the real
production origin(s) at deploy time; this is infrastructure that enables
restricting CORS, not itself a claim that a specific production origin has
been configured yet.

### 9.2 Security headers

Configure:

- `Strict-Transport-Security`
- `Content-Security-Policy`
- `X-Content-Type-Options: nosniff`
- `Referrer-Policy`
- `Permissions-Policy`
- `frame-ancestors` or an equivalent clickjacking policy

The Content Security Policy must explicitly account for Socket.IO, fonts,
audio, and any external CDN resources. Prefer self-hosting critical
JavaScript dependencies.

**Verified blocker for a standard strict CSP:** `frontend/admin.html` has 65
inline `onclick=` handlers plus one large inline `<script>` block;
`frontend/index.html` has inline handlers plus 4 inline `<script>` blocks. A
CSP without `unsafe-inline` for scripts would break most buttons in both
pages. Either accept `unsafe-inline` (weakens much of the CSP's benefit) or
plan a real refactor first (externalize scripts, replace `onclick=` with
`addEventListener`, add nonces) - this is a separate, nontrivial project, not
a one-line header change.

### 9.3 Service worker

Verify `frontend/sw.js` during deployment testing:

- API responses are never cached.
- Admin pages cannot remain stale after a release.
- Asset cache versions change reliably.
- Failed network responses do not look like successful API responses.
- A new deployment cannot leave clients with incompatible JavaScript.

Use content-hashed assets or a controlled cache invalidation strategy instead
of relying only on manually edited version strings.

## 10. Privacy and logging

The application accepts a browser-supplied `user_id` stored in local storage
and falls back to the remote address when none is supplied. Neither value is a
trusted identity. Document the purpose, retention period, and access policy
for identifiers and network addresses.

Prefer a short-lived pseudonymous session identifier or a hashed address when
the full address is not required. Configure trusted proxy handling before
using forwarded address headers.

Logs must:

- Include timestamp, severity, service, and request ID.
- Avoid passwords, tokens, cookies, and full sensitive headers.
- Avoid unnecessary full IP addresses.
- Record admin actions and spin outcome codes.
- Be sent to centralized storage with retention limits.

## 11. Testing and CI/CD

Add automated tests for:

### Security

- Unauthenticated admin requests.
- Invalid and expired sessions.
- CSRF failures.
- CORS behavior.
- Rate limits.
- Oversized and malformed requests.
- Tampered reservation and prize IDs.

### Spin behavior

- Successful reservation and finalization.
- Expired reservation.
- Replayed finalization.
- Concurrent spins against one remaining item.
- Daily limit enforcement under concurrency.
- Guaranteed-win rollback.
- Inactive and ended events.

### Operations

- Database migration from a clean database.
- Database migration from the previous production version.
- `/live` and `/ready`.
- WebSocket connect, reconnect, and fallback polling.
- Backup restore.
- Container startup without development defaults.

Backend integration and Playwright E2E suites are present, but notable admin
routes and production behaviors remain uncovered (see `TEST_PLAN.md`). No
repository CI workflow is currently configured. CI should run on every pull
request:

- Formatting and linting.
- Type checking where applicable.
- Unit and integration tests with PostgreSQL.
- Docker build.
- Dependency vulnerability scan.
- Secret scan.
- Migration validation.

Deploy only from a protected branch after CI passes.

## 12. Observability and incident response

Monitor:

- Availability and readiness.
- HTTP 4xx/5xx rates.
- WebSocket connection and reconnect rates.
- Spin reservations, finalizations, failures, and conflicts.
- Inventory exhaustion.
- Database latency, connections, locks, and storage.
- Admin login failures.
- Container restarts and memory/CPU usage.

Create alerts for:

- Readiness failures.
- Elevated 5xx responses.
- Database connection exhaustion.
- Duplicate or suspicious spin activity.
- Inventory inconsistencies.
- Repeated admin authentication failures.

Document:

- How to pause an event.
- How to disable a prize.
- How to rotate secrets.
- How to revoke admin sessions.
- How to restore PostgreSQL.
- How to roll back an application release.
- Who is responsible for incident response.

## 13. Launch acceptance checklist

The release owner must sign off all of the following:

- [ ] Production configuration contains no insecure defaults.
- [ ] Secrets are stored outside Git and have been rotated.
- [ ] Admin authentication and authorization tests pass.
- [ ] Spin results cannot be changed by editing browser requests.
- [ ] Duplicate requests cannot create duplicate wins.
- [ ] Concurrent inventory tests pass.
- [ ] Guaranteed-win rollback tests pass.
- [ ] Migrations are applied and schema version is recorded.
- [ ] Backups are enabled and a restore has succeeded.
- [ ] HTTPS and security headers are verified externally.
- [ ] CORS allows only expected origins.
- [ ] WebSocket and polling fallback work through the production proxy.
- [ ] `/live` and `/ready` are monitored.
- [ ] Error responses do not expose internals.
- [ ] Logs and alerts are visible to the operations owner.
- [ ] The event dates, timezone, prizes, inventory, and daily limits have been
      verified by the campaign owner.
- [ ] A rollback and incident contact plan exists.

## 14. Recommended implementation order

1. Remove secrets and enforce production configuration validation.
2. Implement secure admin authentication and authorization.
3. Implement server-side reservations, finalization, and idempotency.
4. Make guaranteed wins and inventory consumption atomic.
5. Implement migrations, event lifecycle, and timezone handling.
6. Configure the production Socket.IO server.
7. Add validation, rate limiting, and safe error responses.
8. Harden the Docker image and hosting configuration.
9. Add automated tests and CI/CD gates.
10. Add backups, monitoring, security headers, and perform load testing.

## 15. Production-readiness kanban

This board is the implementation tracker for the findings above. `OPEN` means
not production-ready; `PARTIAL` means some supporting code exists but the
acceptance criteria are not complete; `DONE` is reserved for controls verified
in the deployed production-like configuration. Priorities:

- **P0 / release blocker**: must be complete before any public production
  launch.
- **P1 / launch requirement**: complete before campaign traffic or before
  increasing service scale.
- **P2 / operational follow-up**: schedule and track with the release owner.

### Identity and admin access

- [ ] **OPEN · P0 — Replace shared admin password.** Implement individual
  administrator identities using a maintained identity provider or
  securely-hashed credentials, secure/HttpOnly/SameSite sessions, expiration,
  logout, and revocation. Remove password values from every HTTP body/header
  and WebSocket event. **Accept when:** tests prove unauthenticated,
  expired, revoked, and unauthorized users cannot access or mutate admin
  resources; secrets are not returned or logged.
- [ ] **OPEN · P0 — Enforce permissions and trusted audit attribution.**
  Protect every admin route and mutation-capable WebSocket event with the same
  authorization policy; derive actor identity from the authenticated server
  session instead of `X-Admin-Actor`/`admin_actor`. **Accept when:** route and
  socket authorization tests cover every mutation class and audit rows contain
  the authenticated actor.
- [ ] **OPEN · P1 — Add identity lifecycle operations.** Define account
  provisioning, least-privilege roles, credential rotation, administrator
  offboarding, and emergency revocation. **Accept when:** the release owner can
  revoke an admin without a deployment and the procedure is exercised.

### Security and privacy

- [ ] **PARTIAL · P0 — Remove development credentials and validate configuration.**
  `validate_production_config()` now fails fast if `FLASK_ENV=production` and
  `SECRET_KEY`/`ADMIN_PASSWORD` are still their insecure defaults;
  `docker-compose.yml`'s mislabeled `FLASK_ENV=production` (which would have
  tripped this on the local dev stack) is fixed to `development`. Still open:
  `DATABASE_URL` is not yet required in production; Git history has not been
  scanned; no credentials have been rotated. **Accept when:** production
  startup fails clearly for missing/weak settings and secret scanning is clean.
- [ ] **PARTIAL · P0 — Restrict cross-origin access.** `ALLOWED_ORIGINS` is
  now parsed as a list and applied consistently to Flask CORS and Socket.IO,
  replacing the wildcard. Still open: the default value only covers local
  dev - no real production origin has been configured yet, since none is
  chosen. **Accept when:** production-origin requests succeed and untrusted
  origins fail in automated HTTP and WebSocket tests against a real deployment.
- [ ] **OPEN · P0 — Add abuse controls and input limits.** Rate-limit public
  spin/pre-spin and admin login routes; bound body sizes, string lengths, date
  ranges, IDs, and concurrent outstanding reservations. **Accept when:** limit
  and malformed-input tests demonstrate stable 4xx responses without creating
  transactions or reservations.
- [ ] **OPEN · P1 — Add safe security defaults.** Add CSRF protection for
  cookie-authenticated mutations, secure cookie settings, trusted-proxy
  configuration, and a documented data-retention policy for user IDs and IP
  addresses. **Accept when:** CSRF, proxy spoofing, cookie, and retention
  checks pass for the hosting platform.

### Frontend and browser behavior

- [ ] **OPEN · P0 — Remove client authority over winning outcomes.** Wire the
  wheel to the backend reservation/finalization API and display only the
  finalized server result; remove or implement the current calls to
  `/api/spin/reserve` and `/api/spin/finalize` so the browser and API contracts
  match. **Verified this pass:** `requestServerPrizeDecision`/
  `confirmReceiptAndFinalize`/`startResponsiveSpinAnimation` in
  `frontend/wheel.js` are confirmed dead code - never called from anywhere;
  the active `spin()` path uses `getBackendSelectedPrize()` →
  `/api/pre-spin`/`/api/spin` instead. This is the largest remaining item in
  this document: it needs new backend routes, rewiring the working `spin()`
  method onto this currently-untested dead path, and rewriting roughly 23
  existing tests across `test_spin_flow.py`, `test_guaranteed_wins.py`, and
  `test_special_event_boost.py` that are keyed to the current contract. Give
  it its own dedicated implementation plan rather than folding it into other
  hardening work. **Accept when:** E2E tests tamper with prize IDs,
  reservation IDs, user IDs, and finalization retries and cannot obtain an
  unauthorized or duplicate win.
- [ ] **OPEN · P1 — Make offline/API failures unambiguous.** In
  `frontend/sw.js`, keep APIs network-only and return a genuine non-success
  network error rather than a success-shaped JSON response with HTTP 200.
  Prevent admin HTML/API responses from being cached; define a versioned,
  tested static-asset invalidation strategy. **Accept when:** offline and
  upgrade E2E tests never show stale admin pages or treat a failed API call as
  a successful result.
- [ ] **OPEN · P1 — Verify browser security and usability.** Test rendering of
  untrusted prize/admin content, keyboard navigation, focus handling, mobile
  layouts, and CSP-compatible assets. Keep third-party assets minimized or
  self-hosted. **Accept when:** XSS regression, accessibility, and supported
  browser checks pass without weakening CSP.

### Backend and event operations

- [ ] **OPEN · P0 — Implement server-owned spin reservations.** Persist a
  one-time reservation, expiry, owner/session, event/date, selected prize,
  finalization status, and idempotency key; make finalization atomic with
  `consume_prize`. **Accept when:** concurrent, expired, replayed, cross-user,
  and failed-transaction tests prove inventory and transaction invariants.
- [ ] **OPEN · P0 — Enforce production startup and runtime settings.** Reject
  unknown environment names and missing required settings, force debug off,
  configure pool limits, and stop logging database connection details.
  **Accept when:** a container-start test with production settings verifies
  fail-fast behavior and no development fallback.
- [ ] **OPEN · P1 — Enforce event lifecycle and business time.** Replace
  implicit event ID `1` and direct server-local `date.today()` assumptions
  with configured active-event resolution and one explicit business timezone
  across selection, inventory, statistics, and audit dates. **Verified this
  pass:** the seeded event's `end_date` (`2026-03-21`) has already passed
  relative to the current system date - implementing this literally right now
  would break every spin immediately unless the seed dates are corrected in
  the same change. **Accept when:** tests cover before/during/after event
  dates and timezone boundaries, and the seed data reflects a real,
  currently-valid campaign window.
- [ ] **OPEN · P1 — Normalize error handling and request observability.** Use
  stable public error codes, request IDs, structured server-side exception
  logs, and consistent logging that excludes credentials, tokens, cookies, and
  sensitive headers. **Accept when:** failure-path tests confirm clients see
  no stack traces, SQL, paths, or secrets while operators can correlate logs.

### API contracts

- [ ] **OPEN · P0 — Lock down spin API ownership and idempotency.** Make the
  reservation token the sole authority to finalize; derive identity, event,
  and date on the server and reject client-selected prize/event/date values.
  **Accept when:** OpenAPI or equivalent contract documentation matches the
  implementation and tampering/replay tests pass.
- [ ] **OPEN · P1 — Validate every external request.** Apply schema-based
  validation and consistent error responses to all public and admin endpoints,
  including query dates, numeric ranges, enum values, and missing fields.
  **Accept when:** malformed and boundary-value test cases return intentional
  4xx responses rather than 500s.
- [ ] **OPEN · P1 — Separate liveness and readiness.** Retain a cheap liveness
  endpoint and add readiness that verifies database connectivity and deployed
  schema version without disclosing internals. **Accept when:** readiness
  fails during a database outage and succeeds only after required schema is
  available.

### Database and data integrity

- [ ] **OPEN · P0 — Establish versioned production migrations.** Convert the
  ordered SQL bootstrap files in `backend/schema/` into a repeatable,
  version-tracked migration workflow for managed PostgreSQL, run it as a
  controlled deploy step, and test clean and upgrade paths. **Accept when:**
  deploys record schema version, fail safely on migration errors, and do not
  rely on container initialization mounts.
- [ ] **PARTIAL · P0 — Preserve transactional spin invariants.** The current
  `consume_prize` implementation (migration `012`) uses database-side
  checks/locking, atomically records inventory and guaranteed-win changes, and
  now also verifies a submitted `guaranteed_win_id` belongs to the submitted
  `prize_id`. Verify production migrations are applied through `012` (not an
  earlier definition), review constraints and audit consistency, and retain
  concurrency/replay/mismatch regression tests. **Accept when:** parallel
  attempts against the last unit yield exactly one win, a mismatched
  prize/guaranteed-win pair is rejected, and all related writes either commit
  together or roll back.
- [ ] **OPEN · P0 — Prove backup and restore.** Configure encrypted automated
  backups/PITR, retention, access controls, and named RPO/RTO targets.
  **Accept when:** a documented restore into an isolated environment succeeds
  and campaign data integrity is verified.
- [x] **DONE · P1 — Close remaining optimistic-locking gaps.** Special-event
  theme config (`update_event_theme`/`reset_event_theme`, previously routed
  through a separate unlocked method) and template-prize edits
  (`add_prize_to_template`/`update_template_prize`, previously no
  `updated_at` column at all on `template_prizes` - added via migration `013`)
  now have the same `expected_updated_at`/409-conflict check as every other
  admin resource. **Accepted:** 9 new tests in
  `backend/tests/test_optimistic_concurrency.py` cover happy-path and
  stale-conflict for both, plus the add-vs-edit optional-locking distinction
  on `add_prize_to_template`.
- [ ] **OPEN · P1 — Size and monitor database connections.** Configure the
  SQLAlchemy pool against the actual platform/database connection limit,
  timeouts, TLS, and connection monitoring. **Accept when:** a load test
  demonstrates the pool remains within provider limits and recovers cleanly
  from dropped connections.

### Hosting, container, and network

- [ ] **PARTIAL · P0 — Run a production-supported Socket.IO server.** A
  `Procfile` now runs gunicorn (`gthread`, pinned to 1 worker) in place of
  `python main.py`/Werkzeug/`allow_unsafe_werkzeug=True`; locally smoke-tested
  (boots, serves `/api/health` and `/api/pre-spin` correctly). Still open:
  not yet verified against an actual hosting platform - WebSocket upgrade,
  polling fallback, graceful shutdown, health checks, and worker behavior
  through a real reverse proxy. **Accept when:** all of the above pass through
  the actual hosting proxy.
- [ ] **OPEN · P0 — Build a production-only container.** Add a `.dockerignore`,
  non-root runtime user, least-privilege filesystem, production entrypoint and
  health check; remove development source mounts and ensure secrets are not
  copied into the image. **Accept when:** image inspection and startup tests
  prove it runs non-root with no source bind mounts or embedded secrets.
- [ ] **OPEN · P0 — Configure the hosting platform.** Use managed PostgreSQL,
  private database networking/TLS, HTTPS/custom domain, secret manager,
  protected deploy branch, and an always-on service sized for Socket.IO. Do
  not expose the database port publicly. **Accept when:** external HTTPS and
  database connectivity are verified and only intended public ports are
  reachable.
- [ ] **OPEN · P1 — Add browser response security headers.** Configure and
  validate HSTS, CSP, `X-Content-Type-Options`, `Referrer-Policy`,
  `Permissions-Policy`, and clickjacking protection for all app routes.
  **Verified this pass:** `admin.html` has 65 inline `onclick=` handlers plus
  an inline `<script>` block; `index.html` has inline handlers plus 4 inline
  `<script>` blocks - a standard strict CSP would break most of the UI in
  both pages. Plan either `unsafe-inline` for scripts (weaker) or a frontend
  refactor (externalize scripts, `addEventListener`, nonces) before writing
  the policy, not after. **Accept when:** production responses include the
  intended headers and the actual wheel, fonts, audio, and Socket.IO work
  under CSP without silently broken buttons.

### Testing, CI/CD, and release management

- [ ] **OPEN · P0 — Gate deploys on CI.** Add CI for formatting/linting,
  backend tests on isolated PostgreSQL, Playwright E2E, migration validation,
  Docker build, dependency scanning, and secret scanning. **Accept when:**
  pull requests cannot deploy unless required checks pass.
- [ ] **OPEN · P0 — Close launch-critical coverage gaps.** Extend tests for
  spin reservation ownership/idempotency, every admin mutation class,
  authorization, CSRF, CORS, rate limits, health/readiness, and migration
  upgrades. **Accept when:** test results are repeatable from a clean CI
  environment and all P0 acceptance cases are covered.
- [ ] **OPEN · P1 — Validate capacity and release safety.** Load-test expected
  campaign traffic, test one-instance Socket.IO behavior and recovery, define
  rollback criteria, and rehearse rollback to a previous image/schema-safe
  release. **Accept when:** measured capacity has documented headroom and the
  release owner completes a rollback rehearsal.

### Monitoring and incident readiness

- [ ] **OPEN · P0 — Configure centralized logs and actionable alerts.** Monitor
  availability/readiness, HTTP errors, WebSocket failures, spin outcomes,
  inventory anomalies, admin login failures, database capacity, and container
  restarts. **Accept when:** an injected failure triggers the correct alert
  and on-call owner can find a correlated request in logs.
- [ ] **OPEN · P1 — Document campaign response procedures.** Assign owners and
  document how to pause an event, disable prizes, revoke admins, rotate
  secrets, restore data, contact the host/provider, and communicate an
  incident. **Accept when:** the release owner rehearses the runbook and
  confirms contacts and escalation paths.

### Launch sign-off

- [ ] **OPEN · P0 — Complete an end-to-end production rehearsal.** Deploy the
  release candidate to a production-like hosting environment, apply
  migrations, load verified event/prize/inventory settings, test public and
  admin paths, verify HTTPS/CORS/headers/WebSockets, restore a backup, and
  confirm monitoring/rollback. **Accept when:** the campaign owner and
  technical release owner sign off every launch checklist item in section 13.
