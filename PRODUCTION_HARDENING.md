# PickerWheel Production Hardening Guide [NotReady to apply yet - still in dev only]

This document defines the work required to deploy PickerWheel safely for a real
prize campaign. It is written for the current Flask, Flask-SocketIO,
PostgreSQL, and Docker architecture.

The application should not be exposed to the public internet until the
**Release blockers** have been completed and verified.

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

The following are mandatory before launch:

- [ ] Remove all real or production-like credentials from Git history and
      configuration files.
- [ ] Require production secrets at startup; do not use insecure fallbacks.
- [ ] Replace repeated static admin-password authentication with a secure
      login/session or identity-provider integration.
- [ ] Make spin finalization server-authoritative.
- [ ] Prevent replay, duplicate finalization, and client-selected prize
      tampering.
- [ ] Make guaranteed-win state changes and inventory consumption atomic.
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

If a session-based admin system is implemented, replace the bootstrap
`ADMIN_PASSWORD` with a securely hashed administrator account and remove the
plaintext password variable.

### 3.2 Configuration requirements

Update `backend/app/config.py` so that:

- `SECRET_KEY` has no production fallback.
- `ADMIN_PASSWORD` has no production fallback.
- `DATABASE_URL` is required in production.
- `ALLOWED_ORIGINS` is parsed as a list.
- Database pool sizes are configurable and sized for the hosting plan.
- Business timezone is explicit and consistently applied.
- Debug mode is impossible when `FLASK_ENV=production`.

Fail fast with a clear startup error if a required variable is absent or
invalid. Do not silently switch to development settings.

### 3.3 Credential cleanup

The following files currently contain unsafe defaults and must be updated:

- `docker-compose.yml`
- `backend/app/config.py`

After removing secrets, scan the full Git history. Rotate any credential that
has been used outside local development; deleting it from the latest commit is
not sufficient.

## 4. Authentication and authorization

### 4.1 Admin authentication

The current `X-Admin-Password`/JSON password approach is not suitable for
production. Implement:

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
must record the administrator identity and source address in the audit log.

## 5. Spin integrity and abuse prevention

### 5.1 Server-authoritative spin flow

The current browser flow submits a client-selected prize ID to `/api/spin`.
That value must not be trusted.

Implement the following flow:

1. The client calls `/api/pre-spin`.
2. The server creates a one-time spin reservation containing:
   - Reservation ID or opaque token.
   - User/session identifier.
   - Event ID and business date.
   - Selected prize ID.
   - Expiration timestamp.
   - Status (`reserved`, `finalized`, or `expired`).
3. The client receives only the reservation token and display information.
4. The client calls `/api/spin/finalize` with the reservation token.
5. The server verifies ownership, expiry, event, and status.
6. The server atomically consumes the reserved prize and marks the reservation
   finalized.
7. Repeated finalization returns the original result or a safe conflict; it
   must never create another win.

The server must reject:

- A client-supplied prize ID that differs from the reservation.
- A reservation belonging to another session.
- An expired reservation.
- A previously finalized reservation.
- A reservation for an inactive event or incorrect business date.

### 5.2 Idempotency

Store an idempotency key for every finalization request and enforce a unique
constraint. A retry caused by a network timeout must return the original
result rather than consume inventory again.

### 5.3 Guaranteed wins

Guaranteed-win state changes and inventory consumption must occur in one
database transaction. Do not mark a guaranteed win as used before the prize
consumption succeeds.

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

Do not run the application with the Werkzeug development server or
`allow_unsafe_werkzeug=True`.

Use a production-supported Flask-SocketIO deployment model and verify:

- WebSocket upgrades.
- Long-polling fallback.
- Graceful shutdown.
- Connection and request timeouts.
- Worker behavior.
- Deployment-platform health checks.

Start with one application instance. If multiple instances are required,
configure Redis as the Socket.IO message queue and test broadcasts across
instances.

### 7.2 Health endpoints

Provide separate endpoints:

```text
/live   - process is running
/ready  - application can serve traffic
```

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

Replace wildcard API and Socket.IO CORS settings with the configured
production-origin allowlist. Same-origin deployment should be the default.

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

The application currently uses the remote address as a user identifier.
Document the purpose, retention period, and access policy for this data.

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

CI should run on every pull request:

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

