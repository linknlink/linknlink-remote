#!/bin/bash

# =============================================================================
# 脚本：FRPC 心跳上报
# =============================================================================

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

log_debug() {
    if [ "${LOG_LEVEL:-info}" = "debug" ] || [ "${LOG_LEVEL:-info}" = "trace" ]; then
        log "DEBUG" "$@"
    fi
}

LOG_LEVEL="${LOG_LEVEL:-info}"

DEVICE_ID="${1:-}"
COMPANY_ID="${2:-}"
USER_ID="${3:-}"
FRPC_PID="${4:-}"

if [ -z "$DEVICE_ID" ]; then
    log_warn "Heartbeat script requires device_id"
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

    log_debug "Heartbeat request payload: $json_data"

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

    log_debug "Heartbeat response code: $http_code"
    log_debug "Heartbeat response body: $content"

    if [ "$http_code" != "200" ]; then
        log_warn "Heartbeat request failed with HTTP code: $http_code"
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
            log_warn "Heartbeat responded with status: $status, message: $msg"
            return 1
        fi
    fi

    return 0
}

send_heartbeat
