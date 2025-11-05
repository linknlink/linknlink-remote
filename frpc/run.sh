#!/usr/bin/with-contenv bashio

# =============================================================================
# FRPC Add-on for Home Assistant
# 启动脚本
# =============================================================================

set -e

# 日志函数
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*" >&2
}

# 从配置中读取参数
SERVER_ADDR=$(bashio::config 'server_addr')
SERVER_PORT=$(bashio::config 'server_port')
TOKEN=$(bashio::config 'token')
LOCAL_IP=$(bashio::config 'local_ip')
LOCAL_PORT=$(bashio::config 'local_port')
REMOTE_PORT=$(bashio::config 'remote_port')
PROXY_NAME=$(bashio::config 'proxy_name')
PROTOCOL=$(bashio::config 'protocol')
LOG_LEVEL=$(bashio::config 'log_level')
LOG_MAX_DAYS=$(bashio::config 'log_max_days')

# 读取预留配置（后续实现）
AUTH_ENABLED=$(bashio::config 'authentication.enabled' false)
AUTH_ACCOUNT=$(bashio::config 'authentication.account' "")
AUTH_PASSWORD=$(bashio::config 'authentication.password' "")

THIRD_PARTY_ENABLED=$(bashio::config 'third_party.enabled' false)
THIRD_PARTY_PROVIDER=$(bashio::config 'third_party.provider' "")
THIRD_PARTY_API_KEY=$(bashio::config 'third_party.api_key' "")
THIRD_PARTY_API_SECRET=$(bashio::config 'third_party.api_secret' "")

# 验证必需参数
if [ -z "$SERVER_ADDR" ]; then
    log "错误: server_addr 不能为空"
    exit 1
fi

if [ -z "$SERVER_PORT" ]; then
    log "错误: server_port 不能为空"
    exit 1
fi

# 配置文件路径
CONFIG_FILE="/config/frpc.toml"

log "正在生成 frpc 配置文件: $CONFIG_FILE"

# 生成 frpc 配置文件 (TOML 格式)
cat > "$CONFIG_FILE" <<EOF
# FRPC 配置文件
# 由 Home Assistant Add-on 自动生成

serverAddr = "${SERVER_ADDR}"
serverPort = ${SERVER_PORT}

# 日志配置
log.level = "${LOG_LEVEL}"
log.maxDays = ${LOG_MAX_DAYS}
log.to = "/config/frpc.log"
EOF

# 如果提供了 token，添加认证
if [ -n "$TOKEN" ]; then
    echo "auth.token = \"${TOKEN}\"" >> "$CONFIG_FILE"
fi

# 添加代理配置
cat >> "$CONFIG_FILE" <<EOF

# 代理配置
[[proxies]]
name = "${PROXY_NAME}"
type = "${PROTOCOL}"
localIP = "${LOCAL_IP}"
localPort = ${LOCAL_PORT}
remotePort = ${REMOTE_PORT}
EOF

# 如果是 HTTP/HTTPS 协议，添加额外配置
if [ "$PROTOCOL" = "http" ] || [ "$PROTOCOL" = "https" ]; then
    cat >> "$CONFIG_FILE" <<EOF

# HTTP/HTTPS 特定配置
customDomains = ["${PROXY_NAME}"]
EOF
fi

log "配置文件生成完成:"
cat "$CONFIG_FILE"
log "============================"

# 检查 frpc 可执行文件
if [ ! -x "/usr/local/bin/frpc" ]; then
    log "错误: 找不到 frpc 可执行文件"
    exit 1
fi

log "正在启动 frpc..."
log "服务器地址: ${SERVER_ADDR}:${SERVER_PORT}"
log "本地地址: ${LOCAL_IP}:${LOCAL_PORT}"
log "远程端口: ${REMOTE_PORT}"
log "代理名称: ${PROXY_NAME}"
log "协议类型: ${PROTOCOL}"

# 显示预留配置状态（后续实现具体功能）
if [ "$AUTH_ENABLED" = "true" ]; then
    log "提示: 私有账号登录功能已启用（功能开发中）"
fi

if [ "$THIRD_PARTY_ENABLED" = "true" ]; then
    log "提示: 第三方服务功能已启用（功能开发中）"
fi

# 启动 frpc
exec /usr/local/bin/frpc -c "$CONFIG_FILE"
