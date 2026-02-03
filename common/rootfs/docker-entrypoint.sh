#!/bin/bash
set -e

# 修正权限（如果需要）
mkdir -p /data
mkdir -p /etc/frpc

# 直接执行传入的命令，或者默认启动 Python 服务
# 因为 web_config.py 现在负责了所有的初始化工作（获取 DeviceID, 登录, 心跳等）
exec "$@"
