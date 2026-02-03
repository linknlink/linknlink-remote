#!/bin/bash

# 构建并发布 Release 的脚本
# 自动递增版本号，更新 VERSION 文件，并触发构建流程
# 使用方法: ./scripts/build-release.sh [版本号类型: patch|minor|major] [--commit] [--push]
# 例如: ./scripts/build-release.sh patch --commit --push

set -e

# 配置
VERSION_FILE="VERSION"
REPO="linknlink/linknlink-remote"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 显示帮助信息
show_help() {
    echo "使用方法: $0 [版本类型] [选项]"
    echo ""
    echo "版本类型:"
    echo "  patch  - 递增补丁版本 (1.0.1 -> 1.0.2) [默认]"
    echo "  minor  - 递增次版本 (1.0.1 -> 1.1.0)"
    echo "  major  - 递增主版本 (1.0.1 -> 2.0.0)"
    echo "  或直接指定版本号，如: 1.0.2"
    echo ""
    echo "选项:"
    echo "  --commit    - 提交更改到 git"
    echo "  --push      - 推送到远程仓库"
    echo "  --trigger   - 触发 release workflow (需要 GITHUB_TOKEN)"
    echo "  --help      - 显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 patch                    # 递增补丁版本，仅更新本地文件"
    echo "  $0 patch --commit          # 递增补丁版本并提交"
    echo "  $0 patch --commit --push   # 递增补丁版本，提交并推送"
    echo "  $0 1.0.5 --commit --push   # 使用指定版本号"
}

# 解析参数
VERSION_TYPE="patch"
COMMIT=false
PUSH=false
TRIGGER=false

while [[ $# -gt 0 ]]; do
    case $1 in
        patch|minor|major)
            VERSION_TYPE="$1"
            shift
            ;;
        --commit)
            COMMIT=true
            shift
            ;;
        --push)
            PUSH=true
            shift
            ;;
        --trigger)
            TRIGGER=true
            shift
            ;;
        --help|-h)
            show_help
            exit 0
            ;;
        *)
            # 检查是否是版本号格式
            if [[ "$1" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
                NEW_VERSION="$1"
                VERSION_TYPE="custom"
            else
                echo -e "${RED}错误: 未知参数 '$1'${NC}"
                show_help
                exit 1
            fi
            shift
            ;;
    esac
done

# 检查文件是否存在
if [ ! -f "$VERSION_FILE" ]; then
    echo "0.0.0" > "$VERSION_FILE"
    echo -e "${YELLOW}警告: 找不到配置文件 $VERSION_FILE，已创建初始版本 0.0.0${NC}"
fi

# 读取当前版本
CURRENT_VERSION=$(cat "$VERSION_FILE" | tr -d '[:space:]')
echo -e "${GREEN}当前版本: ${CURRENT_VERSION}${NC}"

# 计算新版本
if [ "$VERSION_TYPE" = "custom" ]; then
    NEW_VERSION="$NEW_VERSION"
elif [ "$VERSION_TYPE" = "patch" ]; then
    # 递增补丁版本: 1.0.1 -> 1.0.2
    IFS='.' read -ra VERSION_PARTS <<< "$CURRENT_VERSION"
    MAJOR=${VERSION_PARTS[0]}
    MINOR=${VERSION_PARTS[1]}
    PATCH=${VERSION_PARTS[2]}
    NEW_VERSION="${MAJOR}.${MINOR}.$((PATCH + 1))"
elif [ "$VERSION_TYPE" = "minor" ]; then
    # 递增次版本: 1.0.1 -> 1.1.0
    IFS='.' read -ra VERSION_PARTS <<< "$CURRENT_VERSION"
    MAJOR=${VERSION_PARTS[0]}
    MINOR=${VERSION_PARTS[1]}
    NEW_VERSION="${MAJOR}.$((MINOR + 1)).0"
elif [ "$VERSION_TYPE" = "major" ]; then
    # 递增主版本: 1.0.1 -> 2.0.0
    IFS='.' read -ra VERSION_PARTS <<< "$CURRENT_VERSION"
    MAJOR=${VERSION_PARTS[0]}
    NEW_VERSION="$((MAJOR + 1)).0.0"
else
    echo -e "${RED}错误: 未知的版本类型 '$VERSION_TYPE'${NC}"
    exit 1
fi

# 检查版本是否有效
if [ "$NEW_VERSION" = "$CURRENT_VERSION" ]; then
    echo -e "${YELLOW}警告: 新版本与当前版本相同${NC}"
    exit 1
fi

# 检查版本是否已经存在 tag
if git tag -l | grep -q "^v${NEW_VERSION}$"; then
    echo -e "${RED}错误: 版本 tag v${NEW_VERSION} 已经存在${NC}"
    echo "请使用不同的版本号"
    exit 1
fi

echo -e "${GREEN}新版本: ${NEW_VERSION}${NC}"
echo ""

# 确认
read -p "确认更新版本号并继续? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "已取消"
    exit 0
fi

# 更新 VERSION 文件
echo -e "${GREEN}更新 $VERSION_FILE...${NC}"
echo "$NEW_VERSION" > "$VERSION_FILE"

# 验证更新
UPDATED_VERSION=$(cat "$VERSION_FILE" | tr -d '[:space:]')
if [ "$UPDATED_VERSION" != "$NEW_VERSION" ]; then
    echo -e "${RED}错误: 版本更新失败${NC}"
    exit 1
fi

echo -e "${GREEN}✓ 版本已更新为 ${NEW_VERSION}${NC}"

# 提交更改
if [ "$COMMIT" = true ]; then
    echo ""
    echo -e "${GREEN}提交更改...${NC}"
    
    # 检查是否有未提交的更改
    if ! git diff --quiet "$VERSION_FILE"; then
        git add "$VERSION_FILE"
        git commit -m "chore: 更新版本到 v${NEW_VERSION}"
        echo -e "${GREEN}✓ 已提交更改${NC}"
    else
        echo -e "${YELLOW}没有需要提交的更改${NC}"
    fi

    # 创建 git tag
    echo -e "${GREEN}创建 tag v${NEW_VERSION}...${NC}"
    git tag "v${NEW_VERSION}"
    echo -e "${GREEN}✓ 已创建 tag${NC}"
fi

# 推送到远程
if [ "$PUSH" = true ]; then
    echo ""
    echo -e "${GREEN}推送到远程仓库...${NC}"
    
    if [ "$COMMIT" = false ]; then
        echo -e "${YELLOW}警告: 未提交更改，跳过推送${NC}"
    else
        # 获取当前分支名称
        CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
        
        # 尝试推送代码
        if ! git push 2>/tmp/git_push_error; then
            if grep -q "has no upstream branch" /tmp/git_push_error; then
                echo -e "${YELLOW}当前分支 $CURRENT_BRANCH 没有上游分支，正在设置...${NC}"
                git push --set-upstream origin "$CURRENT_BRANCH"
            else
                cat /tmp/git_push_error
                echo -e "${RED}✗ 推送失败${NC}"
                exit 1
            fi
        fi
        
        # 推送 tags (通过 tag 触发 CI 构建)
        echo -e "${GREEN}推送 tags...${NC}"
        if git push origin "v${NEW_VERSION}"; then
             echo -e "${GREEN}✓ 已推送 tags${NC}"
        else
             echo -e "${RED}✗ tags 推送失败${NC}"
        fi

        echo -e "${GREEN}✓ 已推送到远程仓库${NC}"
    fi
fi

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# 获取 GitHub Token
get_github_token() {
    local token="${GITHUB_TOKEN}"
    local token_file=$(find "$PROJECT_ROOT" -maxdepth 1 -name "*.token" -type f 2>/dev/null | head -n1)
    if [ -n "$token_file" ] && [ -f "$token_file" ]; then
        local file_token=$(cat "$token_file" | tr -d '[:space:]')
        if [ -n "$file_token" ]; then
            token="$file_token"
            echo -e "${YELLOW}从文件读取 token: $(basename "$token_file")${NC}" >&2
        fi
    fi
    echo "$token"
}

# 触发 release workflow (如果设置了 TRIGGER)
# 注意: 现在 CI 是通过 tag 触发的，所以这步可能不是必需的，除非有特定的 workflow_dispatch
if [ "$TRIGGER" = true ]; then
    echo ""
    echo -e "${GREEN}触发 release workflow...${NC}"
    
    TOKEN=$(get_github_token)
    if [ -z "$TOKEN" ]; then
        echo -e "${RED}错误: GITHUB_TOKEN 未设置${NC}"
        # 忽略错误，因为我们已经通过 tag 触发了构建
        echo -e "${YELLOW}跳过手动触发 (CI 已通过 tag 推送触发)${NC}"
    else
        response=$(curl -s -w "\n%{http_code}" -X POST \
          -H "Accept: application/vnd.github.v3+json" \
          -H "Authorization: token $TOKEN" \
          "https://api.github.com/repos/$REPO/dispatches" \
          -d "{
            \"event_type\": \"release\",
            \"client_payload\": {
              \"version\": \"$NEW_VERSION\"
            }
          }")
        
        http_code=$(echo "$response" | tail -n1)
        if [ "$http_code" = "204" ]; then
            echo -e "${GREEN}✓ Workflow 触发成功!${NC}"
        else
            echo -e "${RED}✗ 触发失败 (HTTP $http_code)${NC}"
            # 不退出，因为 tag 可能已经触发了构建
        fi
    fi
fi

echo ""
echo -e "${GREEN}完成!${NC}"
echo ""
echo "下一步:"
echo "  查看构建状态: https://github.com/$REPO/actions"
echo "  查看已发布的镜像: https://github.com/orgs/linknlink/packages/container/package/linknlink-remote"
echo ""


