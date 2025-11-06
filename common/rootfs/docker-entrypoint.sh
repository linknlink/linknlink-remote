#!/usr/bin/env bashio

bashio::log.info "Preparing to start FRPC Client..."

# 从配置中读取参数
SERVER_ADDR=$(bashio::config 'server_addr')
SERVER_PORT=$(bashio::config 'server_port')
TOKEN=$(bashio::config 'token')
LOCAL_IP=$(bashio::config 'local_ip')
LOCAL_PORT=$(bashio::config 'local_port')
SECRET_KEY=$(bashio::config 'secret_key')
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
    bashio::exit.nok "server_addr cannot be empty"
fi

if [ -z "$SERVER_PORT" ]; then
    bashio::exit.nok "server_port cannot be empty"
fi

# 配置文件路径
CONFIG_FILE="/config/frpc.toml"

# 确保配置目录存在
mkdir -p "$(dirname "$CONFIG_FILE")"

bashio::log.info "Generating FRPC configuration file: $CONFIG_FILE"

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
secretKey = ${SECRET_KEY}
EOF

# 如果是 HTTP/HTTPS 协议，添加额外配置
if [ "$PROTOCOL" = "http" ] || [ "$PROTOCOL" = "https" ]; then
    cat >> "$CONFIG_FILE" <<EOF

# HTTP/HTTPS 特定配置
customDomains = ["${PROXY_NAME}"]
EOF
fi

bashio::log.info "Configuration file generated successfully"
bashio::log.debug "Configuration content:"
cat "$CONFIG_FILE" | bashio::log.debug

# 检查 frpc 可执行文件
if [ ! -x "/usr/local/bin/frpc" ]; then
    bashio::exit.nok "FRPC executable not found at /usr/local/bin/frpc"
fi

bashio::log.info "Starting FRPC..."
bashio::log.info "Server address: ${SERVER_ADDR}:${SERVER_PORT}"
bashio::log.info "Local address: ${LOCAL_IP}:${LOCAL_PORT}"
bashio::log.info "Proxy name: ${PROXY_NAME}"
bashio::log.info "Protocol: ${PROTOCOL}"

# 显示预留配置状态（后续实现具体功能）
if [ "$AUTH_ENABLED" = "true" ]; then
    bashio::log.info "Authentication feature enabled (development in progress)"
fi

if [ "$THIRD_PARTY_ENABLED" = "true" ]; then
    bashio::log.info "Third-party service feature enabled (development in progress)"
fi

# 启动 frpc
exec /usr/local/bin/frpc -c "$CONFIG_FILE"

