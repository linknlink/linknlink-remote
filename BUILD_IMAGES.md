# Docker 镜像构建和发布指南

本文档说明如何构建和发布 FRPC Client Add-on 的 Docker 镜像。

## 重要说明

### 两种部署方式

**方式 1：使用预构建镜像（推荐）**
- 优点：安装快速，无需在 Home Assistant 上构建，避免网络问题
- 缺点：需要先构建并发布镜像
- 使用方法：在 `config.json` 中指定 `image` 字段，并移除或重命名 `Dockerfile`

**方式 2：使用 Dockerfile 构建**
- 优点：代码更新后自动构建，无需手动发布镜像
- 缺点：安装时需要在 Home Assistant 上构建，可能遇到网络问题
- 使用方法：在 `config.json` 中移除 `image` 字段，保留 `Dockerfile`

**当前配置：** 项目默认使用 Dockerfile 构建方式。如果您想切换到预构建镜像方式，请参考下面的"切换到预构建镜像"部分。

## 切换到预构建镜像

### 步骤 1：等待 GitHub Actions 构建完成

1. 提交并推送代码到 GitHub
2. 等待 GitHub Actions 工作流完成镜像构建
3. 查看构建的镜像：访问 `https://github.com/Acmen0102/linknlink-remote/pkgs/container/linknlink-remote-frpc`

### 步骤 2：修改 config.json

将 `config.json` 中的内容替换为 `config.json.example` 的内容，或手动添加 `image` 字段：

```json
{
  "image": "ghcr.io/acmen0102/linknlink-remote-frpc/{arch}"
}
```

### 步骤 3：移除或重命名 Dockerfile（可选）

如果使用预构建镜像，可以移除 Dockerfile（或重命名为 Dockerfile.bak）：

```bash
# 重命名 Dockerfile（保留作为备份）
mv frpc/Dockerfile frpc/Dockerfile.bak
```

### 步骤 4：提交更改

```bash
git add frpc/config.json
git commit -m "切换到预构建镜像方式"
git push
```

## 自动构建（推荐）

项目已配置 GitHub Actions 工作流，在以下情况下会自动构建镜像：

- 推送到 `main` 分支
- 创建新的 Release
- 手动触发工作流（在 GitHub Actions 页面）

### 镜像地址

构建完成后，镜像将发布到 GitHub Container Registry：

```
ghcr.io/acmen0102/linknlink-remote-frpc:latest
ghcr.io/acmen0102/linknlink-remote-frpc:1.0.0
```

**Home Assistant 使用的镜像格式：**
```
ghcr.io/acmen0102/linknlink-remote-frpc/{arch}
```

其中 `{arch}` 会被替换为：`amd64`, `aarch64`, `armhf`, `armv7`, `i386`

### 支持的架构

- `amd64` (x86_64)
- `aarch64` (ARM 64-bit)
- `armhf` (ARM v6)
- `armv7` (ARM v7)
- `i386` (x86 32-bit)

## 本地构建

### 前提条件

- 安装 Docker 和 Docker Buildx
- 确保 Docker 守护进程正在运行

### 构建单个架构镜像

```bash
# 进入项目目录
cd frpc

# 构建 amd64 架构镜像
docker buildx build \
  --platform linux/amd64 \
  --build-arg BUILD_FROM=ghcr.io/hassio-addons/base:14.2.0 \
  -t ghcr.io/acmen0102/linknlink-remote-frpc:1.0.0-amd64 \
  --load \
  .

# 构建 arm64 架构镜像
docker buildx build \
  --platform linux/arm64 \
  --build-arg BUILD_FROM=ghcr.io/hassio-addons/base:14.2.0 \
  -t ghcr.io/acmen0102/linknlink-remote-frpc:1.0.0-arm64 \
  --load \
  .
```

### 构建多架构镜像

```bash
# 创建并使用 buildx builder
docker buildx create --name multiarch --use
docker buildx inspect --bootstrap

# 登录到 GitHub Container Registry
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin

# 构建并推送多架构镜像
docker buildx build \
  --platform linux/amd64,linux/arm64,linux/arm/v6,linux/arm/v7,linux/386 \
  --build-arg BUILD_FROM=ghcr.io/hassio-addons/base:14.2.0 \
  -t ghcr.io/acmen0102/linknlink-remote-frpc:1.0.0 \
  -t ghcr.io/acmen0102/linknlink-remote-frpc:latest \
  --push \
  ./frpc
```

### 测试本地构建的镜像

```bash
# 运行容器测试
docker run --rm \
  ghcr.io/acmen0102/linknlink-remote-frpc:1.0.0-amd64 \
  frpc version
```

## 使用预构建镜像

### 方案 1：使用默认标签（latest）

在 `config.json` 中指定：
```json
{
  "image": "ghcr.io/acmen0102/linknlink-remote-frpc/{arch}"
}
```

### 方案 2：使用版本标签

```json
{
  "image": "ghcr.io/acmen0102/linknlink-remote-frpc/{arch}:1.0.0"
}
```

**注意：** 
- `{arch}` 会被 Home Assistant 自动替换为当前架构
- 使用预构建镜像时，确保已发布对应架构的镜像
- 如果同时存在 `image` 字段和 `Dockerfile`，Home Assistant 会优先使用 `image` 字段

## 发布镜像到 Docker Hub（可选）

如果需要同时发布到 Docker Hub：

```bash
# 登录 Docker Hub
docker login

# 构建并推送
docker buildx build \
  --platform linux/amd64,linux/arm64,linux/arm/v6,linux/arm/v7,linux/386 \
  --build-arg BUILD_FROM=ghcr.io/hassio-addons/base:14.2.0 \
  -t acmen0102/frpc:1.0.0 \
  -t acmen0102/frpc:latest \
  --push \
  ./frpc
```

然后在 `config.json` 中使用：
```json
{
  "image": "acmen0102/frpc:{arch}"
}
```

## 镜像大小优化

当前镜像构建步骤已经做了优化：
- 使用 Alpine Linux 基础镜像（体积小）
- 构建后清理临时文件和缓存
- 删除不必要的构建工具

如需进一步优化，可以考虑：
- 使用多阶段构建
- 合并 RUN 命令减少层数
- 使用 `.dockerignore` 排除不必要的文件

## 常见问题

### Q: 如何验证镜像是否构建成功？

A: 
```bash
# 检查镜像列表
docker images | grep frpc

# 检查镜像架构
docker inspect ghcr.io/acmen0102/linknlink-remote-frpc:1.0.0 | grep Architecture

# 在 GitHub 上查看：https://github.com/Acmen0102/linknlink-remote/pkgs/container/linknlink-remote-frpc
```

### Q: 如何在本地测试不同架构的镜像？

A: 使用 `docker run --platform` 参数：
```bash
docker run --platform linux/arm64 --rm \
  ghcr.io/acmen0102/linknlink-remote-frpc:latest \
  frpc version
```

### Q: GitHub Actions 构建失败怎么办？

A: 
1. 检查 Actions 日志中的错误信息
2. 确认 Dockerfile 语法正确
3. 确认基础镜像 `ghcr.io/hassio-addons/base:14.2.0` 可访问
4. 检查仓库权限设置
5. 确认 GitHub Token 有推送权限

### Q: 如何更新镜像？

A: 
1. 修改 Dockerfile 或相关文件
2. 更新 `config.json` 中的版本号（如果使用版本标签）
3. 提交并推送到 GitHub
4. GitHub Actions 会自动构建新镜像
5. 创建新的 Release 以标记版本

### Q: 预构建镜像和 Dockerfile 构建可以共存吗？

A: 可以，但 Home Assistant 会优先使用 `config.json` 中的 `image` 字段。如果指定了 `image`，即使存在 Dockerfile 也不会使用。

### Q: 如何为不同架构单独构建镜像？

A: GitHub Actions 会自动构建所有架构的镜像。如果需要单独构建，可以使用本地的 `docker buildx` 命令，为每个架构单独构建和推送。

## 镜像标签策略

- `latest` - 最新版本（main 分支）
- `<version>` - 版本号（从 config.json 读取，如 1.0.0）
- `<branch>-<sha>` - 分支名和提交 SHA（用于开发分支）

## 参考资源

- [Docker Buildx 文档](https://docs.docker.com/buildx/)
- [GitHub Container Registry](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
- [Home Assistant Add-on 镜像规范](https://developers.home-assistant.io/docs/add-ons/configuration#docker-image)
