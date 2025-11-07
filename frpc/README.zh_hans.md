# Home Assistant Add-on: FRPC Client

通过 LinknLink 平台实现 Home Assistant 的远程访问。

## 关于

FRPC Client 是一个简单易用的 Home Assistant 加载项，让您无需复杂配置即可实现远程访问。

它通过与 LinknLink IoT 平台集成，自动完成设备注册、代理配置和隧道建立。您只需要提供平台账号，剩下的工作交给它来完成。

**查看 [文档标签页](#) 了解更多详细信息。**

## 功能特性

- ✅ **零配置远程访问** - 只需账号密码，自动完成所有设置
- 🔐 **安全连接** - 使用加密隧道和 HTTPS 通信
- 🚀 **自动化管理** - 自动设备识别、注册和代理配置
- 📱 **多平台支持** - 支持 aarch64、amd64、armv7 等多种架构
- 🔄 **稳定可靠** - 自动重连机制，确保服务持续可用
- 📊 **清晰日志** - 详细的运行日志，方便排查问题

## 安装

### 添加仓库

1. 打开 Home Assistant
2. 进入 **设置** → **加载项** → **加载项商店**
3. 点击右上角菜单（⋮）→ **仓库**
4. 添加此仓库 URL：
   ```
   https://github.com/acmen0102/linknlink-remote
   ```
5. 点击 **添加**

### 安装 Add-on

1. 在加载项商店中找到 **FRPC Client**
2. 点击进入 Add-on 详情页
3. 点击 **安装** 按钮
4. 等待安装完成

## 配置

安装完成后，需要配置您的 LinknLink 平台账号：

### 必需配置

```yaml
authentication:
  email: "your-email@example.com"
  password: "your-password"
```

**配置说明：**

- **email**: 您的 LinknLink 平台账号邮箱
- **password**: 您的 LinknLink 平台账号密码

> **注意**：如果您还没有 LinknLink 账号，请使用LinknLink APP注册开通。

### 启动 Add-on

1. 填写配置后，点击 **保存**
2. 返回 **信息** 标签页
3. 点击 **启动** 按钮
4. 查看 **日志** 确认运行状态

## 使用

启动后，Add-on 会自动：

1. 获取设备唯一标识
2. 登录 LinknLink 平台
3. 注册 Home Assistant 代理服务
4. 建立远程访问隧道

您可以在日志中看到设备 ID 和连接状态。

**默认代理配置：**

- **服务名称**: HomeAssistant
- **本地端口**: 8123
- **远程端口**: 38123

## 支持的架构

- `aarch64` - ARM 64位（如树莓派 4）
- `amd64` - x86_64（大多数 PC 和服务器）
- `armv7` - ARM 32位（较旧的 ARM 设备）

## 文档

详细文档请查看 **文档** 标签页，包含：

- 完整的配置指南
- 工作原理说明
- 故障排除方法
- 常见问题解答

## 支持

遇到问题？

- 📖 查看 [文档标签页](#) 中的故障排除部分
- 🐛 在 [GitHub](https://github.com/acmen0102/linknlink-remote/issues) 提交 Issue
- 💬 联系 LinknLink 技术支持

## 致谢

本 Add-on 基于 [FRP](https://github.com/fatedier/frp) 项目构建。

