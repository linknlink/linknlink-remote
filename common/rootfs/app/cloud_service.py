import logging
import requests
import time
import os
import json
import config
from device import get_device_id

logger = logging.getLogger(__name__)


# 全局变量存储云端认证信息
CLOUD_AUTH_INFO = {
    'company_id': None,
    'user_id': None,
    'device_id': None,
    'account': None
}

def register_proxy_to_cloud(proxy_list, is_tmp=False, force=False):
    """
    向云端注册 frp 代理
    """
    try:
        # userid 为必传字段，拿不到直接报错
        if not CLOUD_AUTH_INFO.get('user_id'):
            logger.error("Cloud registration aborted: userid not available")
            return None, "userid not available"

        from device import get_device_id
        device_id = get_device_id()
        
        url = config.TMP_PROXY_API_URL if is_tmp else config.PROXY_API_URL
        
        # 构造请求数据
        payload = {
            "did": device_id,
            "name": "iSG-Linux",
            "type": 0,
            "account": CLOUD_AUTH_INFO.get('account', ''),
            "proxyList": proxy_list
        }
        
        if not is_tmp:
            payload["heartbeat"] = 1

        # 构造头部（companyid、userid 为必传字段）
        headers = {
            "Content-Type": "application/json",
            "companyid": str(CLOUD_AUTH_INFO.get('company_id') or '1dda5816c83d32da73e209540ecbedaf'),
            "userid": str(CLOUD_AUTH_INFO['user_id'])
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
    if not CLOUD_AUTH_INFO.get('device_id'):
        return False
    if not CLOUD_AUTH_INFO.get('user_id'):
        return False
        
    # 检查frpc是否运行
    from frpc_service import check_frpc_running
    frpc_running = check_frpc_running()
    
    payload = {
        'did': CLOUD_AUTH_INFO['device_id'],
        'running': frpc_running
    }
    
    # companyid、userid 为必传字段
    headers = {
        'companyid': str(CLOUD_AUTH_INFO.get('company_id') or '1dda5816c83d32da73e209540ecbedaf'),
        'userid': str(CLOUD_AUTH_INFO['user_id'])
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
    
    # 获取 Device ID
    CLOUD_AUTH_INFO['device_id'] = get_device_id()
    
    # 循环
    while True:
        try:
            # 如果没有认证信息，尝试从本地 ieg_auth 获取
            if not CLOUD_AUTH_INFO['user_id']:
                from ieg_auth import get_current_user_info
                user_info = get_current_user_info()
                
                if isinstance(user_info, dict) and user_info.get('userid'):
                     CLOUD_AUTH_INFO['company_id'] = user_info.get('companyid')
                     CLOUD_AUTH_INFO['user_id'] = user_info.get('userid')
                     CLOUD_AUTH_INFO['account'] = user_info.get('email')
                     # 根据集群地区切换云端服务地址
                     cluster = user_info.get('cluster', 'oversea')
                     config.update_cloud_urls(cluster)
                     logger.info(f"Obtained auth info from local iEG service. UserID: {user_info.get('userid')}, Cluster: {cluster}")
                else:
                    # 获取失败，等待一段时间重试
                    time.sleep(5)
                    continue
            
            # 发送心跳
            send_heartbeat()
            
        except Exception as e:
            logger.error(f"Heartbeat loop error: {e}")
        
        time.sleep(30)
