# Home Assistant Add-on: LinknLink Remote

Remote access to Home Assistant through the LinknLink platform, plus optional
LinknLink cloud access.

## Requirements

- Home Assistant OS or a Supervised installation on **aarch64** or **amd64**.
  armv7 (32-bit ARM, e.g. older Raspberry Pi images) is not supported since 2.0.0.
- A LinknLink account. If you don't have one, register in the LinknLink app.

## Getting started

1. Install the add-on and click **Start**.
2. Open the add-on web UI: click **Open Web UI**, or enable **Show in sidebar**
   and use the **LinknLink Remote** panel.
3. **Sign in** with your LinknLink account (email / account and password).

That's all for remote access. The add-on registers this Home Assistant with the
LinknLink platform and keeps the remote tunnel online. Remote access is free.

Your password is only sent to the LinknLink login service. It is not stored in
the add-on options.

## Cloud access (optional)

Cloud access connects this Home Assistant to the LinknLink cloud. It is
authorized per host: the add-on identifies the host by the MAC address of its
primary network interface, as reported by Home Assistant OS / Supervisor.

To enable it:

1. Open the add-on web UI and sign in.
2. Click **Enable cloud access**.
3. Buy an activation code in the
   [LinknLink store](https://www.linknlink.com/products/linknlink-activation-code-for-linkhub).
   No device details are needed at checkout.
4. Copy your **order number**, enter it in the dialog and click **Submit request**.
5. Wait for review. The status card shows *Pending*, then *Activating* once
   approved; activation usually completes within about 15 minutes.
   If a request is rejected, the reason is shown and you can correct the order
   number and submit again.

Notes:

- Each order number can be linked to one host only.
- Once approved, cloud access stays enabled permanently for that host.
- The authorization is bound to the host's primary network interface. If you
  replace that interface or move to new hardware, the add-on shows
  **NIC changed**; contact LinknLink support to move the authorization.
- Cloud access is currently available for accounts on the overseas (EU)
  LinknLink service only.

## Configuration

Login happens in the web UI, so normally nothing needs to be configured.

```yaml
log_level: info
```

- **log_level**: `trace`, `debug`, `info` (default), `notice`, `warning`,
  `error` or `fatal`.
- **guide_url** / **purchase_url**: help and store links shown in the web UI.
  Leave the defaults.

## Upgrading from 1.x

- The `authentication` email/password options were removed. After upgrading,
  open the web UI and sign in once. Credentials left in the old options are
  removed automatically on first start.
- The existing device ID (`/data/device_id.txt`) is kept, so the device keeps
  its identity on the LinknLink platform.
- armv7 installs cannot upgrade and stay on 1.2.2.

## Troubleshooting

- **Cannot sign in**: check the account and password in the LinknLink app first.
  "Account does not exist" means the account is not registered.
- **Remote access offline**: check that the host can reach the Internet, then
  restart the add-on and look at the **Log** tab.
- **Cloud access stays "Activating"**: activation can take up to about 15
  minutes after approval. Use **Refresh** in the web UI.
- **unable to resolve primary NIC MAC** in the log: the add-on could not read the
  primary interface from Supervisor; make sure the host has a connected
  network interface and restart the add-on.

For other problems, open an issue on
[GitHub](https://github.com/linknlink/linknlink-remote/issues) with the add-on
log attached, or contact LinknLink support.

## Credits

- [frp](https://github.com/fatedier/frp) provides the tunnel client.
