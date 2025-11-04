# Home Assistant Docker 镜像加速器配置指南

本指南适用于在 VirtualBox 中安装的 Home Assistant OS，用于配置 Docker 镜像加速器以解决镜像拉取超时问题。

## 前提条件

1. 已安装 Home Assistant OS（通过 VirtualBox）
2. 已安装 **SSH & Web Terminal** 或 **Terminal & SSH** Add-on
3. 能够通过 SSH 访问 Home Assistant 系统

## 方法 1：通过 SSH Add-on 配置（推荐）

### 步骤 1：安装 SSH Add-on

1. 在 Home Assistant Web 界面中，进入 **Supervisor** → **加载项商店**
2. 搜索并安装 **"SSH & Web Terminal"** 或 **"Terminal & SSH"**
3. 启动 Add-on 并启用 **"Show in sidebar"**（可选）

### 步骤 2：通过 SSH 访问系统

1. 打开 SSH 终端（通过 Web 界面或使用 SSH 客户端）
2. 登录到系统（Home Assistant OS 默认用户名是 `root`，可能不需要密码）

### 步骤 3：配置 Docker 镜像加速器

在 SSH 终端中执行以下命令：

```bash
# 创建或编辑 Docker 守护进程配置文件
mkdir -p /etc/docker
cat > /etc/docker/daemon.json << 'EOF'
{
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com",
    "https://mirror.baidubce.com"
  ]
}
EOF
```

**国内常用镜像加速器地址：**
- 中科大镜像：`https://docker.mirrors.ustc.edu.cn`
- 网易镜像：`https://hub-mirror.c.163.com`
- 百度云镜像：`https://mirror.baidubce.com`
- 阿里云镜像：需要登录阿里云获取专属加速地址（推荐）
- Docker 官方中国镜像：`https://registry.docker-cn.com`（已停止服务）

### 步骤 4：重启 Docker 服务

```bash
# 重启 Docker 守护进程
systemctl restart docker

# 或者重启整个 Home Assistant 系统（推荐）
ha host reboot
```

### 步骤 5：验证配置

```bash
# 检查 Docker 配置
cat /etc/docker/daemon.json

# 检查 Docker 信息（查看镜像加速器是否生效）
docker info | grep -A 5 "Registry Mirrors"
```

## 方法 2：通过 Home Assistant 系统设置配置

### 步骤 1：启用高级模式

1. 进入 **设置** → **系统**
2. 启用 **高级模式**

### 步骤 2：通过 Supervisor 配置

1. 进入 **Supervisor** → **系统**
2. 点击右上角的 **⋮** 菜单
3. 选择 **硬件**
4. 查看系统信息，找到 Docker 相关配置

**注意：** Home Assistant OS 的 Docker 配置可能需要通过 SSH 直接修改，因为 UI 界面可能不提供此选项。

## 方法 3：使用环境变量配置代理（如果使用代理）

如果您的 Home Assistant 服务器需要通过代理访问外网，可以配置 Docker 代理：

```bash
# 创建 Docker 服务目录
mkdir -p /etc/systemd/system/docker.service.d

# 创建代理配置文件
cat > /etc/systemd/system/docker.service.d/http-proxy.conf << 'EOF'
[Service]
Environment="HTTP_PROXY=http://127.0.0.1:7897"
Environment="HTTPS_PROXY=http://127.0.0.1:7897"
Environment="NO_PROXY=localhost,127.0.0.1,172.17.0.0/16"
EOF

# 重新加载 systemd 配置
systemctl daemon-reload

# 重启 Docker 服务
systemctl restart docker
```

## 阿里云镜像加速器配置（推荐）

阿里云提供专属的 Docker 镜像加速器，速度更快更稳定：

### 获取专属加速地址

1. 登录 [阿里云容器镜像服务控制台](https://cr.console.aliyun.com/)
2. 进入 **镜像工具** → **镜像加速器**
3. 选择您的地域，复制专属加速地址
4. 按照上述方法配置到 `/etc/docker/daemon.json`

示例配置：

```json
{
  "registry-mirrors": [
    "https://your-aliyun-mirror.mirror.aliyuncs.com"
  ]
}
```

## 验证配置是否生效

配置完成后，尝试重新安装 FRPC Client Add-on：

1. 进入 **Supervisor** → **加载项商店**
2. 找到 **FRPC Client**
3. 点击 **安装**

如果仍然遇到超时问题，可以：

1. 查看 Supervisor 日志：
   - **Supervisor** → **系统** → **日志**
   - 查找 Docker 相关错误信息

2. 通过 SSH 手动测试镜像拉取：
   ```bash
   docker pull ghcr.io/hassio-addons/base:14.2.0
   ```

## 常见问题

### Q: 配置后仍然无法拉取镜像？

A: 尝试以下方法：
1. 确认镜像加速器地址正确
2. 检查网络连接是否正常
3. 尝试使用不同的镜像加速器
4. 重启 Home Assistant 系统

### Q: 如何知道镜像加速器是否生效？

A: 执行 `docker info` 命令，查看 "Registry Mirrors" 部分是否显示配置的加速器地址。

### Q: 配置后需要重启整个系统吗？

A: 建议重启，以确保所有配置生效。可以执行 `ha host reboot` 或通过 Web 界面重启。

## 注意事项

1. **备份配置**：修改系统配置文件前，建议先备份
2. **权限问题**：确保使用 root 用户或具有 sudo 权限
3. **网络环境**：如果是在内网环境，确保可以访问镜像加速器地址
4. **Home Assistant OS 限制**：某些配置可能在系统更新后会被重置

## 参考资源

- [Docker 官方文档 - 配置镜像加速器](https://docs.docker.com/registry/recipes/mirror/)
- [阿里云容器镜像服务](https://cr.console.aliyun.com/)
- [Home Assistant 官方文档](https://www.home-assistant.io/docs/)
