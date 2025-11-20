# Home Assistant Add-on: FRPC Client

Enable easy remote access to Home Assistant through the LinknLink platform.

## Getting Started

### Prerequisites

Before using this Add-on, you need:

1. A LinknLink platform account (email and password)
2. Ensure Home Assistant is running normally
3. Ensure network connection is normal

> **Tip**
> 
> If you don't have a LinknLink account yet, please register using the LinknLink APP.

### Enable Sidebar Display (Optional)

For convenient access and management, you can display the Add-on in the sidebar:

1. Go to `Settings` → `Add-ons` → `FRPC Client`
2. Enable the **Show in sidebar** option

## Configuration

### Basic Configuration

This Add-on's configuration is very simple, only requiring LinknLink platform login credentials.

#### Required Parameters

On the Add-on configuration page, you need to fill in the following information:

- **email**: Your LinknLink platform account email
- **password**: Your LinknLink platform account password

### Configuration Examples

#### Basic Example

```yaml
authentication:
  email: "your-email@example.com"
  password: "your-password"
```

> **Note**
> 
> The password field will be displayed in encrypted form in the configuration interface to protect your privacy and security.

## How It Works

FRPC Client Add-on workflow:

1. **Device Identification**: Automatically obtains device unique identifier on startup
2. **Platform Login**: Uses your provided account credentials to log in to the LinknLink platform
3. **Proxy Registration**: Automatically registers Home Assistant service (port 8123) with the platform
4. **Establish Connection**: Downloads and starts FRPC client, establishes reverse proxy tunnel (port 38123)
5. **Stay Online**: Continuously maintains connection to ensure stable remote access availability

### Device ID

Each device has a unique 32-bit device ID used to identify your Home Assistant instance on the platform.

Device ID generation rules:
- Priority: Use network interface MAC address (padded to 32 bits)
- If MAC address is unavailable, use UUID
- As a last resort, use timestamp to generate unique ID

You can view the device ID in the following locations:

1. **Log Output**: Displayed prominently on startup
   ```
   ==========================================
     Device ID: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ==========================================
   ```

## Proxy Configuration

### Default Proxy Rules

The Add-on automatically configures the following proxy rules:

| Service Name | Local Port | Remote Port | Description |
|-------------|-----------|-------------|-------------|
| HomeAssistant | 8123 | 38123 | Home Assistant Web Interface |

### Network Mode

This Add-on uses **Host network mode**, which means:

- The Add-on container directly uses the host machine's network
- Can directly access Home Assistant service at `127.0.0.1:8123`
- No additional network configuration or port mapping required

## Logging and Debugging

### View Logs

In the Add-on details page's **Logs** tab, you can see:

- Device ID information
- Login status
- Proxy registration results
- FRPC connection status
- Error messages (if any)

### Debug Level

By default, logs display critical runtime information. If you encounter issues, you can:

1. View complete log output
2. Check for error or warning messages
3. Record error messages for troubleshooting

## Troubleshooting

### Login Failure

If prompted that account or password is incorrect:

1. Confirm email and password are filled in correctly
2. Check if the account has been activated on the LinknLink platform
3. Contact administrator to confirm account status

> **Common Errors**
> 
> - **Account does not exist (status: -46009)**: Indicates the email is not registered on the platform, please register an account using the LinknLink APP
> - **Password error**: Please check if the password is correct (note case sensitivity)

### Connection Failure

If FRPC cannot establish a connection:

1. Check if network connection is normal
2. Confirm you can access `euhome.linklinkiot.com`
3. View detailed error messages in the logs
4. Try restarting the Add-on

### Proxy Registration Failure

If proxy registration returns an error:

1. Confirm login was successful (check User ID in logs)
2. View complete error response information
3. Contact technical support

## Advanced Features

### Security

This Add-on's security considerations:

1. **Password Encryption**: Password uses SHA1 + Salt encryption for transmission during login
2. **HTTPS Connection**: All API calls use HTTPS encryption
3. **Encrypted Storage**: Password is displayed in encrypted form in the configuration interface
4. **Secure Transmission**: FRPC connection uses encrypted tunnel

## Changelog

### v1.0.0

- Initial release
- Support for LinknLink platform automatic login and registration
- Automatic Home Assistant reverse proxy configuration

## Technical Support

If you encounter issues:

1. Check the troubleshooting section of this document
2. Check detailed error messages in the logs
3. Submit an issue on [GitHub Issues](https://github.com/linknlink/linknlink-remote/issues)
4. Contact LinknLink platform technical support

---

## Credits

- [FRP Project](https://github.com/fatedier/frp) - Provides reverse proxy core functionality
- LinknLink IoT Platform - Provides device management and proxy services
- Home Assistant Community - Provides Add-on development framework and support
