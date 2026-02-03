#!/bin/bash
# =============================================================================
# frpc Service Management Script - Common Configuration
# Project: iegservicemanager
# Version: 1.0.0
# Description: Common configuration for frpc service management
# =============================================================================

# Service basic information
SERVICE_ID="frpc"
SERVICE_NAME="frpc"

# Base path definitions
# If SCRIPT_DIR is not set, use the directory where common.sh is located
if [[ -z "${SCRIPT_DIR:-}" ]]; then
    # Get the directory where common.sh is located
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
fi

# BASE_DIR is the parent directory of SCRIPT_DIR
BASE_DIR=${BASE_DIR:-"$(dirname "$SCRIPT_DIR")"}
CONFIG_FILE="$BASE_DIR/configuration.yaml"
SERVICEUPDATE_FILE="$BASE_DIR/serviceupdate.json"
SCRIPT_VERSION_FILE="$SCRIPT_DIR/VERSION"

# Data directories
SERVICE_DIR="/etc/$SERVICE_ID"

# MQTT configuration
MQTT_TOPIC_BASE="ieg"

# -----------------------------------------------------------------------------
# 时间相关函数
# -----------------------------------------------------------------------------

# 获取当前时间戳（秒）
function get_timestamp() {
    date +%s
}

# 获取格式化时间字符串
function get_datetime() {
    date '+%F %T'
}

# -----------------------------------------------------------------------------
# 日志相关函数
# -----------------------------------------------------------------------------

# 统一日志记录
function log() {
    local level="${1-INFO}"
    local message="$2"
    local log_file="${3:-$LOG_FILE}"

    if [ -n "$log_file" ]; then
        echo "[$(get_datetime)] $level $message" | tee -a "$log_file"
    else
        echo "[$(get_datetime)] $level $message"
    fi
}

# -----------------------------------------------------------------------------
# MQTT 相关函数
# -----------------------------------------------------------------------------

# 加载 MQTT 配置
function load_mqtt_conf() {
    if [[ -f "$CONFIG_FILE" ]]; then
        MQTT_HOST=$(grep -Po '^[[:space:]]*host:[[:space:]]*\K.*' "$CONFIG_FILE" 2>/dev/null | head -n1 || echo "127.0.0.1")
        MQTT_PORT=$(grep -Po '^[[:space:]]*port:[[:space:]]*\K.*' "$CONFIG_FILE" 2>/dev/null | head -n1 || echo "1883")
        MQTT_USER=$(grep -Po '^[[:space:]]*username:[[:space:]]*\K.*' "$CONFIG_FILE" 2>/dev/null | head -n1 || echo "admin")
        MQTT_PASS=$(grep -Po '^[[:space:]]*password:[[:space:]]*\K.*' "$CONFIG_FILE" 2>/dev/null | head -n1 || echo "admin")
    else
        MQTT_HOST="127.0.0.1"
        MQTT_PORT="1883"
        MQTT_USER="admin"
        MQTT_PASS="admin"
    fi
}

# MQTT 消息发布
function mqtt_report() {
    local topic="$1"
    local payload="$2"

    load_mqtt_conf
    mosquitto_pub -h "$MQTT_HOST" -p "$MQTT_PORT" -u "$MQTT_USER" -P "$MQTT_PASS" -t "$topic" -m "$payload" >/dev/null 2>&1 || true

    log "MQTT" "$topic -> $payload"
}

# -----------------------------------------------------------------------------
# 网络和服务检查函数
# -----------------------------------------------------------------------------

# 检查端口状态
function check_port_status() {
    local port="$1"
    nc -z 127.0.0.1 "$port" >/dev/null 2>&1 && echo "online" || echo "offline"
}

# 确保目录存在
function ensure_directory() {
    local dir="$1"
    mkdir -p "$dir" 2>/dev/null || true
}

# 检查服务是否已安装
function check_service_install() {
    # 在 Docker 环境中，我们检查二进制文件和配置文件
    if [ -x "/usr/local/bin/frpc" ] && [ -d "$SERVICE_DIR" ]; then
        return 0
    else
        return 1
    fi
}

# 检查服务是否运行
function check_service_running() {
    # 改用 pgrep 检查进程，不再依赖 systemctl
    if pgrep -f "frpc -c.*/frpc.toml" >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# 获取服务版本
function get_version() {
    local service="$1"
    if [ -x "/etc/$service/bin/$service" ]; then
        "/etc/$service/bin/$service" --version 2>/dev/null | head -n1 || echo "unknown"
    else
        echo "unknown"
    fi
}

################################################################################

# 获取设备ID函数
function get_device_id() {
    local device_id=""
    
    # 1. 优先从 DATA_DIR (环境变量) 下的 device_id.txt 获取，与 Python 保持一致
    local data_dir="${DATA_DIR:-/data}"
    local dev_id_file="${data_dir}/device_id.txt"
    
    if [ -f "$dev_id_file" ]; then
        device_id=$(cat "$dev_id_file" | tr -d '[:space:]' | tr '[:upper:]' '[:lower:]')
        log "INFO" "Found device ID from $dev_id_file: $device_id"
    fi

    # 2. 回退到原有 ieginfo.json
    if [ -z "$device_id" ]; then
        local ieginfo_file="/etc/iegcloudaccess/ieginfo.json"
        if [ -f "$ieginfo_file" ]; then
            if command -v jq &> /dev/null; then
                device_id=$(jq -r '.did' "$ieginfo_file" 2>/dev/null)
            else
                device_id=$(sed -n 's/.*"did"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' "$ieginfo_file")
            fi
            [ "$device_id" = "null" ] && device_id=""
        fi
    fi

    # 导出变量供后续使用
    export DEVICE_ID="$device_id"
}

# 查询iSG状态、配置相关信息函数
function get_ieg_config_info() {
    local api_url="http://127.0.0.1:22210/iegauth/rpc/remoteuser/info"
    # local api_url="http://192.168.115.184:22201/iegauth/rpc/remoteuser/info"
    local response=""

    # 尝试使用curl或wget发送POST请求获取配置信息
    if command -v curl &> /dev/null; then
        response=$(curl -s -X POST "$api_url")
    elif command -v wget &> /dev/null; then
        response=$(wget -q -O - --post-data="" "$api_url")
    fi

    # 检查响应是否为有效的JSON并包含所需字段
    if [ -n "$response" ]; then
        # 使用jq提取account、userid和cluster字段
        if command -v jq &> /dev/null; then
            # 如果jq可用，使用jq解析JSON
            companyid=$(echo "$response" | jq -r '.data.companyId')
            account=$(echo "$response" | jq -r '.data.account')
            userid=$(echo "$response" | jq -r '.data.userId')
#            cluster=$(echo "$response" | jq -r '.data.cluster')
        else
            # 如果jq不可用，回退到sed解析
            companyid=$(echo "$response" | sed -n 's/.*"companyId"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')
            account=$(echo "$response" | sed -n 's/.*"account"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')
            userid=$(echo "$response" | sed -n 's/.*"userId"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')
#            cluster=$(echo "$response" | sed -n 's/.*"cluster"[[:space:]]*:[[:space:]]*\([0-9]*\).*/\1/p')
        fi

#        # 根据cluster值设置admin_domain
#        if [ "$cluster" -eq 1 ] 2>/dev/null; then
#            admin_domain="euadmin.linklinkiot.com"
#        else
#            admin_domain="admin.linklinkiot.com"
#        fi

        # 导出变量供后续使用
        export REMOTE_COMPANYID="$companyid"
        export REMOTE_ACCOUNT="$account"
        export REMOTE_USERID="$userid"
        export ADMIN_DOMAIN="https://admin.linklinkiot.com"
    fi
}

# 注册代理函数
function register_proxy() {
    # 从JSON文件读取PROXY_JSON配置（优先从$SERVICE_DIR读取，如果不存在则从$SCRIPT_DIR/conf读取）
    local proxy_json_file="${SERVICE_DIR}/register_proxy.json"
    if [ ! -f "$proxy_json_file" ]; then
        # 如果$SERVICE_DIR中不存在，从$SCRIPT_DIR/conf拷贝一份
        if [ -f "${SCRIPT_DIR}/conf/register_proxy.json" ]; then
            cp -f "${SCRIPT_DIR}/conf/register_proxy.json" "$proxy_json_file"
            log "INFO" "Copied register_proxy.json from $SCRIPT_DIR/conf to $SERVICE_DIR"
        else
            echo "Error: register_proxy.json file not found"
            return 1
        fi
    fi

    # 读取JSON文件并格式化为一行
    PROXY_JSON=$(cat "$proxy_json_file" | tr '\n' ' ' | sed 's/ //g')

    # 构造带额外参数的JSON数据
    local companyid="$REMOTE_COMPANYID"
    local userid="$REMOTE_USERID"
    local account="$REMOTE_ACCOUNT"
    local server_url="${ADMIN_DOMAIN}/frpserver/api/proxy"

    JSON_DATA="{\"did\":\"$DEVICE_ID\",\"name\":\"iEG\",\"type\":1,\"account\":\"$account\",\"heartbeat\":1,\"proxyList\":$PROXY_JSON}"

    echo "Sending request to $server_url"
    echo "Request data: $JSON_DATA"

    # 读取环境变量 REGISTER_FORCE，如果为 true 则添加 register_force 请求头
    local register_force="${REGISTER_FORCE:-false}"
    local curl_headers=(
        "-H" "Content-Type: application/json"
        "-H" "companyid: $companyid"
        "-H" "userid: $userid"
    )

    if [ "$register_force" = "true" ]; then
        curl_headers+=("-H" "register-force: true")
        echo "Using register_force: true"
    fi

    # 发送请求并保存响应
    RESPONSE_FILE="response.json"
    HTTP_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST \
        "${curl_headers[@]}" \
        -d "$JSON_DATA" \
        "$server_url")

    HTTP_CODE=$(echo "$HTTP_RESPONSE" | tail -n1)
    CONTENT=$(echo "$HTTP_RESPONSE" | head -n -1)

    # 将响应内容写入文件
    echo "$CONTENT" > "$RESPONSE_FILE"

    # 检查HTTP状态码
    if [ "$HTTP_CODE" != "200" ]; then
        echo "Error: HTTP request failed with code $HTTP_CODE"
        echo "Response: $CONTENT"
        rm -f "$RESPONSE_FILE"
        return 1
    fi

    # 检查响应是否为JSON格式的错误信息
    if [[ $CONTENT == \{* ]]; then
        # 可能是JSON格式的错误响应
        STATUS=$(echo "$CONTENT" | jq -r '.status' 2>/dev/null)

        # 如果status字段存在且不为0，则是错误响应
        if [ "$STATUS" != "null" ] && [ "$STATUS" != "0" ]; then
            MSG=$(echo "$CONTENT" | jq -r '.msg' 2>/dev/null)
            echo "Error: Registration failed"
            echo "Status: $STATUS"
            echo "Message: $MSG"
            rm -f "$RESPONSE_FILE"
            return 1
        fi

        # 如果是成功状态，则继续处理
        if [ "$STATUS" == "0" ]; then
            echo "Error: Unexpected JSON response with success status but not file content"
            rm -f "$RESPONSE_FILE"
            return 1
        fi
    fi

    # 将响应保存为配置文件
    echo "$CONTENT" > "frpc.toml"
    echo "Success: Configuration file downloaded as frpc.toml"

    rm -f "$RESPONSE_FILE"
    return 0
}

# 注册frpc代理配置
function register_frpc_proxy() {
    # 获取设备ID
    get_device_id

    # 检查设备ID
    if [ -z "$DEVICE_ID" ]; then
        log "ERROR" "Device ID is required, failed to get device id from any source"
        return 1
    fi

    # 获取iEG配置信息
    get_ieg_config_info

    # 检查是否成功获取到userid和account
    if [ -z "$REMOTE_COMPANYID" ] ||  [ -z "$REMOTE_USERID" ] || [ -z "$REMOTE_ACCOUNT" ]; then
        log "ERROR" "Failed to get companyid or userid or account from iSG config info"
        return 1
    fi

    # 将companyid、account和userid以JSON形式写入ieg_user_info文件（保存到SERVICE_DIR）
    echo "{\"companyid\":\"$REMOTE_COMPANYID\",\"account\":\"$REMOTE_ACCOUNT\",\"userid\":\"$REMOTE_USERID\"}" > "${SERVICE_DIR}/ieg_user_info"

    # 切换到SCRIPT_DIR执行注册（register_proxy函数会从SERVICE_DIR读取配置）
    local old_dir=$(pwd)
    cd "$SCRIPT_DIR" || return 1

    # 调用注册函数
    if ! register_proxy; then
        cd "$old_dir" || true
        return 1
    fi

    # 将生成的配置文件拷贝到SERVICE_DIR
    if [ -f "frpc.toml" ]; then
        # 先删除旧文件，确保新文件能够成功覆盖
        if [ -f "${SERVICE_DIR}/frpc.toml" ]; then
            rm -f "${SERVICE_DIR}/frpc.toml"
        fi
        # 拷贝新文件
        cp -v frpc.toml "${SERVICE_DIR}/"
        # 验证文件是否成功拷贝
        if [ -f "${SERVICE_DIR}/frpc.toml" ]; then
            log "INFO" "配置文件已成功更新到 ${SERVICE_DIR}/frpc.toml"
        else
            log "ERROR" "配置文件拷贝失败"
            return 1
        fi
    else
        log "ERROR" "frpc.toml文件不存在，无法拷贝"
        return 1
    fi

    cd "$old_dir" || true
    return 0
}

# 临时代理注册函数（使用register_proxy_tmp.json）
function register_tmp_frpc_proxy() {
    # 获取设备ID
    get_device_id

    # 检查设备ID
    if [ -z "$DEVICE_ID" ]; then
        log "ERROR" "Device ID is required, failed to get device id from any source"
        return 1
    fi

    # 获取iSG配置信息
    get_ieg_config_info

    # 检查是否成功获取到companyid、userid和account
    if [ -z "$REMOTE_COMPANYID" ] ||  [ -z "$REMOTE_USERID" ] || [ -z "$REMOTE_ACCOUNT" ]; then
        log "ERROR" "Failed to get companyid or userid or account from iSG config info"
        return 1
    fi

    # 从JSON文件读取PROXY_JSON配置（从$SERVICE_DIR读取）
    local proxy_json_file="${SERVICE_DIR}/register_proxy_tmp.json"
    if [ ! -f "$proxy_json_file" ]; then
        # 如果$SERVICE_DIR中不存在，从$SCRIPT_DIR/conf拷贝一份
        if [ -f "${SCRIPT_DIR}/conf/register_proxy_tmp.json" ]; then
            cp -f "${SCRIPT_DIR}/conf/register_proxy_tmp.json" "$proxy_json_file"
            log "INFO" "Copied register_proxy_tmp.json from $SCRIPT_DIR/conf to $SERVICE_DIR"
        else
            log "ERROR" "register_proxy_tmp.json file not found"
            return 1
        fi
    fi

    # 读取JSON文件并格式化为一行
    PROXY_JSON=$(cat "$proxy_json_file" | tr '\n' ' ' | sed 's/ //g')

    # 构造带额外参数的JSON数据（临时代理注册不需要heartbeat字段）
    local companyid="$REMOTE_COMPANYID"
    local userid="$REMOTE_USERID"
    local account="$REMOTE_ACCOUNT"
    local server_url="${ADMIN_DOMAIN}/frpserver/api/tmp-proxy"

    JSON_DATA="{\"did\":\"$DEVICE_ID\",\"name\":\"iEG\",\"type\":1,\"account\":\"$account\",\"proxyList\":$PROXY_JSON}"

    echo "Sending request to $server_url"
    echo "Request data: $JSON_DATA"

    # 切换到SCRIPT_DIR执行
    local old_dir=$(pwd)
    cd "$SCRIPT_DIR" || return 1

    # 发送请求并保存响应（使用 -D 选项保存响应头到文件）
    RESPONSE_FILE="response.json"
    HEADER_FILE="response_headers.txt"
    
    # 使用 -D 选项将响应头保存到文件，-o 选项将响应体保存到文件
    HTTP_CODE=$(curl -s --connect-timeout 10 --max-time 30 -w "%{http_code}" -o "$RESPONSE_FILE" -D "$HEADER_FILE" -X POST \
        -H "Content-Type: application/json" \
        -H "companyid: $companyid" \
        -H "userid: $userid" \
        -d "$JSON_DATA" \
        "$server_url")
    
    # 读取响应体
    CONTENT=$(cat "$RESPONSE_FILE" 2>/dev/null || echo "")

    # 从响应头文件中提取 X-Visitor-Code
    VISITOR_CODE=$(grep -i "^X-Visitor-Code:" "$HEADER_FILE" 2>/dev/null | sed 's/^[^:]*:[[:space:]]*//' | tr -d '\r\n' || echo "")

    # 检查HTTP状态码
    if [ "$HTTP_CODE" != "200" ]; then
        echo "Error: HTTP request failed with code $HTTP_CODE"
        echo "Response: $CONTENT"
        rm -f "$RESPONSE_FILE" "$HEADER_FILE"
        cd "$old_dir" || true
        return 1
    fi

    # 检查响应是否为JSON格式的错误信息
    if [[ $CONTENT == \{* ]]; then
        # 可能是JSON格式的错误响应
        STATUS=$(echo "$CONTENT" | jq -r '.status' 2>/dev/null)

        # 如果status字段存在且不为0，则是错误响应
        if [ "$STATUS" != "null" ] && [ "$STATUS" != "0" ]; then
            MSG=$(echo "$CONTENT" | jq -r '.msg' 2>/dev/null)
            echo "Error: Registration failed"
            echo "Status: $STATUS"
            echo "Message: $MSG"
            rm -f "$RESPONSE_FILE" "$HEADER_FILE"
            cd "$old_dir" || true
            return 1
        fi

        # 如果是成功状态，则继续处理
        if [ "$STATUS" == "0" ]; then
            echo "Error: Unexpected JSON response with success status but not file content"
            rm -f "$RESPONSE_FILE" "$HEADER_FILE"
            cd "$old_dir" || true
            return 1
        fi
    fi

    # 将响应保存为配置文件
    echo "$CONTENT" > "frpc_tmp.toml"
    echo "Success: Configuration file downloaded as frpc_tmp.toml"
    
    # 保存访客码到文件
    if [ -n "$VISITOR_CODE" ]; then
        echo "$VISITOR_CODE" > "${SERVICE_DIR}/visitor_code"
        export VISITOR_CODE
        echo "Visitor Code: $VISITOR_CODE"
        log "INFO" "Visitor code saved to ${SERVICE_DIR}/visitor_code"
    else
        export VISITOR_CODE=""
        echo "Warning: No visitor code found in response headers"
    fi

    # 将生成的配置文件拷贝到SERVICE_DIR
    if [ -f "frpc_tmp.toml" ]; then
        cp -v frpc_tmp.toml "${SERVICE_DIR}/"
    fi

    rm -f "$RESPONSE_FILE" "$HEADER_FILE"
    cd "$old_dir" || true
    return 0
}