# 删除 GitHub Container Registry 镜像标签

## 方法 1：通过 GitHub 网页界面（推荐）

### 步骤：

1. **访问包页面**：
   ```
   https://github.com/Acmen0102/linknlink-remote/pkgs/container/linknlink-remote-frpc
   ```

2. **查看所有版本/标签**：
   - 在页面右侧或下方会显示所有标签
   - 找到需要删除的标签：`amd64`, `aarch64`, `armhf`, `armv7`, `i386`

3. **删除标签**：
   - 点击标签名称或右侧的菜单（三个点 `...`）
   - 选择 "Delete" 或 "删除版本"
   - 确认删除

**注意**：如果网页界面没有删除选项，可能需要通过 API 删除。

## 方法 2：通过 GitHub API（命令行）

### 步骤 1：获取 Personal Access Token

1. 访问：`https://github.com/settings/tokens`
2. 创建新的 token（Classic）或使用 Fine-grained token
3. 需要的权限：
   - `write:packages`（写入包）
   - `delete:packages`（删除包）
   - `read:packages`（读取包）

### 步骤 2：获取包的 SHA256 摘要

对于每个标签，需要获取其 SHA256 摘要：

```bash
# 设置变量
GITHUB_USER=Acmen0102
PACKAGE_NAME=linknlink-remote-frpc
TAG=amd64
TOKEN=your_github_token_here

# 获取标签的 SHA256
curl -s \
  -H "Authorization: token $TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  "https://api.github.com/user/packages/container/${PACKAGE_NAME}/versions" | \
  jq -r ".[] | select(.metadata.container.tags[] | contains(\"$TAG\")) | .id"
```

### 步骤 3：删除标签

#### 选项 A：删除特定版本的标签（推荐）

```bash
# 删除指定标签的版本
curl -X DELETE \
  -H "Authorization: token $TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  "https://api.github.com/user/packages/container/${PACKAGE_NAME}/versions/${VERSION_ID}"
```

#### 选项 B：使用 GitHub CLI（如果已安装）

```bash
# 安装 GitHub CLI（如果还没有）
# Ubuntu/Debian:
# sudo apt install gh

# 登录
gh auth login

# 列出所有版本
gh api user/packages/container/linknlink-remote-frpc/versions | jq '.[] | {id, tags: .metadata.container.tags}'

# 删除特定版本（需要先获取版本 ID）
gh api -X DELETE user/packages/container/linknlink-remote-frpc/versions/<VERSION_ID>
```

## 方法 3：使用脚本批量删除

创建一个脚本来自动删除所有架构标签：

```bash
#!/bin/bash

# 配置
GITHUB_USER=Acmen0102
PACKAGE_NAME=linknlink-remote-frpc
TAGS=("amd64" "aarch64" "armhf" "armv7" "i386")

# 读取 token（建议从环境变量或文件读取，不要硬编码）
TOKEN="${GITHUB_TOKEN}"

if [ -z "$TOKEN" ]; then
    echo "错误: 请设置 GITHUB_TOKEN 环境变量"
    echo "export GITHUB_TOKEN=your_token_here"
    exit 1
fi

echo "获取所有版本..."
VERSIONS=$(curl -s \
  -H "Authorization: token $TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  "https://api.github.com/user/packages/container/${PACKAGE_NAME}/versions")

# 删除每个标签对应的版本
for TAG in "${TAGS[@]}"; do
    echo "查找标签: $TAG"
    VERSION_IDS=$(echo "$VERSIONS" | jq -r ".[] | select(.metadata.container.tags[]? | contains(\"$TAG\")) | .id")
    
    for VERSION_ID in $VERSION_IDS; do
        if [ ! -z "$VERSION_ID" ] && [ "$VERSION_ID" != "null" ]; then
            echo "  删除版本 ID: $VERSION_ID (标签: $TAG)"
            
            # 先获取该版本的所有标签
            TAGS_IN_VERSION=$(echo "$VERSIONS" | jq -r ".[] | select(.id == $VERSION_ID) | .metadata.container.tags[]")
            echo "    包含的标签: $TAGS_IN_VERSION"
            
            # 删除版本
            RESPONSE=$(curl -s -w "\n%{http_code}" -X DELETE \
              -H "Authorization: token $TOKEN" \
              -H "Accept: application/vnd.github.v3+json" \
              "https://api.github.com/user/packages/container/${PACKAGE_NAME}/versions/${VERSION_ID}")
            
            HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
            if [ "$HTTP_CODE" = "204" ]; then
                echo "    ✓ 成功删除"
            else
                echo "    ✗ 删除失败 (HTTP $HTTP_CODE)"
                echo "    响应: $(echo "$RESPONSE" | head -n-1)"
            fi
        fi
    done
done

echo "完成！"
```

保存为 `delete_tags.sh`，然后执行：

```bash
chmod +x delete_tags.sh
export GITHUB_TOKEN=your_token_here
./delete_tags.sh
```

## 方法 4：使用 Docker 命令（需要 Docker 登录）

```bash
# 登录到 GitHub Container Registry
echo $GITHUB_TOKEN | docker login ghcr.io -u Acmen0102 --password-stdin

# 注意：Docker 命令不能直接删除标签，但可以删除整个镜像
# 删除操作需要通过 API 或网页界面
```

## 注意事项

1. **删除是不可逆的**：删除后需要重新构建
2. **可能影响其他标签**：如果一个版本包含多个标签，删除版本会删除所有标签
3. **权限要求**：需要包的写入/删除权限
4. **API 限制**：GitHub API 有速率限制，批量操作时注意

## 验证删除

删除后，验证标签是否已删除：

```bash
# 方法 1：通过 API 检查
curl -s \
  -H "Authorization: token $TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  "https://api.github.com/user/packages/container/${PACKAGE_NAME}/versions" | \
  jq '.[] | .metadata.container.tags'

# 方法 2：通过 Docker manifest 检查（如果镜像已公开）
docker manifest inspect ghcr.io/acmen0102/linknlink-remote-frpc:amd64
# 如果标签已删除，会返回 404 错误
```

## 推荐流程

1. **先通过网页界面尝试删除**（最简单）
2. **如果网页界面没有删除选项，使用 GitHub CLI**（最方便）
3. **如果需要批量操作，使用脚本**（最高效）
4. **删除后重新运行 GitHub Actions 工作流**重新构建
