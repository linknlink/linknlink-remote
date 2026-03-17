#!/bin/bash
set -e

# 创建运行时目录
mkdir -p /app/runtime/etc
mkdir -p /app/runtime/data

echo "运行时目录已创建: /app/runtime/etc, /app/runtime/data"

# 直接执行传入的命令，或者默认启动 Python 服务
exec "$@"
