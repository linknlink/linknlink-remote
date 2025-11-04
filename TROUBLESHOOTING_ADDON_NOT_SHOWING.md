# 加载项不显示在商店中的排查指南

## 问题

仓库已成功添加，但在加载项商店中看不到加载项。

## 可能的原因和解决方案

### 1. 等待同步（最常见）

Home Assistant 需要时间同步仓库内容：
- **等待 2-5 分钟**让 Home Assistant 自动同步
- 刷新浏览器页面
- 进入 **Supervisor** → **加载项商店**，点击刷新按钮

### 2. 重启 Supervisor

1. 进入 **Supervisor** → **系统**
2. 点击 **重新启动 Supervisor**
3. 等待重启完成后，再次查看加载项商店

### 3. 检查仓库同步状态

1. 进入 **Supervisor** → **系统** → **日志**
2. 查找与仓库相关的错误信息
3. 查找类似 `cdbc1f01` 或 `linknlink-remote` 的日志条目

### 4. 检查镜像是否可访问

由于 `config.json` 中使用了预构建镜像：
```json
"image": "ghcr.io/acmen0102/linknlink-remote-frpc:{arch}"
```

如果镜像不可访问（403 错误或包未公开），Home Assistant 可能会隐藏加载项。

**解决方法：**
- 确保 GitHub Container Registry 包已设置为**公开**
- 参考 `GITHUB_PACKAGE_PUBLIC.md` 设置包为公开
- 测试镜像是否可拉取：
  ```bash
  docker pull ghcr.io/acmen0102/linknlink-remote-frpc:amd64
  ```

### 5. 检查配置文件格式

确保 `frpc/config.json` 格式正确：
- JSON 语法正确
- 必需的字段存在：`name`, `slug`, `version`, `description`
- `slug` 字段值必须是小写字母、数字和连字符

### 6. 检查架构支持

确认您的 Home Assistant 系统架构在支持列表中：
- 查看支持的架构：`aarch64`, `amd64`, `armhf`, `armv7`, `i386`
- 在 Home Assistant 中查看系统信息：**Supervisor** → **系统** → **硬件**

### 7. 手动刷新仓库

1. 进入 **Supervisor** → **加载项商店**
2. 点击右上角的 **⋮** 菜单（三个点）
3. 选择 **刷新** 或 **重新加载**

### 8. 检查浏览器缓存

- 清除浏览器缓存
- 使用无痕/隐私模式访问
- 尝试不同的浏览器

### 9. 检查仓库 URL 大小写

当前 URL：`https://github.com/acmen0102/linknlink-remote`

如果 GitHub 仓库名是大写开头（`Acmen0102`），尝试使用：
- `https://github.com/Acmen0102/linknlink-remote`

### 10. 临时切换到 Dockerfile 构建方式

如果镜像问题导致加载项不显示，可以临时移除 `image` 字段，使用 Dockerfile 构建：

```json
{
  // ... 其他配置 ...
  // 注释掉或删除这一行：
  // "image": "ghcr.io/acmen0102/linknlink-remote-frpc:{arch}",
}
```

**注意：** 这会回到之前的构建方式，可能遇到网络超时问题。

## 验证步骤

按顺序执行以下步骤：

1. ✅ 检查 `repository.json` 格式正确
2. ✅ 检查 `frpc/config.json` 格式正确
3. ✅ 确认仓库已添加（在"管理加载项存储库"中可见）
4. ⏱️ 等待 2-5 分钟
5. 🔄 刷新浏览器页面
6. 🔄 重启 Supervisor
7. 🔍 检查 Supervisor 日志
8. 🌐 确认镜像包已公开且可访问

## 如果仍然不显示

1. **查看详细日志**：
   - **Supervisor** → **系统** → **日志**
   - 搜索错误信息

2. **检查 GitHub 仓库**：
   - 确认 `frpc/config.json` 存在于仓库中
   - 确认文件格式正确

3. **测试镜像访问**：
   ```bash
   # 在 Home Assistant 服务器上执行
   docker pull ghcr.io/acmen0102/linknlink-remote-frpc:amd64
   ```

4. **联系支持**：
   - Home Assistant 社区论坛
   - 创建 GitHub Issue

## 常见错误信息

### "404 Not Found"
- 镜像标签不存在
- 包未公开
- 架构不匹配

### "403 Forbidden"
- 包是私有的，需要设置为公开

### "manifest unknown"
- 镜像标签不存在
- 需要重新构建镜像
