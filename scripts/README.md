# 构建和发布脚本

本目录包含用于构建和发布 Release 的脚本。

## 快速开始（推荐）

### 使用 build-release.sh 一键构建和发布

这是最便捷的方式，会自动：
- 递增版本号（patch/minor/major）
- 更新 `frpc/config.json` 中的版本
- 可选：提交更改、推送到远程、触发 workflow

```bash
# 最简单的方式：递增补丁版本，提交并推送
./scripts/build-release.sh patch --commit --push

# 递增次版本
./scripts/build-release.sh minor --commit --push

# 递增主版本
./scripts/build-release.sh major --commit --push

# 指定具体版本号
./scripts/build-release.sh 1.0.5 --commit --push

# 完整流程：递增版本、提交、推送、触发 workflow
export GITHUB_TOKEN="your_token_here"
./scripts/build-release.sh patch --commit --push --trigger
```

**功能说明：**
- `patch` - 递增补丁版本 (1.0.1 -> 1.0.2) [默认]
- `minor` - 递增次版本 (1.0.1 -> 1.1.0)
- `major` - 递增主版本 (1.0.1 -> 2.0.0)
- `--commit` - 提交更改到 git
- `--push` - 推送到远程仓库
- `--trigger` - 触发 release workflow（需要 GITHUB_TOKEN）

---

## 手动触发 Release Workflow

### 前置要求：获取 GITHUB_TOKEN

要触发 GitHub Actions workflow，需要先获取 GitHub Personal Access Token (PAT)。

#### 步骤 1: 生成 Personal Access Token

1. **访问 GitHub Token 设置页面**
   - 打开浏览器，访问：https://github.com/settings/tokens
   - 或者：GitHub 主页 → 右上角头像 → **Settings** → 左侧菜单 **Developer settings** → **Personal access tokens** → **Tokens (classic)**

2. **创建新 Token**
   - 点击 **Generate new token** 按钮
   - 选择 **Generate new token (classic)**（经典版本）

3. **配置 Token**
   - **Note（备注）**：填写一个描述性名称，如 `linknlink-remote-release`
   - **Expiration（过期时间）**：选择有效期（建议选择较长时间，如 90 天或自定义）
   - **Select scopes（选择权限）**：至少勾选以下权限之一：
     - ✅ **`repo`** - 完整仓库访问权限（推荐，包含所有仓库操作）
     - ✅ **`workflow`** - 更新 GitHub Action workflows（如果只使用 workflow 功能）

4. **生成并复制 Token**
   - 滚动到页面底部，点击 **Generate token** 按钮
   - ⚠️ **重要**：Token 只会显示一次，请立即复制保存！
   - Token 格式类似：`ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

#### 步骤 2: 设置环境变量

有几种方式设置 `GITHUB_TOKEN` 环境变量：

**方法 1: 临时设置（当前终端会话有效）**
```bash
export GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

**方法 2: 永久设置（推荐）**
```bash
# 编辑 ~/.bashrc 或 ~/.zshrc
echo 'export GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"' >> ~/.bashrc

# 重新加载配置
source ~/.bashrc
```

**方法 3: 使用专用脚本文件（推荐用于多账号）**
```bash
# 在 ~/1_codes/env/ 目录下创建脚本文件
# 例如：~/1_codes/env/github_token_acmen0102.sh
export GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

# 使用前加载
source ~/1_codes/env/github_token_linknlink.sh
```

**方法 4: 在命令中直接指定（一次性使用）**
```bash
GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" ./scripts/build-release.sh patch --commit --push --trigger
```

#### 步骤 3: 验证 Token

```bash
# 检查环境变量是否设置成功
echo $GITHUB_TOKEN

# 测试 Token 是否有效（会显示你的 GitHub 用户名）
curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user
```

#### 安全提示

- ⚠️ **不要将 Token 提交到 Git 仓库**
- ⚠️ **不要在不安全的环境中分享 Token**
- ⚠️ **定期更新 Token**（如果设置了过期时间）
- ✅ **使用最小权限原则**（只授予必要的权限）
- ✅ **Token 泄露后立即撤销**：访问 https://github.com/settings/tokens 删除旧 Token

## 使用方法

### 方法 1: 使用 Bash 脚本

```bash
# 设置 token
export GITHUB_TOKEN="your_token_here"

# 触发 release workflow
./scripts/trigger-release.sh 1.0.1
```

### 方法 2: 使用 Python 脚本

```bash
# 设置 token
export GITHUB_TOKEN="your_token_here"

# 触发 release workflow
python3 scripts/trigger-release.py 1.0.1
```

**注意**: Python 脚本需要 `requests` 库，如果没有安装：
```bash
pip install requests
```

### 方法 3: 一行命令（使用 curl）

```bash
export GITHUB_TOKEN="your_token_here"
curl -X POST \
  -H "Accept: application/vnd.github.v3+json" \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/linknlink/linknlink-remote/dispatches \
  -d '{"event_type":"release","client_payload":{"version":"1.0.1"}}'
```

## 验证

触发成功后，访问以下链接查看 workflow 运行状态：
- https://github.com/linknlink/linknlink-remote/actions

## 其他触发方式

除了使用脚本，还可以通过以下方式触发：

1. **GitHub Actions 页面手动触发** (`workflow_dispatch`)
   - 进入 Actions 页面
   - 选择 Release workflow
   - 点击 "Run workflow"
   - 输入版本号

2. **创建 GitHub Release** (`release`)
   - 进入 Releases 页面
   - 创建新 Release
   - 输入 Tag（例如：`v1.0.1`）
   - 发布

更多详细信息请查看：[docs/trigger-release.md](../docs/trigger-release.md)

