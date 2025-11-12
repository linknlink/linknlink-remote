#!/usr/bin/env bashio

# =============================================================================
# 脚本：FRPC 心跳上报
# =============================================================================

set -euo pipefail

LOG_LEVEL="${BASHIO_LOG_LEVEL:-info}"
bashio::log.level "$LOG_LEVEL"

DEVICE_ID="${1:-}"
COMPANY_ID="${2:-}"
USER_ID="${3:-}"
FRPC_PID="${4:-}"

if [ -z "$DEVICE_ID" ]; then
    bashio::log.error "Heartbeat script requires device_id"
    exit 1
fi

# =============================================================================
# 函数：检查 FRPC 是否运行
# =============================================================================
is_frpc_running() {
    local running="false"

    if [ -n "$FRPC_PID" ]; then
        if kill -0 "$FRPC_PID" 2>/dev/null; then
            running="true"
            echo "$running"
            return
        fi
    fi

    if pgrep -x frpc >/dev/null 2>&1; then
        running="true"
    fi

    echo "$running"
}

# =============================================================================
# 主流程：发送心跳
# =============================================================================
send_heartbeat() {
    local server_url="https://euadmin.linklinkiot.com/frpserver/api/heartbeat"
    local running="$(is_frpc_running)"
    local json_data="{\"did\":\"$DEVICE_ID\",\"running\":$running}"

    bashio::log.debug "Heartbeat request payload: $json_data"

    local http_response
    http_response=$(curl -s -w "\n%{http_code}" -X POST \
        -H "Content-Type: application/json" \
        ${COMPANY_ID:+-H "companyid: $COMPANY_ID"} \
        ${USER_ID:+-H "userid: $USER_ID"} \
        -d "$json_data" \
        "$server_url" 2>&1)

    local http_code
    http_code=$(echo "$http_response" | tail -n1)
    local content
    content=$(echo "$http_response" | head -n -1)

    bashio::log.debug "Heartbeat response code: $http_code"
    bashio::log.debug "Heartbeat response body: $content"

    if [ "$http_code" != "200" ]; then
        bashio::log.warning "Heartbeat request failed with HTTP code: $http_code"
        return 1
    fi

    if [[ $content == \{* ]]; then
        local status="0"
        local msg="success"
        if command -v jq >/dev/null 2>&1; then
            status=$(echo "$content" | jq -r '.status // "0"' 2>/dev/null)
            msg=$(echo "$content" | jq -r '.msg // .message // "success"' 2>/dev/null)
        else
            status=$(echo "$content" | grep -o '"status":[^,}]*' | grep -oE '-?[0-9]+' | head -n1 || echo "0")
            msg=$(echo "$content" | sed -n 's/.*"msg"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')
            [ -z "$msg" ] && msg="success"
        fi

        if [ "$status" != "0" ]; then
            bashio::log.warning "Heartbeat responded with status: $status, message: $msg"
            return 1
        fi

        bashio::log.debug "Heartbeat success: $msg"
    fi

    return 0
}

send_heartbeat

