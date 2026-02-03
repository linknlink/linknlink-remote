import requests
import json
import syslog
from flask import session, request, jsonify, redirect, url_for
from functools import wraps

from config import IEG_AUTH_BASE_URL
from utils import enc_password

# ============= 登录和认证相关函数 =============

def check_ieg_user_info(token):
    """
    调用iEG认证服务检查用户信息
    """
    try:
        url = f"{IEG_AUTH_BASE_URL}/server/auth/getuserinfo"
        headers = {'token': token}
        
        # 允许失败，超时时间设置短一点
        response = requests.get(url, headers=headers, timeout=2)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 0:
                return data.get('data')
    except Exception as e:
        syslog.syslog(syslog.LOG_ERR, f"Check user info error: {str(e)}")
    
    return None

def login_to_ieg(username, password):
    """
    调用iEG认证服务进行登录
    注意：这里假设iEG认证服务接受明文或特定格式的密码，
    根据原逻辑，我们对密码进行了SHA1+Salt加密
    """
    try:
        url = f"{IEG_AUTH_BASE_URL}/server/auth/login"
        
        # 加密密码
        encrypted_password = enc_password(password)
        
        data = {
            'username': username,
            'password': encrypted_password
        }
        
        response = requests.post(url, json=data, timeout=5)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('status') == 0:
                return result.get('data', {}).get('token')
            else:
                syslog.syslog(syslog.LOG_WARNING, f"Login failed: {result.get('msg')}")
    except Exception as e:
        syslog.syslog(syslog.LOG_ERR, f"Login exception: {str(e)}")
    
    return None

def require_login(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 1. 检查Session中是否有用户信息
        if 'user_info' in session:
            return f(*args, **kwargs)
        
        # 2. 检查Cookie中的token（iEG兼容）
        token = request.cookies.get('token')
        if token:
            user_info = check_ieg_user_info(token)
            if user_info:
                session['user_info'] = user_info
                return f(*args, **kwargs)
        
        # 3. 如果是已登录状态但Session过期，尝试使用Session中的token
        if 'token' in session:
            user_info = check_ieg_user_info(session['token'])
            if user_info:
                session['user_info'] = user_info
                return f(*args, **kwargs)
            else:
                # token失效，清除session
                session.pop('token', None)

        # 4. 判断请求类型，如果是API请求返回JSON，否则重定向
        if request.path.startswith('/api/'):
            return jsonify({'success': False, 'message': '未登录', 'code': 401}), 401
        
        return redirect(url_for('login_page'))
    return decorated_function
