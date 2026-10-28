---
name: windows-hosting-setup
description: Set up Docker + cloudflared on the Windows store laptop, run the PickerWheel docker-compose stack there, and connect the existing pickerwheel.mytmobiles.com Cloudflare Tunnel from that machine. Use when moving PickerWheel hosting from a dev Mac onto the actual Windows store PC, or reconnecting the tunnel after a reboot/network change.
---

# PickerWheel Windows Hosting Setup

## What this is

PickerWheel currently runs via `docker-compose.yml` on a developer's Mac for
testing, tunneled to the public internet at `pickerwheel.mytmobiles.com`
through a named Cloudflare Tunnel (`pickerwheel-admin`, tunnel id
`df80fe61-1b18-4778-94d8-6dddc8ece52a`). The end target is a Windows laptop
at the actual store, permanently.

That tunnel was created fresh on the store laptop on 2026-09-27 (Option B
below), replacing the original `cb7a20ad-...` tunnel used while testing on
the Mac. If the ID ever looks wrong, `cloudflared tunnel list` shows the
current one on the `pickerwheel-admin` row.

**Cloudflare-side setup (DNS, the Access Application, the 5-email allow
policy, One-Time-PIN identity provider, login branding) is already done in
the Cloudflare account and does not need to be repeated.** This skill is
about getting a `cloudflared` connector and the Docker stack running
*on the Windows machine* and pointed at that same existing tunnel - not
about recreating Cloudflare Access from scratch.

## Known constraints from the original setup (carry these over)

- **`--workers` must stay at 1** in the gunicorn command (`docker-compose.yml`).
  Socket.IO has no message queue configured, so a second worker/replica would
  silently drop real-time updates for some connected clients. Threads (not
  workers) were raised to 16 for headroom - don't lower that without reason.
- **`ALLOWED_ORIGINS`** in `docker-compose.yml` must include
  `https://pickerwheel.mytmobiles.com`, or Socket.IO rejects every real
  browser WebSocket handshake with "not an accepted origin" (surfaces as
  intermittent 400/502s, not an obvious error).
- **`ADMIN_PASSWORD`** in `docker-compose.yml` is still the shipped default
  (`myTAdmin2025`) as of this writing - it was deliberately left alone until
  testing finished. Rotate it before this becomes the real production
  deployment, and update it in both `docker-compose.yml` and anywhere else
  that references it.
- The routes `/app` (wheel), `/admin` (admin panel), and `/` redirecting to
  `/admin` *only* when the request carries a `CF-Connecting-IP` header (i.e.
  came through Cloudflare, not local/LAN) are already implemented in
  `backend/app/__init__.py`. Pull the latest `main` to get this.
- Admin login uses a session cookie, not a per-request password (see
  `backend/app/routes/admin.py`), and auto-fills the audit-log actor from
  `Cf-Access-Authenticated-User-Email` when accessed via the public domain.

## Why the local IP doesn't matter for the tunnel

`cloudflared`'s ingress config points at `http://localhost:9080` - loopback,
not the machine's LAN IP. Since `cloudflared` runs on the *same* machine as
the Docker stack, this stays correct no matter what WiFi network the laptop
joins or what IP it's assigned. **The tunnel needs no reconfiguration when
the network changes.**

The one thing that *does* depend on the local network is customers reaching
the wheel directly over LAN (e.g. `http://192.168.1.34:9080` from a phone on
the store WiFi, bypassing the tunnel entirely for lower latency - the public
domain is comparatively slow and meant for admin/remote access, not the
customer-facing flow). That LAN IP changes on every new network. See the
"Find the current LAN URL" section below for a one-liner to reprint it
whenever the network changes, rather than hardcoding it anywhere.

## Steps

### 1. Prerequisites on the Windows laptop

- Install **Docker Desktop for Windows** (WSL2 backend) -
  https://www.docker.com/products/docker-desktop/ - and make sure it's
  actually running (check the system tray icon) before step 4.
- Install **Git for Windows** if not already present.
- Install **cloudflared**:
  ```powershell
  winget install --id Cloudflare.cloudflared
  ```
  Verify: `cloudflared --version`

### 2. Get the code

```powershell
git clone https://github.com/storetmobiles2-code/pickerwheel-v1-docker-version.git
cd pickerwheel-v1-docker-version
git checkout main
git pull
```

(If working from a fork remote instead, adjust the URL - see the repo's
existing git remotes for the pattern: `origin` read-only, changes go via a
fork + PR.)

### 3. Get the tunnel running on this machine

The tunnel's actual credentials (a private key file) must **never** be
committed to git or pasted into a chat/skill file - treat it like a
password. Two ways to get `cloudflared` authorized on this new machine:

**Option A - reuse the existing tunnel (preferred, keeps the same domain
working with zero Cloudflare-side changes):**

1. On whichever machine currently holds it, securely copy these two files
   to the Windows machine's `%USERPROFILE%\.cloudflared\` folder (AirDrop,
   an encrypted USB stick, or a password manager's secure file storage -
   not email, not Slack, not committed anywhere):
   - `df80fe61-1b18-4778-94d8-6dddc8ece52a.json` (the tunnel credentials)
   - `cert.pem` (the account-level origin certificate)
2. Create `%USERPROFILE%\.cloudflared\config.yml`:
   ```yaml
   tunnel: df80fe61-1b18-4778-94d8-6dddc8ece52a
   credentials-file: C:\Users\<you>\.cloudflared\df80fe61-1b18-4778-94d8-6dddc8ece52a.json

   ingress:
     - hostname: pickerwheel.mytmobiles.com
       service: http://localhost:9080
     - service: http_status:404
   ```
3. Stop `cloudflared` wherever it's currently running (e.g. on the dev Mac:
   `kill <pid>` after finding it with `ps aux | grep cloudflared`) - only
   one connector should serve customer traffic at a time to avoid confusion
   about which machine is actually live, though Cloudflare does support
   multiple simultaneous connectors per tunnel if you deliberately want
   redundancy later.

**Option B - start fresh (if the credentials file was lost, or this is a
clean rebuild):**

```powershell
cloudflared tunnel login
# Browser opens -> select the mytmobiles.com zone -> Authorize
cloudflared tunnel create pickerwheel-admin
cloudflared tunnel route dns pickerwheel-admin pickerwheel.mytmobiles.com
```
Then write `config.yml` as in Option A, but with the **new** tunnel ID
`cloudflared tunnel create` just printed (it will differ from the one
above). Note the old tunnel's DNS record will need deleting in the
Cloudflare dashboard first if one still points at a dead tunnel.

### 4. Install cloudflared as a Windows service (survives reboot/network changes/sleep)

Run `cloudflared service install` from an elevated PowerShell. **This alone does
not work for a locally-managed tunnel.** It registers the exe with no arguments,
so the service shows "Running" but never connects (the public URL then gives
Error 1033 after login). It also rewrites
`C:\Program Files (x86)\cloudflared\config.yml` to a stub on every start, so
editing that file has no effect. After installing the service, run the elevated
repair script in `.claude/agents/cloudflare-tunnel-doctor.md` with the tunnel ID.
It copies the config and credentials to
`C:\Windows\System32\config\systemprofile\.cloudflared\` and sets the service
command to `--config <that config.yml> tunnel run`. Once that's done, the service
starts on boot and reconnects on its own after WiFi drops (usually within about
a minute).

Confirm it's actually connected. `Get-Service` showing "Running" is not enough,
and neither is a 302 from the public URL, because Cloudflare Access returns that
302 even when the tunnel is down:
```powershell
curl.exe -s http://127.0.0.1:20241/ready          # readyConnections must be > 0
cloudflared tunnel info pickerwheel-admin         # must list a connector
```

### 5. Start the app

```powershell
docker compose up -d
```
Wait for `pickerwheel-db` to report healthy, then confirm:
```powershell
curl http://localhost:9080/
```
Should return the wheel page HTML. If Docker Desktop was just installed,
the first `docker compose up -d` will take longer while it builds the image.

### 6. Verify end-to-end

```powershell
curl http://localhost:9080/                          # local wheel - HTTP 200
curl http://localhost:9080/admin                      # local admin - HTTP 200
curl -I https://pickerwheel.mytmobiles.com/           # public - 302 to Cloudflare Access login
```
Then in a browser: visit `https://pickerwheel.mytmobiles.com/`, complete the
email one-time-PIN login (one of the 5 allow-listed addresses), and confirm
it lands on `/admin` automatically.

### 7. Find the current LAN URL (whenever the network changes)

Run this any time the laptop joins a different WiFi network, to get the
current URL for customers on that same local network:

```powershell
$ip = @(Get-NetIPConfiguration |
    Where-Object { $_.IPv4DefaultGateway -and $_.NetAdapter.Status -eq 'Up' } |
    ForEach-Object { $_.IPv4Address.IPAddress })[0]
Write-Host "Customer wheel (this network): http://$($ip):9080/app"
```

Pick the adapter that has a default gateway, not just the first IPv4 address.
Docker Desktop's WSL adapter (`vEthernet (WSL ...)`, e.g. `192.168.128.1`)
often comes first in the address list, and phones on the WiFi can't reach it.
If WiFi and Ethernet are both connected, this takes the first one, so check
it's the one customers' phones are on.

The page itself loads at whatever the current IP is, because the stack
listens on `0.0.0.0:9080`. However, the wheel's live-update (Socket.IO)
connection is rejected with "Not an accepted origin" unless
`http://<that IP>:9080` is in `ALLOWED_ORIGINS` in `docker-compose.yml`. Add it
and run `docker compose up -d pickerwheel` whenever the IP changes. The
`cloudflare-tunnel-doctor` agent checks and fixes this automatically. The
tunnel's own config needs no changes when the network changes.

## Troubleshooting

- **Public domain returns Cloudflare error 530 / doesn't load**: the
  `cloudflared` service likely isn't running or hasn't reconnected yet.
  Check `Get-Service cloudflared` and its logs (Windows Event Viewer, or run
  `cloudflared tunnel run pickerwheel-admin` manually in a terminal to see
  live output).
- **Browser console shows repeated WebSocket handshake failures /
  intermittent 400 or 502 through the public domain**: check
  `ALLOWED_ORIGINS` in `docker-compose.yml` includes
  `https://pickerwheel.mytmobiles.com` exactly, then
  `docker compose up -d pickerwheel` to recreate the container with the
  updated env var.
- **Spin button gets stuck on "SPINNING..." forever**: check gunicorn is
  actually running the app (`docker top pickerwheel-app` should show
  `gunicorn --worker-class gthread --workers 1 --threads 16 ...`, not
  `python main.py`) - the dev server can't handle real concurrent
  WebSocket+HTTP traffic and requests can hang indefinitely. The frontend
  also has a 15s client-side timeout on the spin flow as a backstop
  (`fetchWithTimeout` in `frontend/wheel.js`).
- **Login page shows "restricted to members of the account" instead of an
  email field**: someone clicked "Sign in with Cloudflare" instead of using
  the email one-time-PIN field - that's a different, unrelated Cloudflare
  login path tied to actual Cloudflare.com account membership. The Access
  Application is already scoped to only offer the one-time-PIN provider
  (`allowed_idps` on the PickerWheel Access Application), so this shouldn't
  normally appear.
