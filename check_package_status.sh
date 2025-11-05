#!/bin/bash

# 配置
PACKAGE_NAME=linknlink-remote-frpc
TAGS=("amd64" "aarch64" "armhf" "armv7" "i386")

# 读取 token
TOKEN="${GITHUB_TOKEN}"

if [ -z "$TOKEN" ]; then
    echo "错误: 请设置 GITHUB_TOKEN 环境变量"
    exit 1
fi

echo "========================================="
echo "检查包状态: $PACKAGE_NAME"
echo "========================================="
echo ""

# 获取所有版本
echo "获取所有版本..."
VERSIONS=$(curl -s \
  -H "Authorization: token $TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  "https://api.github.com/user/packages/container/${PACKAGE_NAME}/versions")

if [ -z "$VERSIONS" ] || [ "$VERSIONS" = "[]" ]; then
    echo "❌ 没有找到任何版本"
    exit 0
fi

TOTAL_VERSIONS=$(echo "$VERSIONS" | jq '. | length')
echo "总版本数: $TOTAL_VERSIONS"
echo ""

# 统计
ARCH_COUNT=0
UNTAGGED_COUNT=0
OTHER_COUNT=0
ARCH_VERSIONS=()
UNTAGGED_VERSIONS=()
OTHER_VERSIONS=()

for VERSION_ID in $(echo "$VERSIONS" | jq -r '.[].id'); do
    TAGS_IN_VERSION=$(echo "$VERSIONS" | jq -r ".[] | select(.id == $VERSION_ID) | .metadata.container.tags[]?" | tr '\n' ' ')
    CREATED_AT=$(echo "$VERSIONS" | jq -r ".[] | select(.id == $VERSION_ID) | .created_at")
    
    if [ -z "$TAGS_IN_VERSION" ]; then
        UNTAGGED_COUNT=$((UNTAGGED_COUNT + 1))
        UNTAGGED_VERSIONS+=("$VERSION_ID")
    else
        # 检查是否包含架构标签
        HAS_ARCH_TAG=false
        for TAG in "${TAGS[@]}"; do
            if echo "$TAGS_IN_VERSION" | grep -q "\b$TAG\b"; then
                HAS_ARCH_TAG=true
                ARCH_VERSIONS+=("$VERSION_ID:$TAGS_IN_VERSION")
                break
            fi
        done
        
        if [ "$HAS_ARCH_TAG" = true ]; then
            ARCH_COUNT=$((ARCH_COUNT + 1))
        else
            OTHER_COUNT=$((OTHER_COUNT + 1))
            OTHER_VERSIONS+=("$VERSION_ID:$TAGS_IN_VERSION")
        fi
    fi
done

echo "========================================="
echo "版本统计:"
echo "  📦 架构标签版本: $ARCH_COUNT"
echo "  🏷️  其他标签版本: $OTHER_COUNT"
echo "  ❌ 未标记版本: $UNTAGGED_COUNT"
echo "========================================="
echo ""

# 显示架构标签版本详情
if [ $ARCH_COUNT -gt 0 ]; then
    echo "架构标签版本详情:"
    for VERSION in "${ARCH_VERSIONS[@]}"; do
        echo "  - $VERSION"
    done
    echo ""
fi

# 显示其他标签版本
if [ $OTHER_COUNT -gt 0 ]; then
    echo "其他标签版本:"
    for VERSION in "${OTHER_VERSIONS[@]}"; do
        echo "  - $VERSION"
    done
    echo ""
fi

# 显示未标记版本（如果数量少）
if [ $UNTAGGED_COUNT -gt 0 ] && [ $UNTAGGED_COUNT -le 10 ]; then
    echo "未标记版本 (最近 $UNTAGGED_COUNT 个):"
    for VERSION_ID in "${UNTAGGED_VERSIONS[@]:0:10}"; do
        CREATED_AT=$(echo "$VERSIONS" | jq -r ".[] | select(.id == $VERSION_ID) | .created_at")
        echo "  - $VERSION_ID (创建于: $CREATED_AT)"
    done
    echo ""
elif [ $UNTAGGED_COUNT -gt 10 ]; then
    echo "⚠️  还有 $UNTAGGED_COUNT 个未标记版本未显示"
    echo ""
fi

# 检查每个架构标签的 manifest 类型
echo "========================================="
echo "检查架构标签的 Manifest 类型:"
echo "========================================="

for TAG in "${TAGS[@]}"; do
    IMAGE_NAME="ghcr.io/acmen0102/${PACKAGE_NAME}:${TAG}"
    
    # 尝试检查 manifest
    MANIFEST_OUTPUT=$(docker manifest inspect "$IMAGE_NAME" 2>&1)
    
    if [ $? -eq 0 ]; then
        MEDIA_TYPE=$(echo "$MANIFEST_OUTPUT" | jq -r '.mediaType // .schemaVersion // "unknown"' 2>/dev/null || echo "unknown")
        
        if echo "$MANIFEST_OUTPUT" | jq -e '.manifests' >/dev/null 2>&1; then
            # 是 manifest list
            MANIFEST_COUNT=$(echo "$MANIFEST_OUTPUT" | jq '.manifests | length')
            echo "  ❌ $TAG: 是 manifest list (包含 $MANIFEST_COUNT 个清单)"
        else
            # 是单个镜像
            ARCH=$(echo "$MANIFEST_OUTPUT" | jq -r '.config.architecture // .architecture // "unknown"' 2>/dev/null || echo "unknown")
            OS=$(echo "$MANIFEST_OUTPUT" | jq -r '.config.os // .os // "unknown"' 2>/dev/null || echo "unknown")
            echo "  ✓ $TAG: 单个架构镜像 ($ARCH/$OS)"
        fi
    else
        echo "  ⚠️  $TAG: 不存在或无法访问"
        if echo "$MANIFEST_OUTPUT" | grep -q "unauthorized"; then
            echo "      (需要认证或包未公开)"
        elif echo "$MANIFEST_OUTPUT" | grep -q "manifest unknown"; then
            echo "      (标签不存在)"
        fi
    fi
done

echo ""

# 总结和建议
echo "========================================="
echo "总结和建议:"
echo "========================================="

if [ $UNTAGGED_COUNT -gt 0 ]; then
    echo "⚠️  还有 $UNTAGGED_COUNT 个未标记版本需要清理"
    echo "   运行: ./delete_tags.sh delete-untagged y"
    echo ""
fi

# 检查是否有 manifest list 问题
HAS_MANIFEST_LIST=false
for TAG in "${TAGS[@]}"; do
    IMAGE_NAME="ghcr.io/acmen0102/${PACKAGE_NAME}:${TAG}"
    MANIFEST_OUTPUT=$(docker manifest inspect "$IMAGE_NAME" 2>&1)
    if [ $? -eq 0 ] && echo "$MANIFEST_OUTPUT" | jq -e '.manifests' >/dev/null 2>&1; then
        HAS_MANIFEST_LIST=true
        break
    fi
done

if [ "$HAS_MANIFEST_LIST" = true ]; then
    echo "⚠️  发现 manifest list 问题"
    echo "   需要删除架构标签并重新构建"
    echo "   运行: ./delete_tags.sh delete-arch-tags y"
    echo "   然后: 在 GitHub Actions 中手动触发工作流"
    echo ""
fi

if [ $UNTAGGED_COUNT -eq 0 ] && [ "$HAS_MANIFEST_LIST" = false ] && [ $ARCH_COUNT -gt 0 ]; then
    echo "✅ 清理完成！"
    echo "   - 没有未标记版本"
    echo "   - 架构标签都是单个镜像"
    echo ""
    echo "下一步: 在 GitHub Actions 中手动触发工作流重新构建（如果需要）"
fi

echo ""
