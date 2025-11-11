#!/usr/bin/env bashio

LOG_LEVEL=$(bashio::config 'log_level' 'info')
bashio::log.level "${LOG_LEVEL}"

bashio::log.info "Preparing to start FRPC Client..."

# 从配置中读取账号密码
AUTH_ACCOUNT=$(bashio::config 'authentication.email' "")
AUTH_PASSWORD=$(bashio::config 'authentication.password' "")

# 验证必需参数
if [ -z "$AUTH_ACCOUNT" ]; then
    bashio::exit.nok "authentication.email cannot be empty"
fi

if [ -z "$AUTH_PASSWORD" ]; then
    bashio::exit.nok "authentication.password cannot be empty"
fi

# 配置文件路径
CONFIG_FILE="/config/frpc.toml"
TEMP_DIR="/tmp/frpc_setup"
HEARTBEAT_SCRIPT="/usr/local/bin/frpc-heartbeat.sh"
HEARTBEAT_INTERVAL=30
mkdir -p "$TEMP_DIR"
cd "$TEMP_DIR" || exit 1

# 确保配置目录存在
mkdir -p "$(dirname "$CONFIG_FILE")"

# =============================================================================
# 函数：获取设备ID（MAC地址或UUID）
# =============================================================================
get_device_id() {
    local device_id=""
    local data_dir="/data"
    local stored_file="${data_dir}/device_id.txt"
    local addon_slug="frpc"

    # 确保数据目录存在
    mkdir -p "$data_dir"

    # 优先使用持久化存储的设备ID
    if [ -f "$stored_file" ]; then
        local saved_id
        saved_id=$(cat "$stored_file" 2>/dev/null | tr -d '[:space:]' | tr '[:upper:]' '[:lower:]')
        if [ -n "$saved_id" ]; then
            bashio::log.info "Using stored device ID: $saved_id"
            echo "$saved_id"
            return
        fi
    fi
    
    # 如果持久化文件不存在，尝试基于Supervisor的UUID生成确定性的设备ID
    if [ -z "$device_id" ]; then
        if [ -n "${SUPERVISOR_TOKEN:-}" ]; then
            local supervisor_response=""
            supervisor_response=$(curl -s --fail \
                -H "Authorization: Bearer $SUPERVISOR_TOKEN" \
                -H "Content-Type: application/json" \
                "http://supervisor/info" 2>/dev/null || true)

            if [ -n "$supervisor_response" ]; then
                local supervisor_uuid=""
                if command -v jq &> /dev/null; then
                    supervisor_uuid=$(echo "$supervisor_response" | jq -r '.data.uuid // empty' 2>/dev/null)
                else
                    supervisor_uuid=$(echo "$supervisor_response" | sed -n 's/.*"uuid"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -n1)
                fi

                if [ -n "$supervisor_uuid" ]; then
                    device_id=$(echo -n "${supervisor_uuid}_${addon_slug}" | sha256sum | head -c 32 | tr '[:upper:]' '[:lower:]')
                    bashio::log.info "Generated deterministic device ID from supervisor UUID: $device_id"
                    echo "$device_id" > "$stored_file"
                    echo "$device_id"
                    return
                else
                    bashio::log.warning "Unable to parse supervisor UUID, fallback to MAC/UUID generation."
                fi
            else
                bashio::log.warning "Failed to query supervisor info for deterministic device ID."
            fi
        else
            bashio::log.warning "SUPERVISOR_TOKEN missing, cannot query supervisor info."
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
        bashio::log.info "Using MAC address as device ID: $device_id"
    else
        # 如果获取不到MAC地址，使用UUID
        if command -v uuidgen &> /dev/null; then
            device_id=$(uuidgen | tr -d '-' | tr '[:lower:]' '[:upper:]')
            bashio::log.info "MAC address not available, using UUID as device ID: $device_id"
        else
            # 如果uuidgen也不可用，生成一个基于时间戳的ID
            device_id=$(date +%s%N | sha256sum | head -c 32 | tr '[:lower:]' '[:upper:]')
            bashio::log.warning "UUID generator not available, using generated ID: $device_id"
        fi
    fi
    
    # 将 device_id 转换为小写
    device_id=$(echo "$device_id" | tr '[:upper:]' '[:lower:]')
    
    # 持久化保存设备ID，确保重启或重新安装后仍然固定
    echo "$device_id" > "$stored_file"
    bashio::log.info "Persisted generated device ID: $device_id"

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
    
    bashio::log.info "Attempting to login with account: $account"
    
    # 对密码进行加密
    local encrypted_password
    encrypted_password=$(encrypt_password "$password")
    
    # 调用登录接口（使用email字段）
    local login_url="https://euhome.linklinkiot.com/sfsaas/api/user/pwdlogin"
    local login_data="{\"email\":\"$account\",\"password\":\"$encrypted_password\"}"
    
    bashio::log.debug "Login request URL: $login_url"
    bashio::log.debug "Login request data: $login_data"
    
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
        bashio::log.error "Login request failed (curl exit code: $curl_exit_code)"
        bashio::exit.nok "Failed to connect to login server"
    fi
    
    # 分离HTTP状态码和响应内容
    http_code=$(echo "$http_response" | tail -n1)
    response=$(echo "$http_response" | head -n -1)
    
    bashio::log.debug "Login HTTP status code: $http_code"
    bashio::log.debug "Login response: $response"
    
    # 检查HTTP状态码
    if [ "$http_code" != "200" ]; then
        bashio::log.error "Login request failed with HTTP code: $http_code"
        bashio::log.error "Response: $response"
        bashio::exit.nok "Login request failed with HTTP code: $http_code"
    fi
    
    # 解析响应
    local status
    local msg
    if command -v jq &> /dev/null; then
        # 使用jq解析JSON
        status=$(echo "$response" | jq -r '.status' 2>/dev/null)
        
        # status不等于0就是有问题的，表示登录失败
        if [ -z "$status" ] || [ "$status" = "null" ]; then
            bashio::log.error "Invalid login response: missing status field"
            bashio::exit.nok "Invalid login response format"
        fi
        
        if [ "$status" != "0" ]; then
            msg=$(echo "$response" | jq -r '.msg // .message // "Unknown error"' 2>/dev/null)
            
            # 特别处理-46009表示账号不存在
            if [ "$status" = "-46009" ]; then
                bashio::log.error "Login failed: Account does not exist (status: $status)"
                bashio::log.error "Message: $msg"
                bashio::exit.nok "Account does not exist, please contact HR to add the account"
            else
                bashio::log.error "Login failed with status: $status"
                bashio::log.error "Message: $msg"
                bashio::exit.nok "Login failed (status: $status): $msg"
            fi
        fi
        
        # 提取companyid和userid
        COMPANY_ID=$(echo "$response" | jq -r '.info.companyid' 2>/dev/null)
        USER_ID=$(echo "$response" | jq -r '.info.userid' 2>/dev/null)
        
        # 检查info字段是否存在
        if [ "$COMPANY_ID" = "null" ] || [ -z "$COMPANY_ID" ]; then
            bashio::log.error "Login response missing companyid"
            bashio::exit.nok "Login response missing required field: companyid"
        fi
        
        if [ "$USER_ID" = "null" ] || [ -z "$USER_ID" ]; then
            bashio::log.error "Login response missing userid"
            bashio::exit.nok "Login response missing required field: userid"
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
            bashio::log.error "Invalid login response: missing status field"
            bashio::exit.nok "Invalid login response format"
        fi
        
        # status不等于0就是有问题的，表示登录失败
        if [ "$status" != "0" ]; then
            msg=$(echo "$response" | sed -n 's/.*"msg"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')
            
            # 特别处理-46009表示账号不存在
            if [ "$status" = "-46009" ]; then
                bashio::log.error "Login failed: Account does not exist (status: $status)"
                bashio::log.error "Message: $msg"
                bashio::exit.nok "Account does not exist, please contact HR to add the account"
            else
                bashio::log.error "Login failed with status: $status"
                bashio::log.error "Message: $msg"
                bashio::exit.nok "Login failed (status: $status): $msg"
            fi
        fi
        
        COMPANY_ID=$(echo "$response" | sed -n 's/.*"companyid"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')
        USER_ID=$(echo "$response" | sed -n 's/.*"userid"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')
        
        if [ -z "$COMPANY_ID" ]; then
            bashio::log.error "Login response missing companyid"
            bashio::exit.nok "Login response missing required field: companyid"
        fi
        
        if [ -z "$USER_ID" ]; then
            bashio::log.error "Login response missing userid"
            bashio::exit.nok "Login response missing required field: userid"
        fi
        
        ACCOUNT="$account"
    fi
    
    bashio::log.info "Login successful - User ID: $USER_ID"
}

# =============================================================================
# 函数：注册frpc代理并获取配置
# =============================================================================
register_frpc_proxy() {
    local device_id="$1"
    local company_id="$2"
    local user_id="$3"
    local account="$4"
    
    bashio::log.info "Registering FRPC proxy with device ID: $device_id"
    
    # 构造proxyList JSON（直接使用变量，无需写文件）
    local proxy_json='[{"serviceName":"HomeAssistant","localPort":8123,"bindPort":38123,"link":true}]'
    
    # 构造请求数据
    local server_url="https://euadmin.linklinkiot.com/frpserver/api/proxy"
    local json_data="{\"did\":\"$device_id\",\"name\":\"HA\",\"type\":99,\"account\":\"$account\",\"heartbeat\":1,\"proxyList\":$proxy_json}"
    
    bashio::log.debug "Registration request: $json_data"
    
    # 发送请求
    local response_file="response.json"
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
    
    bashio::log.debug "Registration response code: $http_code"
    bashio::log.debug "Registration response: $content"
    
    # 检查HTTP状态码
    if [ "$http_code" != "200" ]; then
        bashio::log.error "Registration failed with HTTP code: $http_code"
        bashio::log.error "Response: $content"
        bashio::exit.nok "Failed to register FRPC proxy"
    fi
    
    # 检查响应是否为JSON格式的错误信息
    if [[ $content == \{* ]]; then
        local status
        if command -v jq &> /dev/null; then
            status=$(echo "$content" | jq -r '.status' 2>/dev/null)
            if [ "$status" != "null" ] && [ "$status" != "0" ]; then
                local msg=$(echo "$content" | jq -r '.msg // .message // "Unknown error"' 2>/dev/null)
                bashio::log.error "Registration failed: $msg"
                bashio::exit.nok "Registration failed: $msg"
            fi
        else
            # 使用grep检查status字段
            status=$(echo "$content" | grep -o '"status":[^,}]*' | grep -o '[0-9]*' || echo "")
            if [ -n "$status" ] && [ "$status" != "0" ]; then
                bashio::log.error "Registration failed with status: $status"
                bashio::exit.nok "Registration failed"
            fi
        fi
    fi
    
    # 将响应保存为配置文件
    echo "$content" > "$CONFIG_FILE"
    
    # 在 host 网络模式下，容器直接使用宿主机的网络命名空间
    # 127.0.0.1 就是宿主机本身，可以直接访问宿主机的服务（如 8123 端口）
    # 因此不需要替换 127.0.0.1
    # 
    # 如果将来需要支持桥接网络模式，可以使用以下逻辑获取宿主机IP：
    local host_ip=""
    if command -v ip &> /dev/null; then
        host_ip=$(ip route | awk '/default/ {print $3}' | head -n1)
    fi
    if [ -n "$host_ip" ] && [ "$host_ip" != "" ]; then
        sed -i "s/127\.0\.0\.1/$host_ip/g" "$CONFIG_FILE"
    fi
    
    bashio::log.info "FRPC configuration file generated successfully: $CONFIG_FILE"
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
    bashio::log.info ""
    bashio::log.info "=========================================="
    bashio::log.info "  设备ID (Device ID): $device_id"
    bashio::log.info "=========================================="
    bashio::log.info ""
}

# =============================================================================
# 主流程
# =============================================================================

# 1. 获取设备ID
DEVICE_ID=$(get_device_id)

# 显示设备信息
display_device_info "$DEVICE_ID"

# 2. 调用登录接口
login "$AUTH_ACCOUNT" "$AUTH_PASSWORD"

# 3. 注册frpc代理并获取配置
register_frpc_proxy "$DEVICE_ID" "$COMPANY_ID" "$USER_ID" "$ACCOUNT"

# 检查 frpc 可执行文件
if [ ! -x "/usr/local/bin/frpc" ]; then
    bashio::exit.nok "FRPC executable not found at /usr/local/bin/frpc"
fi

bashio::log.info "Starting FRPC..."
bashio::log.info "Configuration file: $CONFIG_FILE"
bashio::log.debug "Configuration content:"
cat "$CONFIG_FILE" | bashio::log.debug

# 清理临时目录
cd / || exit 1
rm -rf "$TEMP_DIR"

# 启动 frpc
/usr/local/bin/frpc -c "$CONFIG_FILE" &
FRPC_PID=$!

bashio::log.info "FRPC started with PID: $FRPC_PID"

cleanup() {
    local exit_code=${1:-0}

    bashio::log.info "Stopping FRPC heartbeat and process..."

    if [ -n "${HEARTBEAT_PID:-}" ]; then
        kill "$HEARTBEAT_PID" 2>/dev/null || true
        wait "$HEARTBEAT_PID" 2>/dev/null || true
    fi

    if kill -0 "$FRPC_PID" 2>/dev/null; then
        kill "$FRPC_PID" 2>/dev/null || true
        wait "$FRPC_PID" 2>/dev/null || true
    fi

    if [ -x "$HEARTBEAT_SCRIPT" ]; then
        "$HEARTBEAT_SCRIPT" "$DEVICE_ID" "$COMPANY_ID" "$USER_ID"
    fi

    exit "$exit_code"
}

trap 'cleanup 0' SIGTERM SIGINT

if [ -x "$HEARTBEAT_SCRIPT" ]; then
    bashio::log.info "Starting FRPC heartbeat task (interval ${HEARTBEAT_INTERVAL}s)..."
    (
        while true; do
            "$HEARTBEAT_SCRIPT" "$DEVICE_ID" "$COMPANY_ID" "$USER_ID" "$FRPC_PID" || true
            sleep "$HEARTBEAT_INTERVAL" &
            wait $!
        done
    ) &
    HEARTBEAT_PID=$!
else
    bashio::log.warning "Heartbeat script not found or not executable: $HEARTBEAT_SCRIPT"
fi

wait "$FRPC_PID"
FRPC_EXIT_CODE=$?

bashio::log.info "FRPC process exited with code: $FRPC_EXIT_CODE"

if [ -n "${HEARTBEAT_PID:-}" ]; then
    kill "$HEARTBEAT_PID" 2>/dev/null || true
    wait "$HEARTBEAT_PID" 2>/dev/null || true
fi

# 上报最终一次心跳，标记为未运行
if [ -x "$HEARTBEAT_SCRIPT" ]; then
    "$HEARTBEAT_SCRIPT" "$DEVICE_ID" "$COMPANY_ID" "$USER_ID"
fi

exit "$FRPC_EXIT_CODE"

