# Changelog

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
