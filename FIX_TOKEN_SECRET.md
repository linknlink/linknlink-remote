# 解决 GitHub Token 泄露问题

## 问题说明

GitHub 推送保护检测到代码中硬编码了 Personal Access Token，阻止了推送。

## 解决方案

### 方案 1：使用环境变量（推荐）

**已在 `delete_tags.sh` 中修复：**

```bash
# ❌ 错误：硬编码 token
export GITHUB_TOKEN="ghp_xxxxx"

# ✅ 正确：使用环境变量
export GITHUB_TOKEN=your_token_here
# 或
TOKEN="${GITHUB_TOKEN}"
```

### 方案 2：使用 GitHub CLI 认证

```bash
# 安装 GitHub CLI
sudo apt install gh

# 登录（会安全地保存 token）
gh auth login

# 使用 GitHub CLI 操作（不需要手动设置 token）
gh api user/packages/container/linknlink-remote-frpc/versions
```

### 方案 3：使用 Secret Manager

对于 CI/CD 环境，使用 GitHub Secrets：
- 在仓库设置中添加 `GITHUB_TOKEN` secret
- 在工作流中使用 `${{ secrets.GITHUB_TOKEN }}`

## 如果 Token 已泄露

1. **立即撤销旧的 Token**：
   - 访问：`https://github.com/settings/tokens`
   - 找到泄露的 token，点击 "Revoke" 撤销

2. **创建新的 Token**：
   - 创建新 token
   - 只授予最小必要权限

3. **从 Git 历史中移除**：
   ```bash
   # 如果还未推送到远程，使用 rebase
   git rebase -i HEAD~n  # n 是要修改的提交数量
   
   # 如果已推送，需要强制推送（谨慎！）
   git push --force
   ```

## 使用脚本时的正确方法

```bash
# 设置环境变量（不要在脚本中硬编码！）
export GITHUB_TOKEN=your_new_token_here

# 运行脚本
./delete_tags.sh delete-untagged y

# 或者一次性设置
GITHUB_TOKEN=your_new_token_here ./delete_tags.sh delete-untagged y
```

## 安全建议

1. ✅ **永远不要**在代码中硬编码 token
2. ✅ 使用环境变量或配置文件（添加到 `.gitignore`）
3. ✅ 定期轮换 token
4. ✅ 只授予最小必要权限
5. ✅ 使用 `.gitignore` 排除包含敏感信息的文件
6. ❌ **不要**将 token 提交到 Git
7. ❌ **不要**在公共仓库中分享 token

## 当前状态

- ✅ `delete_tags.sh` 已修复，使用环境变量
- ✅ 已添加 `.gitignore` 文件
- ✅ 历史记录中的 token 需要从远程仓库历史中移除（如果已推送）

如果 token 已泄露，请立即撤销并创建新的 token！
