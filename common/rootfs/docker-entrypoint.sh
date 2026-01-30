#!/bin/bash

set -euo pipefail

# 日志函数
log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] [$level] $message" >&2
}

log_info() {
    log "INFO" "$@"
}

log_warn() {
    log "WARN" "$@"
}

log_error() {
    log "ERROR" "$@"
}

log_debug() {
    if [ "${LOG_LEVEL:-info}" = "debug" ] || [ "${LOG_LEVEL:-info}" = "trace" ]; then
        log "DEBUG" "$@"
    fi
}

# 从环境变量读取配置
LOG_LEVEL="${LOG_LEVEL:-info}"
AUTH_EMAIL="${AUTH_EMAIL:-}"
AUTH_PASSWORD="${AUTH_PASSWORD:-}"
CONFIG_FILE="${CONFIG_FILE:-/config/frpc.toml}"
DATA_DIR="${DATA_DIR:-/data}"

log_info "Preparing to start LinknLink Remote..."

# 验证必需参数
if [ -z "$AUTH_EMAIL" ]; then
    log_error "AUTH_EMAIL environment variable cannot be empty"
    exit 1
fi

if [ -z "$AUTH_PASSWORD" ]; then
    log_error "AUTH_PASSWORD environment variable cannot be empty"
    exit 1
fi

# 配置文件路径
TEMP_DIR="/tmp/frpc_setup"
HEARTBEAT_SCRIPT="/usr/local/bin/frpc-heartbeat.sh"
HEARTBEAT_INTERVAL=30
mkdir -p "$TEMP_DIR"
cd "$TEMP_DIR" || exit 1

# 确保配置目录存在
mkdir -p "$(dirname "$CONFIG_FILE")"
mkdir -p "$DATA_DIR"

# =============================================================================
# 函数：获取设备ID（MAC地址或UUID）
# =============================================================================
get_device_id() {
    local device_id=""
    local stored_file="${DATA_DIR}/device_id.txt"
    local app_name="frpc"

    # 优先使用持久化存储的设备ID
    if [ -f "$stored_file" ]; then
        local saved_id
        saved_id=$(cat "$stored_file" 2>/dev/null | tr -d '[:space:]' | tr '[:upper:]' '[:lower:]')
        if [ -n "$saved_id" ]; then
            log_info "Using stored device ID: $saved_id"
            echo "$saved_id"
            return
        fi
    fi

    # 尝试获取MAC地址
    # 优先使用eth0，如果没有则使用其他网络接口
    local mac=""
    if [ -f /sys/class/net/eth0/address ]; then
        mac=$(cat /sys/class/net/eth0/address 2>/dev/null | tr -d ':' | tr '[:lower:]' '[:upper:]')
    else
        # 尝试获取第一个非lo接口的MAC地址
        for iface in /sys/class/net/*; do
            if [ -f "$iface/address" ]; then
                local ifname=$(basename "$iface")
                if [ "$ifname" != "lo" ]; then
                    mac=$(cat "$iface/address" 2>/dev/null | tr -d ':' | tr '[:lower:]' '[:upper:]')
                    if [ -n "$mac" ]; then
                        break
                    fi
                fi
            fi
        done
    fi
    
    # 如果获取到MAC地址，格式化为32位（前面补0）
    if [ -n "$mac" ] && [ ${#mac} -le 32 ]; then
        # 计算需要补0的个数
        local padding=$((32 - ${#mac}))
        if [ $padding -gt 0 ]; then
            # 生成指定数量的0
            local zeros=""
            for ((i=0; i<padding; i++)); do
                zeros="${zeros}0"
            done
            device_id="${zeros}${mac}"
        else
            device_id="$mac"
        fi
        log_info "Using MAC address as device ID: $device_id"
    else
        # 如果获取不到MAC地址，使用UUID
        if command -v uuidgen &> /dev/null; then
            device_id=$(uuidgen | tr -d '-' | tr '[:lower:]' '[:upper:]')
            log_info "MAC address not available, using UUID as device ID: $device_id"
        else
            # 如果uuidgen也不可用，生成一个基于时间戳的ID
            device_id=$(date +%s%N | sha256sum | head -c 32 | tr '[:lower:]' '[:upper:]')
            log_warn "UUID generator not available, using generated ID: $device_id"
        fi
    fi
    
    # 将 device_id 转换为小写
    device_id=$(echo "$device_id" | tr '[:upper:]' '[:lower:]')
    
    # 持久化保存设备ID，确保重启或重新安装后仍然固定
    echo "$device_id" > "$stored_file"
    log_info "Persisted generated device ID: $device_id"

    echo "$device_id"
}

# =============================================================================
# 函数：加密密码（使用SHA1）
# =============================================================================
encrypt_password() {
    local password="$1"
    local salt="4969fj#k23#"
    local combined="${password}${salt}"
    
    # 使用sha1sum计算SHA1哈希，并提取十六进制字符串
    echo -n "$combined" | sha1sum | cut -d' ' -f1
}

# =============================================================================
# 函数：调用登录接口获取companyid和userid
# =============================================================================
login() {
    local account="$1"
    local password="$2"
    
    log_info "Attempting to login with account: $account"
    
    # 对密码进行加密
    local encrypted_password
    encrypted_password=$(encrypt_password "$password")
    
    # 调用登录接口（使用email字段）
    local login_url="https://euhome.linklinkiot.com/sfsaas/api/user/pwdlogin"
    local login_data="{\"email\":\"$account\",\"password\":\"$encrypted_password\"}"
    
    log_debug "Login request URL: $login_url"
    log_debug "Login request data: $login_data"
    
    local http_response
    local http_code
    local response
    local curl_exit_code
    
    http_response=$(curl -s -w "\n%{http_code}" -X POST \
        -H "Content-Type: application/json" \
        -d "$login_data" \
        "$login_url" 2>&1)
    
    curl_exit_code=$?
    if [ $curl_exit_code -ne 0 ]; then
        log_error "Login request failed (curl exit code: $curl_exit_code)"
        exit 1
    fi
    
    # 分离HTTP状态码和响应内容
    http_code=$(echo "$http_response" | tail -n1)
    response=$(echo "$http_response" | head -n -1)
    
    log_debug "Login HTTP status code: $http_code"
    log_debug "Login response: $response"
    
    # 检查HTTP状态码
    if [ "$http_code" != "200" ]; then
        log_error "Login request failed with HTTP code: $http_code"
        log_error "Response: $response"
        exit 1
    fi
    
    # 解析响应
    local status
    local msg
    if command -v jq &> /dev/null; then
        # 使用jq解析JSON
        status=$(echo "$response" | jq -r '.status' 2>/dev/null)
        
        # status不等于0就是有问题的，表示登录失败
        if [ -z "$status" ] || [ "$status" = "null" ]; then
            log_error "Invalid login response: missing status field"
            exit 1
        fi
        
        if [ "$status" != "0" ]; then
            msg=$(echo "$response" | jq -r '.msg // .message // "Unknown error"' 2>/dev/null)
            
            # 特别处理-46009表示账号不存在
            if [ "$status" = "-46009" ]; then
                log_error "Login failed: Account does not exist (status: $status)"
                log_error "Message: $msg"
                exit 1
            else
                log_error "Login failed with status: $status"
                log_error "Message: $msg"
                exit 1
            fi
        fi
        
        # 提取companyid和userid
        COMPANY_ID=$(echo "$response" | jq -r '.info.companyid' 2>/dev/null)
        USER_ID=$(echo "$response" | jq -r '.info.userid' 2>/dev/null)
        
        # 检查info字段是否存在
        if [ "$COMPANY_ID" = "null" ] || [ -z "$COMPANY_ID" ]; then
            log_error "Login response missing companyid"
            exit 1
        fi
        
        if [ "$USER_ID" = "null" ] || [ -z "$USER_ID" ]; then
            log_error "Login response missing userid"
            exit 1
        fi
        
        # 尝试获取account，如果没有则使用输入的account
        ACCOUNT=$(echo "$response" | jq -r '.info.account // ""' 2>/dev/null)
        if [ -z "$ACCOUNT" ] || [ "$ACCOUNT" = "null" ]; then
            ACCOUNT="$account"
        fi
    else
        # 如果没有jq，使用grep和sed解析
        status=$(echo "$response" | grep -o '"status":[^,}]*' | grep -oE '-?[0-9]+' | head -n1 || echo "")
        
        if [ -z "$status" ]; then
            log_error "Invalid login response: missing status field"
            exit 1
        fi
        
        # status不等于0就是有问题的，表示登录失败
        if [ "$status" != "0" ]; then
            msg=$(echo "$response" | sed -n 's/.*"msg"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')
            
            # 特别处理-46009表示账号不存在
            if [ "$status" = "-46009" ]; then
                log_error "Login failed: Account does not exist (status: $status)"
                log_error "Message: $msg"
                exit 1
            else
                log_error "Login failed with status: $status"
                log_error "Message: $msg"
                exit 1
            fi
        fi
        
        COMPANY_ID=$(echo "$response" | sed -n 's/.*"companyid"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')
        USER_ID=$(echo "$response" | sed -n 's/.*"userid"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')
        
        if [ -z "$COMPANY_ID" ]; then
            log_error "Login response missing companyid"
            exit 1
        fi
        
        if [ -z "$USER_ID" ]; then
            log_error "Login response missing userid"
            exit 1
        fi
        
        ACCOUNT="$account"
    fi
    
    log_info "Login successful - User ID: $USER_ID"
}

# =============================================================================
# 函数：注册frpc代理并获取配置
# =============================================================================
register_frpc_proxy() {
    local device_id="$1"
    local company_id="$2"
    local user_id="$3"
    local account="$4"
    
    log_info "Registering FRPC proxy with device ID: $device_id"
    
    # 构造proxyList JSON（直接使用变量，无需写文件）
    local proxy_json='[{"serviceName":"HomeAssistant","localPort":8123,"bindPort":38123,"link":true}]'
    
    # 构造请求数据
    local server_url="https://euadmin.linklinkiot.com/frpserver/api/proxy"
    local json_data="{\"did\":\"$device_id\",\"name\":\"HA\",\"type\":99,\"account\":\"$account\",\"heartbeat\":1,\"proxyList\":$proxy_json}"
    
    log_debug "Registration request: $json_data"
    
    # 发送请求
    local http_response
    http_response=$(curl -s -w "\n%{http_code}" -X POST \
        -H "Content-Type: application/json" \
        -H "companyid: $company_id" \
        -H "userid: $user_id" \
        -d "$json_data" \
        "$server_url" 2>&1)
    
    local http_code
    http_code=$(echo "$http_response" | tail -n1)
    local content
    content=$(echo "$http_response" | head -n -1)
    
    log_debug "Registration response code: $http_code"
    
    # 检查HTTP状态码
    if [ "$http_code" != "200" ]; then
        log_error "Registration failed with HTTP code: $http_code"
        log_error "Response: $content"
        exit 1
    fi
    
    # 检查响应是否为JSON格式的错误信息
    if [[ $content == \{* ]]; then
        local status
        if command -v jq &> /dev/null; then
            status=$(echo "$content" | jq -r '.status' 2>/dev/null)
            if [ "$status" != "null" ] && [ "$status" != "0" ]; then
                local msg=$(echo "$content" | jq -r '.msg // .message // "Unknown error"' 2>/dev/null)
                log_error "Registration failed: $msg"
                exit 1
            fi
        else
            # 使用grep检查status字段
            status=$(echo "$content" | grep -o '"status":[^,}]*' | grep -o '[0-9]*' || echo "")
            if [ -n "$status" ] && [ "$status" != "0" ]; then
                log_error "Registration failed with status: $status"
                exit 1
            fi
        fi
    fi
    
    # 将响应保存为配置文件
    echo "$content" > "$CONFIG_FILE"
    
    # 在 host 网络模式下，容器直接使用宿主机的网络命名空间
    # 127.0.0.1 就是宿主机本身，可以直接访问宿主机的服务（如 8123 端口）
    # 因此不需要替换 127.0.0.1
    
    log_info "FRPC configuration file generated successfully: $CONFIG_FILE"
}

# =============================================================================
# 函数：显示设备信息
# =============================================================================
display_device_info() {
    local device_id="$1"
    
    # 确保配置目录存在
    mkdir -p "$(dirname "$CONFIG_FILE")"
    
    # 将 device_id 保存到文件，方便用户查看
    local device_id_file="$(dirname "$CONFIG_FILE")/device_id.txt"
    echo "$device_id" > "$device_id_file"
    
    # 以醒目的方式输出设备ID信息
    log_info ""
    log_info "=========================================="
    log_info "  Device ID: $device_id"
    log_info "=========================================="
    log_info ""
}

# =============================================================================
# 主流程
# =============================================================================

# 1. 获取设备ID
DEVICE_ID=$(get_device_id)

# 显示设备信息
display_device_info "$DEVICE_ID"

# 2. 调用登录接口
login "$AUTH_EMAIL" "$AUTH_PASSWORD"

# 3. 注册frpc代理并获取配置
register_frpc_proxy "$DEVICE_ID" "$COMPANY_ID" "$USER_ID" "$ACCOUNT"

# 检查 frpc 可执行文件
if [ ! -x "/usr/local/bin/frpc" ]; then
    log_error "FRPC executable not found at /usr/local/bin/frpc"
    exit 1
fi

log_info "Starting FRPC..."
log_info "Configuration file: $CONFIG_FILE"
log_debug "Configuration content:"
if [ -f "$CONFIG_FILE" ]; then
    # 逐行输出配置内容，并隐藏敏感的 token 字段
    while IFS= read -r line || [ -n "$line" ]; do
        sanitized_line="$line"
        if [[ "$sanitized_line" == *"token"* ]]; then
            sanitized_line=$(echo "$sanitized_line" | sed -E 's/(token[[:space:]]*=[[:space:]]*")[^"]+(")/\1*****\2/')
            sanitized_line=$(echo "$sanitized_line" | sed -E 's/("token"[[:space:]]*:[[:space:]]*")[^"]+(")/\1*****\2/')
        fi
        log_debug "$sanitized_line"
    done < "$CONFIG_FILE"
else
    log_warn "Configuration file not found: $CONFIG_FILE"
fi

# 清理临时目录
cd / || exit 1
rm -rf "$TEMP_DIR"

# 启动 frpc
/usr/local/bin/frpc -c "$CONFIG_FILE" &
FRPC_PID=$!

log_info "FRPC started with PID: $FRPC_PID"

cleanup() {
    local exit_code=${1:-0}

    log_info "Stopping FRPC heartbeat and process..."

    if [ -n "${HEARTBEAT_PID:-}" ]; then
        kill "$HEARTBEAT_PID" 2>/dev/null || true
        wait "$HEARTBEAT_PID" 2>/dev/null || true
    fi

    if kill -0 "$FRPC_PID" 2>/dev/null; then
        kill "$FRPC_PID" 2>/dev/null || true
        wait "$FRPC_PID" 2>/dev/null || true
    fi

    if [ -x "$HEARTBEAT_SCRIPT" ]; then
        LOG_LEVEL="${LOG_LEVEL}" "$HEARTBEAT_SCRIPT" "$DEVICE_ID" "$COMPANY_ID" "$USER_ID"
    fi

    exit "$exit_code"
}

trap 'cleanup 0' SIGTERM SIGINT

if [ -x "$HEARTBEAT_SCRIPT" ]; then
    log_info "Starting FRPC heartbeat task (interval ${HEARTBEAT_INTERVAL}s)..."
    (
        while true; do
            LOG_LEVEL="${LOG_LEVEL}" "$HEARTBEAT_SCRIPT" "$DEVICE_ID" "$COMPANY_ID" "$USER_ID" "$FRPC_PID" || true
            sleep "$HEARTBEAT_INTERVAL" &
            wait $!
        done
    ) &
    HEARTBEAT_PID=$!
else
    log_warn "Heartbeat script not found or not executable: $HEARTBEAT_SCRIPT"
fi

wait "$FRPC_PID"
FRPC_EXIT_CODE=$?

log_info "FRPC process exited with code: $FRPC_EXIT_CODE"

if [ -n "${HEARTBEAT_PID:-}" ]; then
    kill "$HEARTBEAT_PID" 2>/dev/null || true
    wait "$HEARTBEAT_PID" 2>/dev/null || true
fi

# 上报最终一次心跳，标记为未运行
if [ -x "$HEARTBEAT_SCRIPT" ]; then
    LOG_LEVEL="${LOG_LEVEL}" "$HEARTBEAT_SCRIPT" "$DEVICE_ID" "$COMPANY_ID" "$USER_ID"
fi

exit "$FRPC_EXIT_CODE"
