# Docker Hub 依赖分析：参考项目 vs 我们的项目

## 问题

用户观察到：
- **参考项目**：本地构建时不会用到 `docker.io`（Docker Hub）
- **我们的项目**：本地构建时会依赖 Docker Hub（可能超时）

## 基础镜像对比

### 参考项目（addon-ssh, addon-wireguard）

```yaml
# build.yaml
build_from:
  aarch64: ghcr.io/hassio-addons/base:18.2.1
  amd64: ghcr.io/hassio-addons/base:18.2.1
  armv7: ghcr.io/hassio-addons/base:18.2.1
```

- ✅ 所有基础镜像来自 **GHCR**（GitHub Container Registry）
- ✅ 不依赖 Docker Hub

### 我们的项目

```yaml
# build.yaml
build_from:
  aarch64: ghcr.io/hassio-addons/base:18.2.1
  amd64: ghcr.io/hassio-addons/base:18.2.1
  armv7: ghcr.io/hassio-addons/base:18.2.1
```

- ✅ 所有基础镜像也来自 **GHCR**
- ✅ 理论上也不应该依赖 Docker Hub

## Dockerfile 依赖对比

### 参考项目（addon-ssh）

```dockerfile
FROM ghcr.io/hassio-addons/base:18.2.1

RUN \
    apk add --no-cache \
        docker=28.3.3-r3 \
        ...
```

- ✅ 通过 `apk add` 从 **Alpine 仓库**安装依赖
- ✅ `docker` 包来自 Alpine 仓库，不是 Docker Hub 镜像
- ✅ 不依赖 Docker Hub

### 我们的项目

```dockerfile
FROM ghcr.io/hassio-addons/base:18.2.1

RUN \
    apk add --no-cache --virtual .build-dependencies \
        wget \
        curl \
    ...
```

- ✅ 通过 `apk add` 从 **Alpine 仓库**安装依赖
- ✅ 不依赖 Docker Hub

## 为什么会有 Docker Hub 依赖？

### 可能的原因

1. **Docker 守护进程配置**
   - 如果 Docker 守护进程没有配置 GHCR 镜像加速
   - 或者 Docker 客户端默认从 Docker Hub 拉取
   - 可能会尝试从 Docker Hub 拉取基础镜像（即使配置了 GHCR）

2. **Home Assistant 构建系统**
   - Home Assistant 的构建系统可能有特殊行为
   - 可能在本地构建时会尝试从 Docker Hub 拉取某些基础镜像
   - 或者有回退机制（GHCR 失败时回退到 Docker Hub）

3. **Docker 镜像拉取策略**
   - Docker 客户端可能在某些情况下会尝试从 Docker Hub 拉取
   - 即使镜像标签明确指定了 GHCR

4. **网络配置问题**
   - 如果 GHCR 访问受限，Docker 可能会尝试从 Docker Hub 拉取
   - 或者 DNS 解析问题导致 GHCR 无法访问

## 用户之前遇到的错误

```
Client.Timeout exceeded while awaiting headers
docker.io/library/docker:28.3.3-cli
```

这个错误显示尝试从 Docker Hub 拉取 `docker:28.3.3-cli`。

但我们的 Dockerfile 中：
- ✅ 没有直接拉取 `docker:28.3.3-cli` 镜像
- ✅ 基础镜像来自 GHCR
- ✅ 依赖通过 `apk add` 安装

**可能的原因**：
- Home Assistant 的构建系统在尝试拉取某些依赖
- 或者 Docker 守护进程的配置问题
- 或者某些中间层依赖需要从 Docker Hub 拉取

## 解决方案

### 1. 配置 Docker 镜像加速器

```json
{
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com"
  ]
}
```

### 2. 确保 GHCR 访问正常

```bash
# 测试 GHCR 访问
docker pull ghcr.io/hassio-addons/base:18.2.1
```

### 3. 检查 Docker 配置

```bash
# 检查 Docker 配置
cat /etc/docker/daemon.json
```

### 4. 使用预构建镜像

- 我们的项目使用预构建镜像（有 `image` 字段）
- 安装时直接拉取预构建镜像，不需要本地构建
- 这样可以避免本地构建时的 Docker Hub 依赖问题

## 总结

**参考项目和我们的项目在配置上是相同的**：
- ✅ 都使用 GHCR 作为基础镜像源
- ✅ 都通过 Alpine 仓库安装依赖
- ✅ 理论上都不应该依赖 Docker Hub

**但实际使用中可能遇到 Docker Hub 依赖的原因**：
1. Docker 守护进程配置问题
2. Home Assistant 构建系统的特殊行为
3. 网络配置问题
4. Docker 客户端的行为差异

**建议**：
- 使用预构建镜像（避免本地构建）
- 配置 Docker 镜像加速器（如果必须本地构建）
- 确保 GHCR 访问正常

