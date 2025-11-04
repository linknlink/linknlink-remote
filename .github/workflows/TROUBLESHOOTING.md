# GitHub Actions 构建故障排除

## 常见错误和解决方案

### 错误 1: "Error: The operation was canceled"

**原因：**
- 登录 GitHub Container Registry 时被取消
- 网络超时
- 权限不足

**解决方案：**

1. **检查仓库权限设置**
   - 进入 GitHub 仓库设置：`Settings` → `Actions` → `General`
   - 确保 "Workflow permissions" 设置为 "Read and write permissions"
   - 勾选 "Allow GitHub Actions to create and approve pull requests"

2. **检查 GitHub Token 权限**
   - 工作流使用 `GITHUB_TOKEN`，应该自动有 `packages: write` 权限
   - 如果仍有问题，可以在仓库设置中检查 Actions 权限

3. **重新触发工作流**
   - 进入 `Actions` 标签页
   - 找到失败的工作流
   - 点击 "Re-run jobs" 重新运行

### 错误 2: 工作流没有被触发

**原因：**
- 路径过滤限制
- 提交的文件不在触发路径中

**解决方案：**

1. **手动触发工作流**
   - 进入 `Actions` 标签页
   - 选择 "Build and Push Docker Images"
   - 点击 "Run workflow" 手动触发

2. **检查路径过滤**
   - 工作流在以下文件变更时触发：
     - `frpc/Dockerfile`
     - `frpc/run.sh`
     - `frpc/config.json`
     - `.github/workflows/build-and-push.yml`

### 错误 3: 构建超时

**原因：**
- 构建时间过长（特别是多架构构建）
- 网络速度慢

**解决方案：**

1. **增加超时时间**
   - 工作流已设置 60 分钟超时
   - 如果还不够，可以在工作流文件中调整 `timeout-minutes`

2. **分步构建**
   - 可以先只构建需要的架构（如 amd64）
   - 修改 matrix 只包含需要的架构

### 错误 4: 权限拒绝 (403 Forbidden)

**原因：**
- GitHub Token 没有推送权限
- 容器注册表访问受限

**解决方案：**

1. **检查包权限**
   - 进入：`Settings` → `Actions` → `General`
   - 确保 "Workflow permissions" 有写入权限

2. **检查容器包可见性**
   - 容器包默认为私有
   - 如需公开：`Settings` → `Packages` → 选择包 → `Package settings` → 更改可见性

### 错误 5: 基础镜像拉取失败

**原因：**
- 无法访问 `ghcr.io/hassio-addons/base:14.2.0`
- 网络连接问题

**解决方案：**

1. **使用镜像加速器**
   - 在 GitHub Actions 中配置代理（如果需要）
   - 或者使用 Docker Hub 的镜像

2. **检查基础镜像是否存在**
   ```bash
   docker pull ghcr.io/hassio-addons/base:14.2.0
   ```

## 调试技巧

### 1. 查看详细日志
- 进入失败的 job
- 展开失败的步骤
- 查看完整的错误日志

### 2. 本地测试构建
```bash
# 测试单个架构
docker buildx build --platform linux/amd64 -t test:amd64 ./frpc

# 测试登录
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin
```

### 3. 检查工作流文件语法
- 使用在线 YAML 验证器
- 检查缩进和格式

### 4. 逐步测试
- 先只构建一个架构（如 amd64）
- 确认成功后再构建其他架构

## 联系支持

如果问题仍然存在：
1. 检查 [GitHub Actions 状态页面](https://www.githubstatus.com/)
2. 查看 [GitHub Actions 文档](https://docs.github.com/en/actions)
3. 在仓库中创建 Issue 描述问题
