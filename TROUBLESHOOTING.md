# 故障排除指南

## 安装失败：Docker 镜像拉取超时

如果遇到类似以下错误：
```
Can't execute command: 500 Server Error for http+docker://localhost/v1.51/images/create
Client.Timeout exceeded while awaiting headers
```

这是网络连接问题，通常是因为无法访问 Docker Hub 或 GitHub Container Registry。

### 解决方案

#### 方法 1: 配置 Docker 镜像加速器（推荐国内用户）

Home Assistant 使用 Docker 来构建和运行 Add-on。如果您的 Home Assistant 运行在中国大陆，建议配置 Docker 镜像加速器。

##### 步骤：

1. **通过 SSH 或终端访问 Home Assistant 系统**

   - 如果使用的是 Home Assistant OS，需要通过 SSH Add-on 或其他方式获取 root 访问权限

2. **编辑 Docker 守护进程配置**

   编辑或创建文件：`/etc/docker/daemon.json`

   ```json
   {
     "registry-mirrors": [
       "https://docker.mirrors.ustc.edu.cn",
       "https://hub-mirror.c.163.com",
       "https://mirror.baidubce.com"
     ]
   }
   ```

   或者使用其他镜像源：
   - 中科大：`https://docker.mirrors.ustc.edu.cn`
   - 网易：`https://hub-mirror.c.163.com`
   - 百度云：`https://mirror.baidubce.com`
   - 阿里云：需要登录后获取专属加速地址

3. **重启 Docker 服务**

   ```bash
   # 如果使用 systemd
   systemctl restart docker
   
   # 或者重启 Home Assistant
   ```

4. **重启 Home Assistant Supervisor**

   - 在 Home Assistant Web 界面中
   - 进入 **Supervisor** → **系统** → 点击 **重新启动 Supervisor**

#### 方法 2: 使用代理（如果有可用代理）

如果您的网络环境中可以使用代理：

1. **配置 Docker 代理**

   创建目录和配置文件：
   ```bash
   mkdir -p /etc/systemd/system/docker.service.d
   ```

   创建文件：`/etc/systemd/system/docker.service.d/http-proxy.conf`
   ```ini
   [Service]
   Environment="HTTP_PROXY=http://proxy.example.com:8080"
   Environment="HTTPS_PROXY=http://proxy.example.com:8080"
   Environment="NO_PROXY=localhost,127.0.0.1"
   ```

   重启 Docker：
   ```bash
   systemctl daemon-reload
   systemctl restart docker
   ```

#### 方法 3: 检查网络连接

1. **测试网络连接**

   在 Home Assistant 系统的终端中测试：
   ```bash
   # 测试 GitHub
   curl -I https://github.com
   
   # 测试 Docker Hub
   curl -I https://registry-1.docker.io/v2/
   
   # 测试 GitHub Container Registry
   curl -I https://ghcr.io
   ```

2. **检查 DNS 设置**

   确保 DNS 解析正常，可以尝试：
   - 使用公共 DNS（如 8.8.8.8, 1.1.1.1）
   - 检查防火墙设置

#### 方法 4: 等待重试

有时网络问题是暂时性的，可以：
1. 等待几分钟后重试安装
2. 检查 Home Assistant 系统日志查看详细错误信息

### 查看详细日志

如果问题持续存在，可以查看详细日志：

1. **Supervisor 日志**
   - Home Assistant Web 界面 → **Supervisor** → **系统** → **日志**

2. **Add-on 日志**
   - 在 Add-on 详情页面的 **日志** 标签页查看

3. **系统日志**
   - 通过 SSH 访问系统后：
     ```bash
     journalctl -u docker -f
     ```

## 其他常见问题

### 构建过程中下载 frp 失败

如果 Dockerfile 在下载 frp 时失败：

1. 检查 GitHub 是否可访问
2. 检查网络连接
3. 查看构建日志中的具体错误信息

### Add-on 启动失败

如果安装成功但启动失败：

1. 检查配置是否正确（特别是 `server_addr` 和 `server_port`）
2. 查看 Add-on 日志
3. 验证 frpc 可执行文件是否正确安装


## Home Assistant OS (HassOS) 用户特别注意

如果您使用的是 Home Assistant OS，系统基于只读文件系统，配置方法可能不同：

### 方法 A: 使用 SSH & Terminal Add-on（推荐）

1. **安装 Terminal & SSH Add-on**
   - 在 Add-on Store 中安装 "Terminal & SSH"

2. **获取 root 访问权限**
   ```bash
   # 通过 SSH 连接到 Home Assistant
   # 然后获取 root shell
   login
   ```

3. **配置 Docker 镜像加速器**
   ```bash
   # 对于 HassOS，需要修改特定的配置文件
   # 具体方法可能因版本而异，请查看 Home Assistant 官方文档
   ```

### 方法 B: 使用 Portainer Add-on（可视化配置）

1. **安装 Portainer Add-on**
   - 在 Add-on Store 中搜索并安装 Portainer

2. **通过 Portainer 配置 Docker**
   - 访问 Portainer Web 界面
   - 配置 Docker 镜像注册表

### 方法 C: 网络层面解决（最简单）

如果可能，在网络路由器或网关层面：
- 配置代理服务器
- 使用支持代理的路由器固件（如 OpenWrt）
- 在路由器上配置 Docker Hub 镜像加速

## 仍然无法解决？

如果以上方法都无法解决问题：

1. **检查 Home Assistant 版本**
   - 确保使用最新版本的 Home Assistant
   - 某些旧版本可能存在已知的网络问题

2. **联系社区获取帮助**
   - Home Assistant 社区论坛：https://community.home-assistant.io/
   - 提交 Issue：在 GitHub 仓库中提交问题报告

3. **使用预构建镜像版本**（如果有）
   - 如果仓库提供了预构建的镜像，可以考虑使用该版本
   - 但这需要仓库维护者预先构建镜像

