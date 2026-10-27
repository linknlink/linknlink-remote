# Home Assistant Add-on: LinknLink Remote

Remote access to Home Assistant through the LinknLink platform, plus optional
LinknLink cloud access.

![Supports aarch64 Architecture][aarch64-shield]
![Supports amd64 Architecture][amd64-shield]

## About

Install, start, open the add-on page and sign in with your LinknLink account.
The add-on registers this Home Assistant with LinknLink and keeps an encrypted
remote tunnel online. No port forwarding, no YAML.

## Features

- **Free remote access** after signing in with your LinknLink account
- **Sign in from the add-on page** (Home Assistant Ingress / sidebar panel);
  no credentials in the add-on options
- **Optional cloud access**, authorized per host: buy an activation code in the
  [LinknLink store](https://www.linknlink.com/products/linknlink-activation-code-for-linkhub),
  submit the order number in the add-on page and wait for review
- Automatic reconnection and clear status in the web UI
- **LAN ports for the LinknLink app** (`1691` / `1692` / `1696`) so the app can reach this Home Assistant on the local network

Cloud access is currently available for overseas (EU) LinknLink accounts only.

## Installation

1. Go to **Settings** → **Add-ons** → **Add-on Store**
2. Menu (⋮) → **Repositories**, add `https://github.com/linknlink/linknlink-remote`
3. Install **LinknLink Remote** and click **Start**
4. Click **Open Web UI** (or enable **Show in sidebar**) and sign in

See the **Documentation** tab for cloud access, upgrade notes and
troubleshooting.

## Supported architectures

- `aarch64` - ARM 64-bit (e.g. Raspberry Pi 4/5, Home Assistant Green/Yellow)
- `amd64` - x86_64 (most PCs, NUCs and VMs)

armv7 is no longer supported as of 2.0.0; armv7 installs stay on 1.2.2.

## Upgrading from 1.x

The email/password options were removed. After upgrading, open the add-on
page and sign in once. See [CHANGELOG.md](CHANGELOG.md).

## Support

- [GitHub Issues](https://github.com/linknlink/linknlink-remote/issues)
- LinknLink support

This add-on uses [frp](https://github.com/fatedier/frp) as its tunnel client.

[aarch64-shield]: https://img.shields.io/badge/aarch64-yes-green.svg
[amd64-shield]: https://img.shields.io/badge/amd64-yes-green.svg
