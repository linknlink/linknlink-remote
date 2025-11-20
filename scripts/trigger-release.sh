#!/bin/bash

# 触发 Release Workflow 的脚本
# 使用方法: ./scripts/trigger-release.sh [版本号]
# 例如: ./scripts/trigger-release.sh 1.0.1

set -e

# 配置
REPO="linknlink/linknlink-remote"
VERSION="${1}"

# 获取脚本所在目录和项目根目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# 获取 GitHub Token（先从环境变量获取，如果本地有 *.token 文件，则读取文件中 token 进行覆盖）
get_github_token() {
    local token="${GITHUB_TOKEN}"
    
    # 查找项目根目录下的 *.token 文件
    local token_file=$(find "$PROJECT_ROOT" -maxdepth 1 -name "*.token" -type f 2>/dev/null | head -n1)
    
    # 如果找到 token 文件，读取文件中的 token 覆盖环境变量
    if [ -n "$token_file" ] && [ -f "$token_file" ]; then
        local file_token=$(cat "$token_file" | tr -d '[:space:]')
        if [ -n "$file_token" ]; then
            token="$file_token"
            echo "从文件读取 token: $(basename "$token_file")" >&2
        fi
    fi
    
    echo "$token"
}

# 检查版本参数
if [ -z "$VERSION" ]; then
    echo "错误: 请提供版本号"
    echo "使用方法: $0 <版本号>"
    echo "例如: $0 1.0.1"
    exit 1
fi

# 获取 token
TOKEN=$(get_github_token)

# 检查 token
if [ -z "$TOKEN" ]; then
    echo "错误: GITHUB_TOKEN 未设置"
    echo ""
    echo "请通过以下方式之一设置:"
    echo "  1. 环境变量: export GITHUB_TOKEN=\"your_token_here\""
    echo "  2. 创建 *.token 文件: 在项目根目录创建 *.token 文件，内容为 token"
    echo "  3. 命令行指定: GITHUB_TOKEN=\"your_token\" $0 $VERSION"
    exit 1
fi

# 验证版本格式（简单检查）
if ! [[ "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+ ]]; then
    echo "警告: 版本号格式可能不正确 (建议使用: x.y.z, 例如: 1.0.1)"
    read -p "是否继续? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 触发 workflow
echo "正在触发 Release Workflow..."
echo "仓库: $REPO"
echo "版本: $VERSION"
echo ""

response=$(curl -s -w "\n%{http_code}" -X POST \
  -H "Accept: application/vnd.github.v3+json" \
  -H "Authorization: token $TOKEN" \
  "https://api.github.com/repos/$REPO/dispatches" \
  -d "{
    \"event_type\": \"release\",
    \"client_payload\": {
      \"version\": \"$VERSION\"
    }
  }")

# 分离响应体和状态码
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | head -n-1)

# 检查结果
if [ "$http_code" = "204" ]; then
    echo "✓ Workflow 触发成功!"
    echo ""
    echo "请访问以下链接查看 workflow 运行状态:"
    echo "  https://github.com/$REPO/actions"
    exit 0
else
    echo "✗ 触发失败 (HTTP $http_code)"
    if [ -n "$body" ]; then
        echo "错误信息: $body"
    fi
    exit 1
fi

