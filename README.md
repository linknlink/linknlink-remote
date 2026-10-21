# LinknLink Remote - Home Assistant Add-ons Repository

Home Assistant community add-ons that provide a simple and secure remote access solution powered by the LinknLink platform.

## About

This repository offers Home Assistant remote access services built on top of the LinknLink IoT platform. Sign in with your LinknLink account and your Home Assistant instance becomes securely reachable from the Internet.

## Available Add-ons

### 📡 LinknLink Remote

Home Assistant add-on that delivers remote access through the LinknLink platform.

**Key highlights:**
- Free remote access: sign in with your LinknLink account in the add-on page
- Optional LinknLink cloud access, authorized per host (activation code + review)
- Secure, encrypted tunneling with automatic reconnection
- Supports aarch64 and amd64 (armv7 dropped in 2.0.0)

[![Install Add-on][addon-badge]][addon]

See detailed documentation: [frpc/README.md](frpc/README.md)

[addon-badge]: https://my.home-assistant.io/badges/supervisor_addon.svg
[addon]: https://my.home-assistant.io/redirect/supervisor_addon/?addon=a4a84f10_frpc

## Installation

### Option 1: One-click add

Click the button below to add this repository to Home Assistant:

[![Add Repository to Home Assistant][add-repo-badge]][add-repo]

[add-repo-badge]: https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg
[add-repo]: https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Flinknlink%2Flinknlink-remote

### Option 2: Manual add

1. Open Home Assistant
2. Navigate to **Settings** → **Add-ons** → **Add-on Store**
3. Click the menu icon (⋮) in the top-right corner → **Repositories**
4. Add repository URL: `https://github.com/linknlink/linknlink-remote`
5. Click **Add**

### Install an add-on

Once the repository is added, locate the desired add-on in the store and click **Install**.

## Quick Start

After installing the LinknLink Remote add-on:

1. Click **Start**
2. Click **Open Web UI** (or use the sidebar panel)
3. Sign in with your LinknLink account

More details: [frpc/README.md](frpc/README.md)

## FAQ

### How do I get a LinknLink account?

Register through the LinknLink mobile app.

### The add-on fails to start

Since 2.0.0 you sign in from the add-on page; there are no email/password options anymore.


1. Check the add-on **Log** tab for detailed error messages
2. Confirm network connectivity is working
3. Make sure the host is aarch64 or amd64 (armv7 is not supported since 2.0.0)

### Need more help?

- 📖 Review the [add-on documentation](frpc/README.md)
- 🐛 [Open an Issue](https://github.com/linknlink/linknlink-remote/issues)
- 💬 Contact LinknLink support

## Support

If you have questions or suggestions:

- File feedback via [GitHub Issues](https://github.com/linknlink/linknlink-remote/issues)
- Review the [Changelog](frpc/CHANGELOG.md) for the latest updates

---

**Note:** These add-ons require the LinknLink IoT platform to function properly.

---

Need the Chinese version? See [README-zh.md](README-zh.md).
