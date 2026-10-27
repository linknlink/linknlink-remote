# Changelog

## 2.0.5

- **ha2devicehub WebSocket id_reuse fix:** outbound Home Assistant WebSocket
  command ids are now assigned and queued atomically, and stale write-queue
  messages are drained on reconnect. This stops intermittent
  `id_reuse` / "Identifier values have to increase" failures when refreshing
  the device registry after connect or reconnect.


## 2.0.4

- **Boot cloud-connect auto-retry:** if the initial cloud uplink handshake fails
  at add-on start, the add-on now retries automatically (15s → 30s → 60s → 2m →
  4m, then every 5m) until connected, or until there is no signed-in account /
  auto-connect is off. `/cloudaccess/info` may show `connection.state` of
  `connecting`, `failed`, `retry_wait` (with next retry time), or `connected`.


## 2.0.3

- **`/cloudaccess/info` fills account fields:** when a LinknLink account is
  signed in, the response now includes `userid` and `username` (nickname when
  set, otherwise the login account). Both clear after logout. `devtype` remains
  `"HAOS"`.


## 2.0.2

- **Device type in `/cloudaccess/info`:** the response now includes
  `"devtype": "HAOS"` so the LinknLink app can recognise this add-on as a
  Home Assistant host (rather than HomeClaw) and pick the matching LAN APIs.

## 2.0.1

- **LAN ports for the LinknLink app:** host ports `1691` (ha2devicehub), `1692`
  (iegcloudaccess) and `1696` (linknlinkedge) are exposed so the mobile app can
  talk to the add-on on the local network.
- **App account sync:** the add-on accepts the same app-sync flow as HomeClaw, so
  the LinknLink app can bind / refresh the signed-in account over LAN.
- **SQLite fixes** for state list and upsert (`/linknlinkedge/api/states` no
  longer fails with MySQL-only `FORCE INDEX` / `ON DUPLICATE KEY` SQL).
- **SQLite stability:** busy timeout, WAL mode and a single writer connection
  to reduce intermittent `database is locked` errors under concurrent writes.

## 2.0.0

Major rewrite. Please read before upgrading.

- **Sign in from the add-on page.** The `authentication` email/password options
  are gone. Open the add-on (or the **LinknLink Remote** sidebar panel) and sign
  in with your LinknLink account. Credentials left over from 1.x are removed
  automatically on first start.
- **Remote access stays free.** After signing in, Home Assistant is reachable
  remotely through LinknLink as before. Your existing device ID is kept, so an
  upgraded install keeps its device on the LinknLink platform.
- **New: optional LinknLink cloud access**, authorized per host (by the primary
  network interface MAC reported by Home Assistant OS / Supervisor). Buy an
  activation code in the
  [LinknLink store](https://www.linknlink.com/products/linknlink-activation-code-for-linkhub),
  submit the order number in the add-on page and wait for review. Once
  approved, cloud access stays enabled permanently for that host.
- New web UI via Home Assistant Ingress (sidebar panel).
- Remote access now follows Home Assistant's actual HTTP port (`http.server_port`,
  reported by Supervisor) instead of assuming 8123. The remote port stays
  38123. If Home Assistant uses SSL, open `https://` on the remote side.
- Base image moved to `ghcr.io/hassio-addons/debian-base`.
- **armv7 is no longer supported.** Supported architectures: `aarch64`, `amd64`.
  armv7 installs stay on 1.2.2 and receive no further updates.
- Cloud access is currently available for accounts on the overseas (EU)
  LinknLink service only.

## 1.2.2

- Last 1.x release (email/password in add-on options; aarch64, amd64, armv7).
