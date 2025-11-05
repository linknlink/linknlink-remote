#!/bin/bash

# 配置
GITHUB_USER=Acmen0102
PACKAGE_NAME=linknlink-remote-frpc
TAGS=("amd64" "aarch64" "armhf" "armv7" "i386")

# 读取 token（必须从环境变量读取，不要硬编码！）
TOKEN="${GITHUB_TOKEN}"

if [ -z "$TOKEN" ]; then
    echo "错误: 请设置 GITHUB_TOKEN 环境变量"
    echo "export GITHUB_TOKEN=your_token_here"
    exit 1
fi

# 解析命令行参数
MODE="${1:-interactive}"  # interactive, delete-arch-tags, delete-untagged, delete-all
AUTO_CONFIRM="${2:-n}"    # y 表示自动确认，不需要交互

case "$MODE" in
    "delete-arch-tags")
        echo "模式: 删除架构标签版本"
        DELETE_ARCH_TAGS=true
        DELETE_UNTAGGED=false
        ;;
    "delete-untagged")
        echo "模式: 删除所有未标记版本"
        DELETE_ARCH_TAGS=false
        DELETE_UNTAGGED=true
        ;;
    "delete-all")
        echo "模式: 删除所有版本（危险操作！）"
        DELETE_ARCH_TAGS=true
        DELETE_UNTAGGED=true
        ;;
    *)
        echo "使用说明:"
        echo "  ./delete_tags.sh delete-arch-tags [y]  - 删除架构标签版本 (amd64, aarch64, etc.)"
        echo "  ./delete_tags.sh delete-untagged [y]   - 删除所有未标记版本"
        echo "  ./delete_tags.sh delete-all [y]        - 删除所有版本（危险！）"
        echo ""
        echo "第二个参数 'y' 表示自动确认，不需要交互提示"
        echo ""
        echo "示例:"
        echo "  ./delete_tags.sh delete-arch-tags      # 交互式删除架构标签"
        echo "  ./delete_tags.sh delete-untagged y     # 自动删除所有未标记版本"
        exit 0
        ;;
esac

echo "获取所有版本..."
VERSIONS=$(curl -s \
  -H "Authorization: token $TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  "https://api.github.com/user/packages/container/${PACKAGE_NAME}/versions")

if [ -z "$VERSIONS" ] || [ "$VERSIONS" = "[]" ]; then
    echo "没有找到任何版本"
    exit 0
fi

TOTAL_VERSIONS=$(echo "$VERSIONS" | jq '. | length')
echo "总共找到 $TOTAL_VERSIONS 个版本"
echo ""

# 统计信息
ARCH_COUNT=0
UNTAGGED_COUNT=0
OTHER_COUNT=0

# 先统计
for VERSION_ID in $(echo "$VERSIONS" | jq -r '.[].id'); do
    TAGS_IN_VERSION=$(echo "$VERSIONS" | jq -r ".[] | select(.id == $VERSION_ID) | .metadata.container.tags[]?" | tr '\n' ' ')
    
    if [ -z "$TAGS_IN_VERSION" ]; then
        UNTAGGED_COUNT=$((UNTAGGED_COUNT + 1))
    else
        # 检查是否包含架构标签
        HAS_ARCH_TAG=false
        for TAG in "${TAGS[@]}"; do
            if echo "$TAGS_IN_VERSION" | grep -q "\b$TAG\b"; then
                HAS_ARCH_TAG=true
                break
            fi
        done
        
        if [ "$HAS_ARCH_TAG" = true ]; then
            ARCH_COUNT=$((ARCH_COUNT + 1))
        else
            OTHER_COUNT=$((OTHER_COUNT + 1))
        fi
    fi
done

echo "版本统计:"
echo "  - 架构标签版本: $ARCH_COUNT"
echo "  - 未标记版本: $UNTAGGED_COUNT"
echo "  - 其他标签版本: $OTHER_COUNT"
echo ""

# 确认删除
if [ "$AUTO_CONFIRM" != "y" ]; then
    case "$MODE" in
        "delete-arch-tags")
            read -p "确认删除 $ARCH_COUNT 个架构标签版本? (y/N): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                echo "取消操作"
                exit 0
            fi
            ;;
        "delete-untagged")
            read -p "确认删除 $UNTAGGED_COUNT 个未标记版本? (y/N): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                echo "取消操作"
                exit 0
            fi
            ;;
        "delete-all")
            read -p "⚠️  警告: 将删除所有 $TOTAL_VERSIONS 个版本！确认? (yes/N): " -r
            echo
            if [ "$REPLY" != "yes" ]; then
                echo "取消操作"
                exit 0
            fi
            ;;
    esac
fi

# 执行删除
DELETED=0
FAILED=0

for VERSION_ID in $(echo "$VERSIONS" | jq -r '.[].id'); do
    TAGS_IN_VERSION=$(echo "$VERSIONS" | jq -r ".[] | select(.id == $VERSION_ID) | .metadata.container.tags[]?" | tr '\n' ' ')
    CREATED_AT=$(echo "$VERSIONS" | jq -r ".[] | select(.id == $VERSION_ID) | .created_at")
    
    # 决定是否删除
    SHOULD_DELETE=false
    
    if [ -z "$TAGS_IN_VERSION" ]; then
        # 未标记版本
        if [ "$DELETE_UNTAGGED" = true ]; then
            SHOULD_DELETE=true
        fi
    else
        # 检查是否包含架构标签
        if [ "$DELETE_ARCH_TAGS" = true ]; then
            for TAG in "${TAGS[@]}"; do
                if echo "$TAGS_IN_VERSION" | grep -q "\b$TAG\b"; then
                    SHOULD_DELETE=true
                    break
                fi
            done
        fi
    fi
    
    if [ "$SHOULD_DELETE" = true ]; then
        if [ -z "$TAGS_IN_VERSION" ]; then
            echo "[$DELETED/$((ARCH_COUNT + UNTAGGED_COUNT))] 删除未标记版本: $VERSION_ID (创建于: $CREATED_AT)"
        else
            echo "[$DELETED/$((ARCH_COUNT + UNTAGGED_COUNT))] 删除版本: $VERSION_ID (标签: $TAGS_IN_VERSION)"
        fi
        
        RESPONSE=$(curl -s -w "\n%{http_code}" -X DELETE \
          -H "Authorization: token $TOKEN" \
          -H "Accept: application/vnd.github.v3+json" \
          "https://api.github.com/user/packages/container/${PACKAGE_NAME}/versions/${VERSION_ID}")
        
        HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
        if [ "$HTTP_CODE" = "204" ]; then
            DELETED=$((DELETED + 1))
            echo "    ✓ 成功删除"
        else
            FAILED=$((FAILED + 1))
            echo "    ✗ 删除失败 (HTTP $HTTP_CODE)"
            ERROR_MSG=$(echo "$RESPONSE" | head -n-1 | jq -r '.message // .' 2>/dev/null || echo "$RESPONSE" | head -n-1)
            if [ ! -z "$ERROR_MSG" ]; then
                echo "    错误: $ERROR_MSG"
            fi
        fi
        
        # 避免触发 API 速率限制，每秒最多 5 个请求
        sleep 0.2
    fi
done

echo ""
echo "========================================="
echo "删除完成！"
echo "  成功: $DELETED"
echo "  失败: $FAILED"
echo "========================================="

if [ $FAILED -gt 0 ]; then
    exit 1
fi
