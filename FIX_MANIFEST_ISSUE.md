# 修复 Manifest List 问题

## 问题说明

从 `docker manifest inspect` 的输出可以看到：
- `:amd64` 标签是一个 **manifest list**（索引），而不是单个架构镜像
- 包含了一个 `unknown` 平台的清单，这是异常的
- Home Assistant 需要的是单个架构镜像，不是 manifest list

## 解决方案

### 方案 1：删除并重新构建（推荐）

1. **手动删除错误的标签**：
   
   在 GitHub Packages 页面：
   - 访问：`https://github.com/Acmen0102/linknlink-remote/pkgs/container/linknlink-remote-frpc`
   - 找到 `amd64`、`aarch64` 等架构标签
   - 删除这些标签（如果有删除选项）

2. **重新运行工作流**：
   - 访问 GitHub Actions
   - 手动触发工作流
   - 确保这次构建为每个架构创建的是单个镜像，不是 manifest list

### 方案 2：使用版本标签（临时方案）

如果 `:amd64` 有问题，但 `:1.0.0-amd64` 是正确的，可以修改 `config.json`：

```json
{
  "image": "ghcr.io/acmen0102/linknlink-remote-frpc:{version}-{arch}"
}
```

但这需要 Home Assistant 支持 `{version}` 占位符。

### 方案 3：检查构建配置

确保工作流中为单个架构构建时，不使用 manifest list。当前配置应该是正确的，但可能需要：
- 清除旧的 manifest
- 重新构建

## 验证修复

修复后，执行：

```bash
docker manifest inspect ghcr.io/acmen0102/linknlink-remote-frpc:amd64
```

应该看到：
- `mediaType`: `application/vnd.oci.image.manifest.v1+json`（单个清单）
- 而不是 `application/vnd.oci.image.index.v1+json`（索引）
- `platform.architecture`: `amd64`
- `platform.os`: `linux`
- 不应该有 `manifests` 数组

## 快速修复步骤

1. 删除所有架构标签（`:amd64`, `:aarch64`, `:armhf`, `:armv7`, `:i386`）
2. 在 GitHub Actions 中手动触发工作流重新构建
3. 验证新的镜像是否为单个架构镜像
4. 如果正确，重新添加 `image` 字段到 `config.json`
