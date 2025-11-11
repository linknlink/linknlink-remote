# Home Assistant Add-on: FRPC Client

Enable remote access to Home Assistant through the LinknLink platform.

## About

FRPC Client is a simple and easy-to-use Home Assistant add-on that enables remote access without complex configuration.

It integrates with the LinknLink IoT platform to automatically complete device registration, proxy configuration, and tunnel establishment. You only need to provide your platform account credentials, and it will handle the rest.

**View the [Documentation tab](#) for more detailed information.**

## Features

- ✅ **Zero-configuration remote access** - Only requires account credentials, automatically completes all settings
- 🔐 **Secure connection** - Uses encrypted tunnels and HTTPS communication
- 🚀 **Automated management** - Automatic device identification, registration, and proxy configuration
- 📱 **Multi-platform support** - Supports aarch64, amd64, armv7, and other architectures
- 🔄 **Stable and reliable** - Automatic reconnection mechanism ensures continuous service availability
- 📊 **Clear logs** - Detailed runtime logs for easy troubleshooting

## Installation

### Add Repository

1. Open Home Assistant
2. Go to **Settings** → **Add-ons** → **Add-on Store**
3. Click the menu icon (⋮) in the top right → **Repositories**
4. Add this repository URL:
   ```
   https://github.com/acmen0102/linknlink-remote
   ```
5. Click **Add**

### Install Add-on

1. Find **FRPC Client** in the Add-on Store
2. Click to enter the Add-on details page
3. Click the **Install** button
4. Wait for installation to complete

## Configuration

After installation, you need to configure your LinknLink platform account:

### Required Configuration

```yaml
authentication:
  email: "your-email@example.com"
  password: "your-password"
```

**Configuration Description:**

- **email**: Your LinknLink platform account email
- **password**: Your LinknLink platform account password

> **Note**: If you don't have a LinknLink account yet, please register using the LinknLink APP.

### Optional Configuration

```yaml
log_level: info
```

- **log_level**: Controls the verbosity of add-on logs. Available values: `trace`, `debug`, `info`, `notice`, `warning`, `error`, `fatal`. Defaults to `info`.

### Start Add-on

1. After filling in the configuration, click **Save**
2. Return to the **Information** tab
3. Click the **Start** button
4. Check the **Logs** to confirm the running status

## Usage

After starting, the Add-on will automatically:

1. Get the device unique identifier
2. Log in to the LinknLink platform
3. Register the Home Assistant proxy service
4. Establish a remote access tunnel

You can see the device ID and connection status in the logs.

**Default Proxy Configuration:**

- **Service Name**: HomeAssistant
- **Local Port**: 8123
- **Remote Port**: 38123

## Supported Architectures

- `aarch64` - ARM 64-bit (e.g., Raspberry Pi 4)
- `amd64` - x86_64 (most PCs and servers)
- `armv7` - ARM 32-bit (older ARM devices)

## Documentation

For detailed documentation, please check the **Documentation** tab, which includes:

- Complete configuration guide
- How it works
- Troubleshooting methods
- Frequently asked questions

## Support

Having issues?

- 📖 Check the troubleshooting section in the [Documentation tab](#)
- 🐛 Submit an Issue on [GitHub](https://github.com/acmen0102/linknlink-remote/issues)
- 💬 Contact LinknLink technical support

## Credits

This Add-on is built based on the [FRP](https://github.com/fatedier/frp) project.
