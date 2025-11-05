# FRPC Client Add-on for Home Assistant

这是一个 Home Assistant 的第三方加载项，用于运行 FRP 客户端（frpc），建立反向代理连接到 FRP 服务器。

## 功能特性

- 🚀 自动下载并安装 frpc 客户端
- ⚙️ 通过 Home Assistant 界面配置所有参数
- 📝 支持多种协议（TCP、UDP、HTTP、HTTPS、STCP、SUDP、XTCP）
- 🔐 支持 Token 认证
- 📊 可配置日志级别和保留天数
- 🏗️ 支持多种架构（aarch64、amd64、armv7）

## 安装方法

### 1. 添加仓库

1. 打开 Home Assistant
2. 进入 **Supervisor** → **加载项** → **加载项商店**
3. 点击右上角菜单（三个点）→ **仓库**
4. 输入仓库地址：`https://github.com/Acmen0102/linknlink-remote`
5. 点击 **添加**

### 2. 安装加载项

1. 在加载项商店中找到 **FRPC Client**
2. 点击进入详情页
3. 点击 **安装**
4. 等待安装完成

### 3. 配置

在安装完成后，点击 **配置** 标签页，设置以下参数：

#### 必需参数

- **server_addr**: FRP 服务器地址（例如：`frp.example.com` 或 `192.168.1.100`）
- **server_port**: FRP 服务器端口（默认：`7000`）

#### 可选参数

- **token**: FRP 服务器认证令牌（如果服务器启用了 token 认证）
- **local_ip**: 本地服务 IP 地址（默认：`127.0.0.1`）
- **local_port**: 本地服务端口（默认：`22`，SSH 端口）
- **remote_port**: 远程映射端口（默认：`6000`）
- **proxy_name**: 代理名称（默认：`homeassistant_proxy`）
- **protocol**: 协议类型（默认：`tcp`，可选：`tcp`、`udp`、`http`、`https`、`stcp`、`sudp`、`xtcp`）
- **log_level**: 日志级别（默认：`info`，可选：`trace`、`debug`、`info`、`warn`、`error`）
- **log_max_days**: 日志保留天数（默认：`3`，范围：1-30）

#### 高级配置（预留功能）

以下配置项为预留功能，将在后续版本中实现：

- **authentication**: 私有账号登录配置
  - **enabled**: 是否启用私有账号登录（默认：`false`）
  - **account**: 账号名称
  - **password**: 账号密码

- **third_party**: 第三方服务配置
  - **enabled**: 是否启用第三方服务（默认：`false`）
  - **provider**: 第三方服务提供商
  - **api_key**: API 密钥
  - **api_secret**: API 密钥（加密存储）

### 4. 启动

1. 配置完成后，点击 **配置** 标签页底部的 **保存**
2. 切换到 **信息** 标签页
3. 点击 **启动** 按钮
4. 查看 **日志** 标签页确认运行状态

## 使用示例

### 基本配置示例

```json
{
  "server_addr": "frp.example.com",
  "server_port": 7000,
  "token": "your_token_here",
  "local_ip": "127.0.0.1",
  "local_port": 22,
  "remote_port": 6000,
  "proxy_name": "homeassistant_ssh",
  "protocol": "tcp",
  "log_level": "info",
  "log_max_days": 7
}
```

### HTTP 协议配置示例

```json
{
  "server_addr": "frp.example.com",
  "server_port": 7000,
  "local_ip": "127.0.0.1",
  "local_port": 8123,
  "remote_port": 8080,
  "proxy_name": "homeassistant_web",
  "protocol": "http",
  "log_level": "info"
}
```

## 工作原理

FRPC Client Add-on 的工作原理：

1. **安装阶段**：从 GitHub 下载对应架构的 frpc 二进制文件
2. **配置阶段**：根据配置参数生成 frpc 配置文件（TOML 格式）
3. **运行阶段**：启动 frpc 客户端，建立到 FRP 服务器的连接
4. **监控阶段**：持续监控连接状态，自动重连（如果连接断开）

## 日志

### 查看日志

1. 在 Add-on 详情页面，点击 **日志** 标签页
2. 日志会实时显示 frpc 的运行状态和连接信息
3. 可以查看以下信息：
   - 连接状态
   - 错误信息
   - 代理配置信息

### 日志级别

- **trace**: 最详细的日志，包含所有调试信息
- **debug**: 调试信息
- **info**: 一般信息（推荐）
- **warn**: 警告信息
- **error**: 错误信息

## 故障排除

### 连接失败

如果无法连接到 FRP 服务器：

1. 检查 `server_addr` 和 `server_port` 是否正确
2. 确认网络连接正常
3. 检查 FRP 服务器是否运行
4. 查看日志中的错误信息

### Token 认证失败

如果启用了 Token 认证但连接失败：

1. 确认 `token` 配置正确
2. 检查服务器端的 Token 设置
3. 查看日志中的认证错误信息

### 端口冲突

如果遇到端口冲突：

1. 检查 `remote_port` 是否已被占用
2. 尝试使用其他端口号
3. 确认服务器端允许使用该端口

### 构建失败

如果 Add-on 安装时构建失败：

1. 检查网络连接（需要访问 GitHub 和 Docker Hub）
2. 查看 [故障排除文档](../../TROUBLESHOOTING.md)
3. 确认系统架构是否支持（aarch64、amd64、armv7）

## 支持的架构

- **aarch64**: ARM 64位架构（如树莓派 4）
- **amd64**: x86_64 架构（大多数 PC 和服务器）
- **armv7**: ARM 32位架构（较旧的 ARM 设备）

## 更新日志

### v1.0.0

- 初始版本发布
- 支持基本的 FRP 客户端功能
- 支持多种协议和架构
- 预留私有账号登录和第三方服务接口

## 技术支持

如果遇到问题，可以：

1. 查看本文档的故障排除部分
2. 查看 [故障排除文档](../../TROUBLESHOOTING.md)
3. 在 GitHub 仓库提交 Issue

## 许可证

请查看仓库根目录的许可证文件。

## 致谢

- [FRP 项目](https://github.com/fatedier/frp) - 提供反向代理解决方案
- Home Assistant 社区 - 提供 Add-on 开发支持
