# Docker 镜像使用说明

本项目已改造为标准的 Docker 镜像，支持通过 docker-compose 启动。

## 前置要求

- Docker 和 Docker Compose 已安装
- LinknLink 平台账号（邮箱和密码）

## 快速开始

### 1. 准备环境变量

创建 `.env` 文件（或直接在 docker-compose.yml 中设置环境变量）：

```bash
# 必需配置
AUTH_EMAIL=your-email@example.com
AUTH_PASSWORD=your-password

# 可选配置
LOG_LEVEL=info
CONFIG_FILE=/config/frpc.toml
DATA_DIR=/data
```

### 2. 创建必要的目录

```bash
mkdir -p data
```

注意：`config` 目录不需要创建，容器会在内部创建临时配置目录。

### 3. 启动服务

```bash
docker-compose up -d
```

### 4. 查看日志

```bash
docker-compose logs -f
```

## 配置说明

### 环境变量

| 变量名 | 必需 | 默认值 | 说明 |
|--------|------|--------|------|
| `AUTH_EMAIL` | 是 | - | LinknLink 平台登录邮箱 |
| `AUTH_PASSWORD` | 是 | - | LinknLink 平台登录密码 |
| `LOG_LEVEL` | 否 | `info` | 日志级别：trace, debug, info, notice, warning, error, fatal |
| `CONFIG_FILE` | 否 | `/config/frpc.toml` | FRPC 配置文件路径 |
| `DATA_DIR` | 否 | `/data` | 数据目录路径（用于持久化设备ID等） |

### 网络模式

当前使用 **host 网络模式**，容器直接使用宿主机网络命名空间。这意味着：

- 容器可以直接访问宿主机上的服务（如 Home Assistant 的 8123 端口）
- 无需配置端口映射
- 适合需要访问宿主机本地服务的场景

### 数据持久化

以下目录会被挂载到宿主机，确保数据持久化：

- `./data` → `/data`：存储设备ID的持久化数据（确保容器重启后设备ID不变）

注意：`/config` 目录在容器内部用于存放临时配置文件（`frpc.toml`），每次启动都会重新从服务器获取，因此不需要持久化。

## 构建镜像

如果需要从源码构建镜像：

```bash
docker build -f common/Dockerfile -t linknlink-remote:latest .
```

## 停止服务

```bash
docker-compose down
```

## 查看设备ID

设备ID会保存在数据目录中：

```bash
cat data/device_id.txt
```

或者在日志中查看：

```bash
docker-compose logs | grep "Device ID"
```

## 故障排查

### 1. 登录失败

检查邮箱和密码是否正确：

```bash
docker-compose logs | grep -i "login"
```

### 2. 连接问题

检查网络连接和日志：

```bash
docker-compose logs -f
```

### 3. 查看详细日志

设置日志级别为 debug：

```bash
# 在 .env 文件中设置
LOG_LEVEL=debug

# 重启服务
docker-compose restart
```

## 注意事项

1. **网络模式**：使用 host 模式时，容器与宿主机共享网络，请确保端口不冲突
2. **数据持久化**：设备ID会保存在 `./data/device_id.txt`，删除此文件会导致生成新的设备ID
3. **安全性**：`.env` 文件包含敏感信息，请勿提交到版本控制系统

## 与 Home Assistant Add-on 版本的区别

- 不再依赖 Home Assistant Supervisor
- 使用标准 Docker 镜像（基于 Alpine Linux）
- 通过环境变量配置，而非 Home Assistant 配置界面
- 支持 docker-compose 管理
- 使用 host 网络模式，可直接访问宿主机服务
