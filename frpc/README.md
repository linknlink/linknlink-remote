# FRPC Client Add-on for Home Assistant

这是一个 Home Assistant 的第三方加载项，用于运行 FRP 客户端（frpc），建立反向代理连接到 FRP 服务器。

## 功能特性

- 🚀 自动下载并安装 frpc 客户端
- ⚙️ 通过 Home Assistant 界面配置所有参数
- 📝 支持多种协议（TCP、UDP、HTTP、HTTPS、STCP、SUDP、XTCP）
- 🔐 支持 Token 认证
- 📊 可配置日志级别和保留天数
- 🏗️ 支持多种架构（aarch64、amd64、armhf、armv7、i386）

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

#### 配置示例

```json
{
  "server_addr": "frp.example.com",
  "server_port": 7000,
  "token": "your-token-here",
  "local_ip": "127.0.0.1",
  "local_port": 8123,
  "remote_port": 6000,
  "proxy_name": "homeassistant",
  "protocol": "tcp",
  "log_level": "info",
  "log_max_days": 7
}
```

### 4. 启动

1. 配置完成后，点击 **启动** 标签页
2. 点击 **启动** 按钮
3. 查看日志确认连接状态

## 使用场景

### 场景 1: 映射 Home Assistant Web 界面

```json
{
  "server_addr": "frp.example.com",
  "server_port": 7000,
  "local_ip": "127.0.0.1",
  "local_port": 8123,
  "remote_port": 6000,
  "proxy_name": "homeassistant_web",
  "protocol": "tcp"
}
```

访问方式：`frp.example.com:6000`

### 场景 2: 映射 SSH 服务

```json
{
  "server_addr": "frp.example.com",
  "server_port": 7000,
  "local_ip": "127.0.0.1",
  "local_port": 22,
  "remote_port": 6001,
  "proxy_name": "ssh",
  "protocol": "tcp"
}
```

SSH 连接：`ssh user@frp.example.com -p 6001`

### 场景 3: HTTP 反向代理

```json
{
  "server_addr": "frp.example.com",
  "server_port": 7000,
  "local_ip": "127.0.0.1",
  "local_port": 8080,
  "remote_port": 80,
  "proxy_name": "webapp",
  "protocol": "http"
}
```

访问方式：`http://webapp.frp.example.com`

## 日志查看

- 日志文件位置：`/config/frpc.log`
- 在 Home Assistant 中查看：**启动** 标签页 → **查看日志**

## 故障排除

### 连接失败

1. 检查 `server_addr` 和 `server_port` 是否正确
2. 确认 FRP 服务器正在运行
3. 检查防火墙设置
4. 如果使用 token，确认 token 是否正确

### 端口冲突

- 确保 `remote_port` 在 FRP 服务器上未被占用
- 检查 `local_port` 对应的服务是否正在运行

### 权限问题

- 确保 Add-on 有足够的权限访问本地服务
- 检查 `/config` 目录的写入权限

## 技术支持

- 问题反馈：在 GitHub 仓库提交 Issue
- FRP 官方文档：https://gofrp.org/docs/

## 许可证

本项目遵循相应的开源许可证。

## 更新日志

### v1.0.0

- 初始版本
- 支持基本的 TCP/UDP/HTTP/HTTPS 协议
- 支持 Token 认证
- 可配置日志级别
