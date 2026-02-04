import syslog
import requests
import time
import os
from config import CLOUD_API_BASE_URL, HEARTBEAT_API_URL, AUTH_EMAIL, AUTH_PASSWORD
from utils import enc_password
from device import get_device_id


# 全局变量存储云端认证信息
CLOUD_AUTH_INFO = {
    'company_id': None,
    'user_id': None,
    'device_id': None,
    'account': None
}

def cloud_login(email, password):
    """
    调用云端登录接口获取companyid和userid
    """
    try:
        api_url = f"{CLOUD_API_BASE_URL}/user/pwdlogin"
        encrypted_password = enc_password(password)
        
        payload = {
            'email': email,
            'password': encrypted_password
        }
        
        response = requests.post(api_url, json=payload, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            status = data.get('status')
            
            if status == 0 or status == "0":
                info = data.get('info', {})
                company_id = info.get('companyid')
                user_id = info.get('userid')
                
                if company_id and user_id:
                    CLOUD_AUTH_INFO['company_id'] = company_id
                    CLOUD_AUTH_INFO['user_id'] = user_id
                    CLOUD_AUTH_INFO['account'] = email
                    syslog.syslog(syslog.LOG_INFO, f"Cloud login successful. UserID: {user_id}")
                    return True
                else:
                    syslog.syslog(syslog.LOG_ERR, "Cloud login response missing companyid or userid")
            else:
                msg = data.get('msg') or data.get('message')
                syslog.syslog(syslog.LOG_ERR, f"Cloud login failed: {msg} (status: {status})")
        else:
            syslog.syslog(syslog.LOG_ERR, f"Cloud login failed with HTTP {response.status_code}")
            
    except Exception as e:
        syslog.syslog(syslog.LOG_ERR, f"Cloud login exception: {str(e)}")
    
    return False

def send_heartbeat():
    """发送心跳到云端"""
    if not CLOUD_AUTH_INFO['device_id']:
        return False
        
    # 检查frpc是否运行
    from frpc_service import check_frpc_running
    frpc_running = check_frpc_running()
    
    payload = {
        'did': CLOUD_AUTH_INFO['device_id'],
        'running': frpc_running
    }
    
    headers = {}
    if CLOUD_AUTH_INFO['company_id']:
        headers['companyid'] = str(CLOUD_AUTH_INFO['company_id'])
    if CLOUD_AUTH_INFO['user_id']:
        headers['userid'] = str(CLOUD_AUTH_INFO['user_id'])
        
    try:
        response = requests.post(HEARTBEAT_API_URL, json=payload, headers=headers, timeout=10)
        if response.status_code != 200:
             syslog.syslog(syslog.LOG_WARNING, f"Heartbeat failed: HTTP {response.status_code}")
             return False
        return True
    except Exception as e:
        # 心跳失败不打印过多日志，避免刷屏，仅调试时关注
        return False

def heartbeat_loop():
    """后台心跳线程"""
    syslog.syslog(syslog.LOG_INFO, "Starting heartbeat loop...")
    
    # Initial Login
    email = AUTH_EMAIL
    password = AUTH_PASSWORD
    
    if not email or not password:
        syslog.syslog(syslog.LOG_ERR, "AUTH_EMAIL or AUTH_PASSWORD not set, heartbeat disabled")
        return

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
                     syslog.syslog(syslog.LOG_INFO, f"Obtained auth info from local iEG service. UserID: {user_info.get('userid')}")
                else:
                    # 获取失败，等待一段时间重试
                    # syslog.syslog(syslog.LOG_WARNING, "Failed to get auth info from local iEG service, retrying...")
                    time.sleep(60)
                    continue
            
            # 发送心跳
            send_heartbeat()
            
        except Exception as e:
            syslog.syslog(syslog.LOG_ERR, f"Heartbeat loop error: {e}")
        
        time.sleep(30)
