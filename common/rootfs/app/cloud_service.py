import logging
import requests
import time
import os
import json
import config
from device import get_device_id

logger = logging.getLogger(__name__)



def register_proxy_to_cloud(proxy_list, is_tmp=False, force=False):
    """
    向云端注册 frp 代理
    """
    try:
        from ieg_auth import get_current_user_info
        from device import get_device_id
        
        user_info = get_current_user_info()
        if not isinstance(user_info, dict) or not user_info.get('userid'):
            logger.error("Cloud registration aborted: userid not available (not logged in)")
            return None, "user not logged in"

        # 根据集群地区切换云端服务地址
        cluster = user_info.get('cluster', 'oversea')
        config.update_cloud_urls(cluster)
        device_id = get_device_id()
        
        url = config.TMP_PROXY_API_URL if is_tmp else config.PROXY_API_URL
        
        # 构造请求数据
        payload = {
            "did": device_id,
            "name": "iSG-Linux",
            "type": 0,
            "account": user_info.get('email') or user_info.get('phone') or '',
            "proxyList": proxy_list
        }
        
        if not is_tmp:
            payload["heartbeat"] = 1

        # 构造头部（companyid、userid 为必传字段）
        headers = {
            "Content-Type": "application/json",
            "companyid": str(user_info.get('companyid') or '1dda5816c83d32da73e209540ecbedaf'),
            "userid": str(user_info['userid'])
        }
        
        if force:
            headers["register-force"] = "true"

        logger.info(f"Outbound Request: POST {url}, Payload: {json.dumps(payload)}")
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        logger.info(f"Outbound Response: POST {url}, Status: {response.status_code}")
        
        if response.status_code == 200:
            # 检查是否是 JSON 错误响应
            try:
                data = response.json()
                status = data.get('status')
                if status is not None and str(status) != "0":
                    msg = data.get('msg') or data.get('message')
                    logger.error(f"Cloud registration failed (API logic): {msg}")
                    return None, msg
            except ValueError:
                # 不是 JSON，说明返回的是 toml 配置文件内容
                pass
            
            # 获取配置文件内容
            config_content = response.text
            
            # 尝试从响应头获取 Visitor Code (针对临时代理)
            visitor_code = response.headers.get('X-Visitor-Code', '')
            
            return config_content, visitor_code
        else:
            logger.error(f"Cloud registration failed with HTTP {response.status_code}")
            return None, f"HTTP {response.status_code}"
            
    except Exception as e:
        logger.error(f"Cloud registration exception: {str(e)}")
        return None, str(e)

def send_heartbeat():
    """发送心跳到云端"""
    from ieg_auth import get_current_user_info
    from device import get_device_id
    from frpc_service import check_frpc_running
    
    user_info = get_current_user_info()
    if not isinstance(user_info, dict) or not user_info.get('userid'):
        return False
        
    try:
        device_id = get_device_id()
    except Exception as e:
        return False
        
    # 根据集群地区切换云端服务地址以防配置漂移
    cluster = user_info.get('cluster', 'oversea')
    config.update_cloud_urls(cluster)
        
    frpc_running = check_frpc_running()
    
    payload = {
        'did': device_id,
        'running': frpc_running
    }
    
    # companyid、userid 为必传字段
    headers = {
        'companyid': str(user_info.get('companyid') or '1dda5816c83d32da73e209540ecbedaf'),
        'userid': str(user_info['userid'])
    }
        
    try:
        # 心跳请求非常频繁，我们仅在失败时记录详细信息，成功时仅记录一次简单汇总
        response = requests.post(config.HEARTBEAT_API_URL, json=payload, headers=headers, timeout=10)
        if response.status_code != 200:
             logger.warning(f"Outbound Heartbeat Response failed: POST {config.HEARTBEAT_API_URL}, Status: {response.status_code}")
             return False
        return True
    except Exception as e:
        # 心跳失败不打印过多日志，避免刷屏，仅调试时关注
        return False

def heartbeat_loop():
    """后台心跳线程"""
    logger.info("Starting heartbeat loop...")
    
    # 循环
    while True:
        try:
            # 发送心跳 (内部实时获取状态，未获取到会静默放弃当前心跳)
            send_heartbeat()
        except Exception as e:
            logger.error(f"Heartbeat loop error: {e}")
        
        time.sleep(30)
