# 故障排除指南

## ❓ 常见问题：在 Home Assistant OS 安装 Add-on 都需要依赖 Docker 吗？

**答案：是的，所有 Add-on 都需要 Docker。**

### Home Assistant Add-on 架构

Home Assistant Add-on 系统完全基于 Docker 容器技术：

1. **所有 Add-on 都是 Docker 容器**
   - 每个 Add-on 运行在独立的 Docker 容器中
   - 容器之间相互隔离，互不影响
   - 这提供了安全性和资源隔离

2. **Supervisor 依赖 Docker**
   - Home Assistant Supervisor 是管理 Add-on 的核心服务
   - Supervisor 使用 Docker Engine 来：
     - 构建 Add-on 镜像（本地构建模式）
     - 拉取预构建镜像（如果有）
     - 创建和运行容器
     - 管理容器的生命周期（启动、停止、重启）
     - 监控容器状态

3. **安装过程**
   - 本地构建：Supervisor 使用 Docker 构建工具（`docker:28.3.3-cli`）从 Dockerfile 构建镜像
   - 预构建镜像：Supervisor 直接从镜像仓库（如 ghcr.io）拉取镜像
   - 运行：Supervisor 使用 `docker run` 创建并启动容器

### 架构层次

```
Home Assistant OS
├── Home Assistant Core (主程序)
├── Supervisor (Add-on 管理器)
├── Docker Engine (容器运行时) ← 必需的基础组件
└── Add-ons (Docker 容器)
    ├── SSH Add-on (容器)
    ├── WireGuard Add-on (容器)
    ├── FRPC Add-on (容器)
    └── ...
```

### 为什么需要 Docker 镜像加速器？

由于所有 Add-on 都依赖 Docker，而构建和运行 Add-on 需要：

1. **构建工具镜像**：`docker:28.3.3-cli`（Supervisor 使用）
2. **基础镜像**：`ghcr.io/hassio-addons/base:18.2.1`（我们的 Dockerfile 使用）
3. **预构建镜像**：如果 Add-on 使用预构建镜像，需要从镜像仓库拉取

如果无法访问 Docker Hub（`docker.io`）或 GitHub Container Registry（`ghcr.io`），就会导致：

- 构建工具无法下载
- 基础镜像无法拉取
- 预构建镜像无法拉取

**因此，配置 Docker 镜像加速器是解决安装问题的关键步骤。**

### 如何查看 Docker 进程？

**重要提示：** 如果您在 SSH Add-on 容器内执行 `ps -ef`，**看不到 Docker 进程是正常的**。

**原因：**

1. **您当前在容器内部**
   - SSH Add-on 本身就是一个 Docker 容器
   - 容器内的 `ps` 只能看到容器内的进程
   - 看不到主机系统（Home Assistant OS）上的进程

2. **Docker 守护进程运行在主机上**
   - `dockerd` 和 `containerd` 运行在 Home Assistant OS 主机上
   - 不在 Add-on 容器内部

3. **架构示意**
   ```
   Home Assistant OS (主机)
   ├── dockerd ← Docker 守护进程在这里
   ├── containerd
   └── Docker 容器
       └── SSH Add-on 容器 ← 您在这里
           ├── sshd
           ├── ttyd
           └── s6-supervise
   ```

**如何查看 Docker 进程：**

方法 1: 通过 `login` 切换到主机系统
```bash
# 在 SSH Add-on 容器中执行
login
# 输入 root（如果需要密码，输入密码）

# 现在您在主机系统上了
ps aux | grep dockerd
systemctl status docker
docker ps
```

方法 2: 检查当前环境
```bash
# 查看当前路径（容器内通常是 /addons/xxx）
pwd

# 查看系统信息
cat /etc/os-release

# 尝试访问 Docker（可能受保护模式限制）
which docker
docker ps  # 如果保护模式开启，会显示警告
```

方法 3: 在主机上直接查看（如果有物理访问）
```bash
# 在 Home Assistant OS 主机上执行
ps aux | grep -E "dockerd|containerd"
systemctl status docker
```

---

## ❓ 常见问题：为什么官方 Add-on 可以安装，而我的 Add-on 不行？

**问题：** 为什么 Home Assistant 官方的 Add-on（如 SSH、WireGuard）可以正常安装，而我们的 Add-on 会出现 Docker 镜像拉取超时错误？

**答案：**

1. **构建工具镜像缓存**
   - 错误信息中的 `docker:28.3.3-cli` 是 Home Assistant Supervisor 构建系统使用的 Docker CLI 工具镜像
   - 如果之前安装过其他 Add-on，这个镜像可能已经缓存在系统中
   - 首次安装任何**本地构建**的 Add-on 时都可能遇到这个问题
   - 官方 Add-on 可能是在系统已有缓存后安装的，所以没有这个问题

2. **预构建镜像 vs 本地构建**
   - 某些官方 Add-on 可能使用了预构建镜像（即使 `config.yaml` 中没有 `image` 字段）
   - 官方仓库可能在 GitHub Actions 中预构建镜像，存储在镜像仓库中
   - 我们的 Add-on 使用本地构建模式，需要从 Docker Hub 拉取基础镜像

3. **网络访问差异**
   - 官方 Add-on 构建时的网络条件可能更好
   - 或者之前下载过相关镜像，已有缓存

4. **解决方案相同**
   - **所有本地构建的 Add-on 都需要配置 Docker 镜像加速器**（如果无法访问 Docker Hub）
   - 配置后，无论是官方 Add-on 还是第三方 Add-on，都可以正常安装

**结论：** 这不是我们 Add-on 配置的问题，而是所有本地构建 Add-on 在无法访问 Docker Hub 时都会遇到的问题。配置 Docker 镜像加速器后即可解决。

---

## ❓ 常见问题：为什么我的 Add-on 要访问 Docker Hub？

**问题：** 我的 Add-on 代码中没有直接使用 Docker Hub 的镜像，为什么安装时还需要访问 Docker Hub？

**答案：**

### 不是您的 Add-on 直接访问，而是构建过程需要

虽然您的 Add-on 代码不直接访问 Docker Hub，但 **Home Assistant Supervisor 在构建您的 Add-on 时需要访问**。

### 构建过程需要的资源

1. **Supervisor 构建工具（必须）**
   - `docker:28.3.3-cli` 是 Supervisor 用来执行 `docker build` 的工具镜像
   - 所有**本地构建**的 Add-on 都需要这个工具
   - 这个工具镜像来自 **Docker Hub** (`docker.io/library/docker:28.3.3-cli`)
   - **这是导致超时错误的主要原因**

2. **基础镜像（必须）**
   - 您的 Dockerfile 中指定：`FROM ghcr.io/hassio-addons/base:18.2.1`
   - 来自 **GitHub Container Registry** (`ghcr.io`)
   - 这是构建的基础镜像

3. **应用依赖（根据 Dockerfile）**
   - 例如：从 GitHub Releases 下载 frp 二进制文件
   - 来自 **GitHub** (`github.com`)

### 构建流程示意

```
┌─────────────────────────────────────────┐
│  Home Assistant Supervisor              │
│                                         │
│  1. 拉取构建工具                        │
│     docker pull docker:28.3.3-cli      │ ← 需要访问 Docker Hub
│                                         │
│  2. 使用工具构建您的 Add-on             │
│     docker build -f Dockerfile ...     │
│       ↓                                 │
│       FROM ghcr.io/hassio-addons/       │ ← 需要访问 ghcr.io
│       base:18.2.1                      │
│                                         │
│  3. 执行 Dockerfile 中的 RUN 命令      │
│     下载 frp 等依赖                     │ ← 需要访问 GitHub
│                                         │
└─────────────────────────────────────────┘
```

### 为什么官方 Add-on 可能没有这个问题？

1. **预构建镜像**
   - 某些官方 Add-on 可能使用预构建镜像
   - 安装时直接拉取镜像，不需要构建过程
   - 但仍然需要访问镜像仓库

2. **镜像缓存**
   - 如果之前安装过其他 Add-on，`docker:28.3.3-cli` 可能已缓存
   - 不需要重新下载

3. **网络条件**
   - 构建时的网络条件可能更好
   - 或者已经下载过相关镜像

### 解决方案

**配置 Docker 镜像加速器**可以解决 Docker Hub 访问问题：

- 构建工具镜像 (`docker:28.3.3-cli`) 可以通过镜像加速器下载
- 基础镜像 (`ghcr.io`) 通常不需要加速（GitHub 访问正常）
- 应用依赖（GitHub）通常不需要加速

**总结：** 即使您的 Add-on 代码不直接使用 Docker Hub，构建过程仍然需要访问 Docker Hub 来获取构建工具。这是 Home Assistant Add-on 系统的架构决定的，不是您代码的问题。

---

## ❓ 常见问题：为什么参考的官方 Add-on 不需要 Docker Hub？

**问题：** 为什么 addon-ssh 和 addon-wireguard 这些官方 Add-on 可以正常安装，不需要访问 Docker Hub？

**答案：**

### 关键区别：预构建镜像 vs 本地构建

1. **官方 Add-on 使用预构建镜像**
   - 官方 Add-on 通过 **GitHub Actions** 在 CI/CD 中预构建镜像
   - 预构建的镜像存储在 **GitHub Container Registry** (`ghcr.io`)
   - 安装时，Supervisor 直接拉取预构建镜像
   - **不需要本地构建过程**
   - **因此不需要 `docker:28.3.3-cli` 构建工具**
   - **不需要访问 Docker Hub**

2. **您的 Add-on 使用本地构建**
   - 您的 GitHub Actions 工作流已禁用（`build-and-push.yml.disabled`）
   - Supervisor 需要在本地构建镜像
   - **需要 `docker:28.3.3-cli` 构建工具**
   - **因此需要访问 Docker Hub**

### 对比说明

| 项目 | 构建方式 | 需要 Docker Hub | 原因 |
|------|---------|----------------|------|
| 官方 Add-on | 预构建镜像 | ❌ 不需要 | 直接拉取预构建镜像，不需要构建工具 |
| 您的 Add-on | 本地构建 | ✅ 需要 | 需要构建工具 `docker:28.3.3-cli` |

### 验证方法

检查官方 Add-on 的 GitHub 仓库：
- 查看 `.github/workflows/` 目录
- 通常有 `build-and-push.yml` 或类似的 CI/CD 工作流
- 这些工作流会在每次提交时自动构建并推送镜像到 `ghcr.io`

### 解决方案

您有两个选择：

**方案 1: 配置 Docker 镜像加速器（推荐，当前方案）**
- 解决 Docker Hub 访问问题
- 保持本地构建模式
- 适合开发和测试

**方案 2: 启用预构建镜像（生产环境推荐）**
- 恢复 GitHub Actions 工作流
- 在 CI/CD 中自动构建镜像
- 用户安装时直接拉取镜像，不需要本地构建
- 不需要访问 Docker Hub
- 安装速度更快

**总结：** 官方 Add-on 不需要 Docker Hub 是因为它们使用预构建镜像，而您的 Add-on 使用本地构建模式，所以需要构建工具，因此需要访问 Docker Hub。

---

## ⚠️ 重要提示：Docker 保护模式

**如果您在诊断时看到 "PROTECTION MODE ENABLED!" 警告，请先执行以下步骤：**

1. 打开 Home Assistant Web 界面
2. 进入 **设置** → **加载项** → **Terminal & SSH**（或您使用的 SSH Add-on）
3. 找到 **保护模式 (Protection mode)** 开关
4. **关闭保护模式**
5. **重启 SSH Add-on**
6. 然后才能配置 Docker 镜像加速器

**警告：** 关闭保护模式后，Add-on 可以访问 Docker，具有更高的系统权限。请确保您知道自己在做什么。

---

## ⚠️ 安装失败：Docker 镜像拉取超时（最常见问题）

如果遇到类似以下错误：
```
Can't execute command: 500 Server Error for http+docker://localhost/v1.51/images/create
Client.Timeout exceeded while awaiting headers
```

这是网络连接问题，通常是因为无法访问 Docker Hub 或 GitHub Container Registry。

### 从 SSH Add-on 容器内修改主机 Docker 配置

**如果您在 SSH Add-on 容器内，无法通过 `login` 访问主机，可以使用以下方法：**

#### 方法 A: 通过主机文件系统挂载点（推荐）

Home Assistant OS 通常会将主机文件系统挂载到容器的某个路径：

1. **检查挂载点**
   ```bash
   # 查看挂载信息
   mount | grep -E "overlay|/mnt|/host"
   
   # 查看 /mnt 目录
   ls -la /mnt/
   
   # 常见的主机挂载点：
   # - /mnt/data (Home Assistant 数据目录)
   # - /host (某些版本)
   ```

2. **找到主机文件系统路径**
   ```bash
   # 检查常见路径
   ls -la /mnt/data/docker/ 2>/dev/null
   ls -la /host/etc/docker/ 2>/dev/null
   ```

3. **修改配置文件**
   
   如果主机文件系统挂载在 `/mnt/data`：
   ```bash
   # 创建配置目录（如果需要）
   mkdir -p /mnt/data/docker
   
   # 创建或编辑配置文件
   cat > /mnt/data/docker/daemon.json << 'EOF'
   {
     "registry-mirrors": [
       "https://docker.mirrors.ustc.edu.cn",
       "https://hub-mirror.c.163.com",
       "https://mirror.baidubce.com"
     ]
   }
   EOF
   
   # 然后需要将配置文件复制到主机系统的正确位置
   # 这可能需要通过其他方式完成
   ```

#### 方法 B: 直接访问（如果容器有权限）

某些配置下，容器可能直接访问主机的 `/etc/docker`：

```bash
# 尝试直接访问
ls -la /etc/docker/

# 如果存在，直接编辑
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

**注意：** 这种方法可能不工作，因为容器内的 `/etc/docker` 通常是容器自己的配置，不是主机的。

#### 方法 C: 使用 Home Assistant OS 的配置机制（最佳方案）

对于 Home Assistant OS，推荐使用官方支持的配置方式：

1. **通过 Home Assistant 配置**

   在 Home Assistant Web 界面：
   - **设置** → **系统** → **硬件**
   - 查看是否有 Docker 相关配置选项

2. **通过 Supervisor API**（高级）

   如果熟悉 API，可以通过 Supervisor API 配置。

3. **物理访问主机**（如果可能）

   如果设备可以物理访问：
   - 使用 USB 键盘连接到设备
   - 通过显示器访问控制台
   - 直接在主机的 shell 中配置

#### 方法 D: 创建辅助脚本（临时方案）

如果您可以执行命令，创建一个脚本让 Supervisor 执行：

```bash
# 这个脚本需要在主机系统上执行
# 可能需要通过其他方式部署
```

**推荐方案：** 如果 `login` 无法使用，最可靠的方法是：

1. 尝试在 SSH Add-on 容器中查找主机文件系统挂载点
2. 如果找不到，考虑：
   - 重新启动 SSH Add-on，尝试再次使用 `login`
   - 通过 Home Assistant Web 界面检查是否有其他配置方式
   - 如果有物理访问，直接在主机上配置

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

**因此，配置 Docker 镜像加速器是解决安装问题的关键步骤。**

### 如何查看 Docker 进程？

**重要提示：** 如果您在 SSH Add-on 容器内执行 `ps -ef`，**看不到 Docker 进程是正常的**。

**原因：**

1. **您当前在容器内部**
   - SSH Add-on 本身就是一个 Docker 容器
   - 容器内的 `ps` 只能看到容器内的进程
   - 看不到主机系统（Home Assistant OS）上的进程

2. **Docker 守护进程运行在主机上**
   - `dockerd` 和 `containerd` 运行在 Home Assistant OS 主机上
   - 不在 Add-on 容器内部

3. **架构示意**
   ```
   Home Assistant OS (主机)
   ├── dockerd ← Docker 守护进程在这里
   ├── containerd
   └── Docker 容器
       └── SSH Add-on 容器 ← 您在这里
           ├── sshd
           ├── ttyd
           └── s6-supervise
   ```

**如何查看 Docker 进程：**

方法 1: 通过 `login` 切换到主机系统
```bash
# 在 SSH Add-on 容器中执行
login
# 输入 root（如果需要密码，输入密码）

# 现在您在主机系统上了
ps aux | grep dockerd
systemctl status docker
docker ps
```

方法 2: 检查当前环境
```bash
# 查看当前路径（容器内通常是 /addons/xxx）
pwd

# 查看系统信息
cat /etc/os-release

# 尝试访问 Docker（可能受保护模式限制）
which docker
docker ps  # 如果保护模式开启，会显示警告
```

方法 3: 在主机上直接查看（如果有物理访问）
```bash
# 在 Home Assistant OS 主机上执行
ps aux | grep -E "dockerd|containerd"
systemctl status docker
```

---

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

