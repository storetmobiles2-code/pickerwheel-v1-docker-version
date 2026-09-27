---
name: cloudflare-tunnel-doctor
description: Sets up, diagnoses, and auto-repairs PickerWheel's Cloudflare Tunnel + Docker hosting on the Windows store laptop. Use after moving the laptop to a new network (store WiFi etc.), after a reboot, or whenever https://pickerwheel.mytmobiles.com shows Error 1033/530/502, won't load, or the customer wheel's live updates fail over LAN. Also handles first-time setup on a fresh Windows machine.
---

You diagnose and fix PickerWheel's hosting on a Windows laptop: a docker-compose
stack (app on port 9080) exposed publicly through a Cloudflare Tunnel at
`https://pickerwheel.mytmobiles.com`, with Cloudflare Access (email one-time-PIN
login) in front. Work through the layers below in order, fix what you can,
verify each fix with the real checks listed here, and finish with a short report.

## Known setup (as of 2026-09-27)

| Thing | Value |
|---|---|
| Repo | `C:\Users\store\Documents\pickerwheel-v1-docker-version` |
| Tunnel name / ID | `pickerwheel-admin` / `df80fe61-1b18-4778-94d8-6dddc8ece52a` |
| Service config (what the service actually reads) | `C:\Windows\System32\config\systemprofile\.cloudflared\config.yml` |
| Service credentials | same folder, `df80fe61-1b18-4778-94d8-6dddc8ece52a.json` |
| User-profile copies (used for manual runs + `cloudflared tunnel info`) | `C:\Users\store\.cloudflared\` (`cert.pem`, credentials JSON, `config.yml`) |
| Service command (registry ImagePath) | `"C:\Program Files (x86)\cloudflared\cloudflared.exe" --config "C:\Windows\System32\config\systemprofile\.cloudflared\config.yml" tunnel run` |
| Service log | `C:\ProgramData\cloudflared\cloudflared.log` (JSON lines) |
| Readiness endpoint | `http://127.0.0.1:20241/ready`: `readyConnections` > 0 means the tunnel is up |
| Ingress | `pickerwheel.mytmobiles.com` → `http://localhost:9080` |
| Cloudflare Access | Configured by hostname in the Cloudflare dashboard. Do not touch. |

If any of this no longer matches (for example, a different tunnel ID in the config), trust
what you observe and say so in the report.

## Lessons that cost real time; do not repeat them

1. **A 302 from the public URL proves nothing about the tunnel.** Access answers
   unauthenticated requests at Cloudflare's edge with a 302 to its login page
   *before* traffic reaches the tunnel. A dead tunnel still returns 302 to curl, while
   a logged-in browser gets Error 1033. Tunnel health is only proven by `/ready`
   showing `readyConnections` > 0 **and** `cloudflared tunnel info pickerwheel-admin`
   listing a connector. Never dismiss a "no active connection" result as a quirk.
2. **`cloudflared service install` is broken for locally-managed tunnels on
   Windows.** It registers the exe with *no arguments* (the service runs but never
   starts a tunnel) and rewrites `C:\Program Files (x86)\cloudflared\config.yml` as a
   one-line `logDirectory` stub on every start. Editing that file does nothing. The fix
   is the ImagePath + systemprofile config above (see "Elevated repair script").
3. **Brief WiFi drops are normal and self-heal.** Re-authentication events on the WiFi
   drop all QUIC connections, and cloudflared re-registers them within roughly a minute.
   Before restarting anything, check the log for `Registered tunnel connection` entries
   after the errors, then re-check `/ready`.
4. **The router's DNS can cache "does not exist" for a new record.** On the original
   network the router (`192.168.1.1`) kept returning NXDOMAIN long after
   1.1.1.1 and 8.8.8.8 resolved the record. To work around this, the laptop's `Wi-Fi` adapter was
   pinned to DNS `1.1.1.1, 8.8.8.8`. That pin applies on every network. If a new network
   blocks outside DNS (captive portal, corporate firewall), nothing will resolve, so
   test it and reset it if needed (see Layer 3).
5. **The LAN IP is baked into `ALLOWED_ORIGINS`.** Socket.IO rejects the customer
   wheel's live-update connection with `"Not an accepted origin."` (HTTP 400) unless
   `http://<current LAN IP>:9080` is listed in `ALLOWED_ORIGINS` in `docker-compose.yml`.
   The page itself still loads, so this failure is easy to miss. Every new network means a new IP.

## Running commands

- Use the PowerShell tool. After any install, refresh PATH first:
  `$env:Path = [Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [Environment]::GetEnvironmentVariable('Path','User')`
- Use `curl.exe` (not the PowerShell `curl` alias).
- **You are not admin.** Anything touching services, the registry, `System32`, or
  network adapter settings needs elevation. Write the commands to a `.ps1` under
  `$env:TEMP\pickerwheel-doctor\` that starts with `Start-Transcript` to a log file,
  then run:
  `Start-Process powershell -Verb RunAs -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"<script>`"" -Wait`
  in the background. That shows a UAC prompt on the laptop's screen, and a person must click Yes.
  Put every elevated change you need into **one** script so there is one prompt, tell the user
  a UAC prompt is waiting, then poll the transcript log until it ends (give up after
  about 3 minutes and report that elevation was not approved). Read the transcript to confirm
  each step succeeded.

## Diagnosis, layer by layer

Run the checks for each layer, fix any failure, re-check, then move to the next layer.

### Layer 1: App (Docker)
- `docker ps` shows `pickerwheel-app` Up and `pickerwheel-db` healthy. If Docker itself
  errors, Docker Desktop isn't running: start it
  (`Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"`) and wait for
  `docker info` to succeed.
- Check that Docker Desktop is set to start on login, otherwise the app stays down after
  a reboot until someone opens it. One signal is not enough here — `AutoStart` in
  `%APPDATA%\Docker\settings-store.json` (or `settings.json` on older versions) can say
  `false` while an HKCU `Run` entry still launches it, and Docker Desktop may rewrite that
  file while it's running. Check both:
  `Get-ItemProperty 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run' -Name "Docker Desktop" -ErrorAction SilentlyContinue`
  and the JSON's `AutoStart` value, and if they disagree, say so rather than picking one.
  Comparing the Docker Desktop process start time to the last logon time (`Get-CimInstance
  Win32_OperatingSystem | select LastBootUpTime`, or `quser` for last logon) can help judge
  whether it actually launched at login, but isn't proof either way if the machine hasn't
  rebooted recently. The reliable fix is just telling the user to check Settings > General >
  "Start Docker Desktop when you sign in" — no elevation needed, and it settles the ambiguity
  directly.
- If containers are missing or stopped, run `docker compose up -d` from the repo.
- `docker top pickerwheel-app` must show `gunicorn --worker-class gthread --workers 1 --threads 16`.
  If it shows `python main.py`, the container is stale: run `docker compose up -d --build`.
- `curl.exe -s -o NUL -w "%{http_code}" http://localhost:9080/app` and `/admin` must both return 200.

### Layer 2: LAN access for customers
- Current IP — prefer the adapter with a default gateway, which `Select -First 1` on a
  plain address list doesn't guarantee (order isn't fixed, and it can still catch a
  disconnected or virtual adapter):
  `(Get-NetIPConfiguration | ? { $_.IPv4DefaultGateway }).IPv4Address.IPAddress`
  Take the first result if there's more than one (e.g. WiFi + Ethernet both up), and say so.
- `http://<ip>:9080/app` should return 200.
- Origin check:
  `curl.exe -s -H "Origin: http://<ip>:9080" "http://<ip>:9080/socket.io/?EIO=4&transport=polling"`
  should return a body starting with `0{"sid":`. If it returns `"Not an accepted origin."`, add
  `http://<ip>:9080` to the `ALLOWED_ORIGINS` line in `docker-compose.yml`. Keep the existing
  entries, especially `https://pickerwheel.mytmobiles.com`. Then run
  `docker compose up -d pickerwheel` and re-run the origin check.
  Leave this edit uncommitted and mention it in the report. It's machine- and network-specific.
- Report the customer URL: `http://<ip>:9080/app`.

### Layer 3: DNS
- `Resolve-DnsName pickerwheel.mytmobiles.com` (system resolver) and
  `Resolve-DnsName pickerwheel.mytmobiles.com -Server 1.1.1.1`.
- If the system resolver fails but 1.1.1.1 works: check `Get-DnsClientServerAddress -InterfaceAlias 'Wi-Fi' -AddressFamily IPv4`.
  If it's the router, the router has probably cached a stale answer. Pin to public DNS elevated:
  `Set-DnsClientServerAddress -InterfaceAlias 'Wi-Fi' -ServerAddresses ('1.1.1.1','8.8.8.8'); ipconfig /flushdns`.
- If **both** fail, and the adapter is pinned to 1.1.1.1/8.8.8.8, the network is probably
  blocking outside DNS. Reset to the network's own DNS elevated:
  `Set-DnsClientServerAddress -InterfaceAlias 'Wi-Fi' -ResetServerAddresses; ipconfig /flushdns`, then re-test.
- Also resolve `region1.v2.argotunnel.com`. cloudflared needs it, and a failure here
  explains a dead tunnel.
- If the laptop is on Ethernet instead of Wi-Fi, use that adapter's InterfaceAlias.

### Layer 4: Outbound connectivity to Cloudflare
- cloudflared connects **out** on port 7844 (UDP for QUIC, TCP for http2). It needs no
  inbound ports or router configuration.
- `Test-NetConnection region1.v2.argotunnel.com -Port 7844` checks TCP.
- UDP can't be tested directly. Read the most recent `CONNECTIVITY PRE-CHECKS` block in the
  service log — it reports DNS / UDP / TCP / API as PASS or FAIL once, right after each
  service start, so a block from hours ago can be stale; a fresh restart produces a fresh one.
  `Select-String` is case-insensitive by default, so filtering for `FAIL` also matches
  unrelated runtime lines like "**Fail**ed to accept" and pushes the actual pre-check block
  out of a head-limited result — pull the whole block by anchoring on its header instead:
  `Select-String $log 'CONNECTIVITY PRE-CHECKS' -Context 0,12 | Select -Last 1`.
  A `Registered tunnel connection` line with `"protocol":"quic"` at the current session's
  timestamp is equally good evidence that UDP works, without needing the pre-check block at all.
- UDP blocked but TCP OK: set `protocol: http2` in the service config (run the repair
  script with `-Protocol http2`).
- Both blocked: this can't be fixed from the laptop. Tell the user the network's
  IT/firewall must allow outbound port 7844 (TCP and UDP) to Cloudflare, or try a phone
  hotspot to confirm the network is the cause.

### Layer 5: Tunnel service
- `Get-Service cloudflared` should be Running. `(Get-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Services\Cloudflared').ImagePath`
  must contain `--config` and `tunnel run`. If not, run the repair script (lesson 2).
- `curl.exe -s http://127.0.0.1:20241/ready` should show `readyConnections` > 0.
- `cloudflared tunnel info pickerwheel-admin` should list a connector.
- The systemprofile `config.yml` (e.g. to check it has the right tunnel ID) is only
  readable elevated — a plain `Get-Content` gives Access Denied for a non-admin session.
  Don't treat that as a failure; confirm the tunnel ID instead from evidence you can already
  read without elevation: the service log's startup `"message":"Settings: map[...]"` line,
  `/ready`'s `connectorId`, or `cloudflared tunnel info` itself.
- If readyConnections is 0: read the last ~50 log lines, comparing timestamps in UTC (the
  log's `time` field is UTC; don't compare it against `Get-Date`, which is local, or against
  file `LastWriteTime`, which is also local — mixing them makes a live tunnel look stale by
  the local UTC offset). If they show recent `Retrying connection` entries, wait 60–90s and
  re-check before restarting (lesson 3). If there is no activity for more than 2 minutes, or
  the service is stuck in StopPending, run the repair script (it force-kills and restarts).
- `sc.exe qfailure cloudflared` normally shows one RESTART action — that's `service install`'s
  default, not a problem; the repair script's three-action config takes over once it has run.
  Windows repeats a service's last configured action after the list is exhausted, so one action
  still means it restarts on every crash, not just once. Check `$LASTEXITCODE` after `sc.exe`
  calls rather than piping to `Out-Null` and assuming success — `sc.exe` doesn't raise a
  PowerShell error or trip `$ErrorActionPreference` on failure.

### Layer 6: Tunnel → app
- Look in the log for `Unable to reach the origin service` or `connection refused` against
  `localhost:9080`. That means Layer 1 is broken, even if the tunnel itself is healthy.
  A handful of these right at container startup/restart is normal (the app wasn't listening
  yet); only treat it as a live problem if it's still happening at the current timestamp.
- `curl.exe -s http://127.0.0.1:20241/metrics` has `response_by_code` and `request_errors`
  counters — cheaper evidence that the tunnel is actually forwarding successful requests than
  scanning the log by eye, and doesn't need a browser.
- Note: the ingress rule points at `localhost:9080`, which cloudflared resolves to `[::1]:9080`
  on this machine. That only works because Docker Desktop also publishes the port on `[::]:9080`
  (IPv6) — if a future Docker/WSL change stops doing that, this layer breaks with no other
  symptom. `http://127.0.0.1:9080` in the ingress config would avoid depending on that.

### Layer 7: End to end
- `curl.exe -s -o NUL -w "%{http_code}" https://pickerwheel.mytmobiles.com/` should return 302 (to
  `*.cloudflareaccess.com`). Remember lesson 1: this only proves DNS, the edge, and Access, not the tunnel.
- The final confirmation needs a person. Ask the user to open the URL in a browser, log in with an
  allow-listed email, and confirm that `/admin` and `/app` load.

## Error code cheat sheet

| Symptom | Usually means | Layer |
|---|---|---|
| Error 1033 / 530 after login | No tunnel connector is connected | 4, 5 |
| 502 / "Unable to reach origin" | Tunnel up, app down | 1, 6 |
| `DNS_PROBE` / "can't resolve" on this laptop only | Local resolver problem | 3 |
| Wheel loads over LAN but never live-updates / spin stuck | Origin rejected, or dev server instead of gunicorn | 2, 1 |
| Login page says "restricted to members of the account" | User clicked "Sign in with Cloudflare"; use the email PIN field | none (user guidance) |

## Elevated repair script (service config + restart)

Save this as `$env:TEMP\pickerwheel-doctor\repair-service.ps1` and run it elevated as described
above. Pass `-Protocol http2` when UDP is blocked. It also works for first-time
setup, once `cloudflared tunnel create` and `cloudflared service install` have run.

```powershell
param([string]$Protocol = 'auto', [string]$TunnelId = 'df80fe61-1b18-4778-94d8-6dddc8ece52a')
$ErrorActionPreference = 'Stop'
Start-Transcript -Path "$env:TEMP\pickerwheel-doctor\repair-service.log" -Force
try {
    $sysDir = Join-Path $env:WINDIR 'System32\config\systemprofile\.cloudflared'
    $logDir = 'C:\ProgramData\cloudflared'
    $exe = 'C:\Program Files (x86)\cloudflared\cloudflared.exe'
    New-Item -ItemType Directory -Force -Path $sysDir, $logDir | Out-Null
    Copy-Item "C:\Users\store\.cloudflared\$TunnelId.json" (Join-Path $sysDir "$TunnelId.json") -Force
    @"
tunnel: $TunnelId
credentials-file: $sysDir\$TunnelId.json
protocol: $Protocol
metrics: 127.0.0.1:20241
logfile: $logDir\cloudflared.log
loglevel: info

ingress:
  - hostname: pickerwheel.mytmobiles.com
    service: http://localhost:9080
  - service: http_status:404
"@ | Set-Content -Path (Join-Path $sysDir 'config.yml') -Encoding ascii
    Set-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Services\Cloudflared' -Name ImagePath `
        -Value "`"$exe`" --config `"$sysDir\config.yml`" tunnel run"
    sc.exe failure cloudflared reset= 86400 actions= restart/20000/restart/20000/restart/20000 | Out-Null
    Stop-Service cloudflared -Force -NoWait -ErrorAction SilentlyContinue
    Start-Sleep 3
    Get-Process cloudflared -ErrorAction SilentlyContinue | Stop-Process -Force
    $deadline = (Get-Date).AddSeconds(30)
    while ((Get-Service cloudflared).Status -ne 'Stopped' -and (Get-Date) -lt $deadline) { Start-Sleep 1 }
    Start-Service cloudflared
    Start-Sleep 8
    "Service status: $((Get-Service cloudflared).Status)"
} catch { "ERROR: $_" } finally { Stop-Transcript }
```

## First-time setup on a fresh machine

Follow `.claude/skills/windows-hosting-setup/SKILL.md` steps 1–3 (Docker Desktop,
`winget install --id Cloudflare.cloudflared`, clone, then `cloudflared tunnel login` → `tunnel create`
→ `tunnel route dns`). For step 4, run `cloudflared service install` elevated, then **always**
run the repair script with the new tunnel ID. The install alone does not work (lesson 2). Then run
Layers 1–7. winget's MSI install also needs a UAC approval.

## Guardrails

- Never run `cloudflared tunnel delete`, `tunnel cleanup`, or `service uninstall`. Never delete
  DNS records or change Cloudflare Access settings. If you think one of these is needed, stop and
  explain why to the user instead.
- Never print, copy into chat, or commit the credentials JSON or `cert.pem`.
- Ask before anything destructive (removing Docker volumes, `docker compose down -v`,
  resetting git state) and before entering any payment or card details anywhere.
- Don't commit or push anything. Leave repo edits uncommitted and list them in the report.

## Report format

End with:
1. A table of checks, one row per layer, with PASS / FIXED / FAIL and a one-line detail.
2. What you changed (files, service config, DNS settings), and whether each change is local
   to this machine or network.
3. Customer LAN URL and public URL.
4. Anything the user must do: approve UAC, test the browser login, ask store IT to open port 7844.
