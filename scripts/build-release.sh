#!/bin/bash

# 构建并发布 Release 的脚本
# 自动递增版本号，更新 config.json，并触发构建流程
# 使用方法: ./scripts/build-release.sh [版本号类型: patch|minor|major] [--commit] [--push]
# 例如: ./scripts/build-release.sh patch --commit --push

set -e

# 配置
CONFIG_FILE="frpc/config.json"
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
if [ ! -f "$CONFIG_FILE" ]; then
    echo -e "${RED}错误: 找不到配置文件 $CONFIG_FILE${NC}"
    exit 1
fi

# 检查是否有 jq 命令
if ! command -v jq &> /dev/null; then
    echo -e "${RED}错误: 需要安装 jq 命令${NC}"
    echo "安装方法:"
    echo "  Ubuntu/Debian: sudo apt-get install jq"
    echo "  macOS: brew install jq"
    exit 1
fi

# 读取当前版本
CURRENT_VERSION=$(jq -r '.version' "$CONFIG_FILE")
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

# 检查版本是否已经存在
if git tag -l | grep -q "^v${NEW_VERSION}$"; then
    echo -e "${RED}错误: 版本 v${NEW_VERSION} 已经存在${NC}"
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

# 更新 config.json
echo -e "${GREEN}更新 $CONFIG_FILE...${NC}"
jq ".version = \"$NEW_VERSION\"" "$CONFIG_FILE" > "$CONFIG_FILE.tmp"
mv "$CONFIG_FILE.tmp" "$CONFIG_FILE"

# 验证更新
UPDATED_VERSION=$(jq -r '.version' "$CONFIG_FILE")
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
    if ! git diff --quiet "$CONFIG_FILE"; then
        git add "$CONFIG_FILE"
        git commit -m "chore: 更新版本到 v${NEW_VERSION}"
        echo -e "${GREEN}✓ 已提交更改${NC}"
    else
        echo -e "${YELLOW}没有需要提交的更改${NC}"
    fi
fi

# 推送到远程
if [ "$PUSH" = true ]; then
    echo ""
    echo -e "${GREEN}推送到远程仓库...${NC}"
    
    if [ "$COMMIT" = false ]; then
        echo -e "${YELLOW}警告: 未提交更改，跳过推送${NC}"
    else
        git push
        echo -e "${GREEN}✓ 已推送到远程仓库${NC}"
    fi
fi

# 触发 release workflow
if [ "$TRIGGER" = true ]; then
    echo ""
    echo -e "${GREEN}触发 release workflow...${NC}"
    
    TOKEN="${GITHUB_TOKEN}"
    if [ -z "$TOKEN" ]; then
        echo -e "${RED}错误: GITHUB_TOKEN 环境变量未设置${NC}"
        echo "请设置 GITHUB_TOKEN 环境变量:"
        echo "  export GITHUB_TOKEN=\"your_token_here\""
        exit 1
    fi
    
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
        echo "请访问以下链接查看 workflow 运行状态:"
        echo "  https://github.com/$REPO/actions"
    else
        echo -e "${RED}✗ 触发失败 (HTTP $http_code)${NC}"
        exit 1
    fi
fi

echo ""
echo -e "${GREEN}完成!${NC}"
echo ""
echo "下一步:"
if [ "$PUSH" = false ]; then
    echo "  1. 检查更改: git diff $CONFIG_FILE"
    echo "  2. 提交更改: git add $CONFIG_FILE && git commit -m 'chore: 更新版本到 v${NEW_VERSION}'"
    echo "  3. 推送到远程: git push"
fi
echo "  4. 查看构建状态: https://github.com/$REPO/actions"
echo "  5. 查看已发布的镜像: https://github.com/$REPO/pkgs/container/linknlink-remote-frpc"

