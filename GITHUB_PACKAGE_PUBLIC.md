# 将 GitHub Container Registry 包设置为公开

## 问题

如果遇到 403 Forbidden 错误，通常是因为 GitHub Container Registry 的包默认是私有的，需要将其设置为公开。

## 解决步骤

### 方法 1：通过 GitHub 网页界面

1. **访问包页面**
   - 访问：`https://github.com/Acmen0102/linknlink-remote/pkgs/container/linknlink-remote-frpc`
   - 或者进入仓库 → 点击右侧的 **Packages** → 选择 `linknlink-remote-frpc`

2. **打开包设置**
   - 在包页面上，点击 **Package settings**（包设置）
   - 或者点击右上角的 **⚙️** 图标

3. **更改可见性**
   - 向下滚动找到 **Danger Zone**（危险区域）
   - 点击 **Change visibility**（更改可见性）
   - 选择 **Public**（公开）
   - 确认更改

### 方法 2：通过 GitHub API（命令行）

```bash
# 需要 GitHub Personal Access Token，权限需要包含 packages:write
# 将 YOUR_TOKEN 替换为您的 token
# 将 OWNER 替换为用户名（Acmen0102）
# 将 PACKAGE_NAME 替换为包名（linknlink-remote-frpc）

curl -X POST \
  -H "Authorization: token YOUR_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/user/packages/container/linknlink-remote-frpc/visibility \
  -d '{"visibility":"public"}'
```

## 验证

设置完成后，可以尝试直接访问镜像：

```bash
# 测试镜像是否可公开访问
docker pull ghcr.io/acmen0102/linknlink-remote-frpc:amd64
```

或者在浏览器中访问：
- `https://github.com/Acmen0102/linknlink-remote/pkgs/container/linknlink-remote-frpc`

如果页面显示 "Public" 标签，说明已成功设置为公开。

## 注意事项

1. **首次构建后**：包需要至少有一个镜像后才能更改可见性
2. **权限要求**：需要仓库的管理员权限
3. **包名称**：包名称必须与工作流中的 `IMAGE_NAME` 匹配

## 如果仍然无法访问

1. 检查镜像标签是否存在：
   ```bash
   docker manifest inspect ghcr.io/acmen0102/linknlink-remote-frpc:amd64
   ```

2. 检查包的访问权限设置

3. 等待几分钟让更改生效

4. 在 Home Assistant 中刷新仓库或重启 Supervisor
