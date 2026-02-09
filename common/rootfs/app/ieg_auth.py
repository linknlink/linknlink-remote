import requests
import json
import logging
import hashlib
import base64
import time
from flask import session, request, jsonify, redirect, url_for
from functools import wraps
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend

from config import HADDONS_API_BASE_URL

logger = logging.getLogger(__name__)

# ============= Crypto Constants =============
IV = b"0123456789abcdef"
SALT_AES_KEY = "kdixkdqp54545^#*"

# ============= Crypto Functions =============

def md5_str(text):
    m = hashlib.md5()
    m.update(text.encode('utf-8'))
    return m.hexdigest()

def aes_encrypt(plaintext, key, iv):
    """
    AES-128-CBC Encrypt
    Padding: PKCS7
    Output: Base64 String
    """
    if isinstance(key, str):
        key = key.encode('utf-8')
    if isinstance(iv, str):
        iv = iv.encode('utf-8')
    if isinstance(plaintext, str):
        plaintext = plaintext.encode('utf-8')

    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(plaintext) + padder.finalize()

    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(padded_data) + encryptor.finalize()

    return base64.b64encode(ciphertext).decode('utf-8')

def aes_decrypt(ciphertext_b64, key, iv):
    """
    AES-128-CBC Decrypt
    Input: Base64 String
    Padding: PKCS7
    """
    try:
        if isinstance(key, str):
            key = key.encode('utf-8')
        if isinstance(iv, str):
            iv = iv.encode('utf-8')

        ciphertext = base64.b64decode(ciphertext_b64)

        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()

        unpadder = padding.PKCS7(128).unpadder()
        plaintext = unpadder.update(padded_plaintext) + unpadder.finalize()

        return plaintext.decode('utf-8')
    except Exception as e:
        logger.error(f"AES Decrypt error: {str(e)}")
        return None

# ============= 认证相关函数 =============

def get_current_user_info():
    """
    通过 HAddons 的 info 接口获取当前活跃用户信息
    API: GET /addons/account/info (局域网公开接口)
    """
    try:
        url = f"{HADDONS_API_BASE_URL}/addons/account/info"
        
        logger.info(f"Outbound Request: GET {url}")
        response = requests.get(url, timeout=5)
        logger.info(f"Outbound Response: GET {url}, Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 0:
                user_data = data.get('data', {})
                # syslog.syslog(syslog.LOG_INFO, f"Get user info success: {user_data.get('nickname')}")
                return {
                    'userid': user_data.get('userid'),
                    'email': user_data.get('email'),
                    'nickname': user_data.get('nickname'),
                    'lid': user_data.get('lid'),
                    'companyid': user_data.get('companyid'),
                    'countrycode': user_data.get('country')
                }
            else:
                msg = data.get('msg', 'Failed to get user info')
                logger.warning(f"Get active user failed: {msg}")
                return msg
        else:
            logger.warning(f"GetUserInfo API returned HTTP {response.status_code}")
            return f"HTTP {response.status_code}"
    except Exception as e:
        logger.error(f"Get current user info error: {str(e)}")
        return str(e)
    
    return None

def require_login(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 1. 尝试填充用户信息（如果 Session 中还没有）
        if 'user_info' not in session:
            user_result = get_current_user_info()
            if isinstance(user_result, dict):
                session['user_info'] = user_result
            # 注意：这里不再返回 401，即使 user_result 不是 dict 也会继续
            # 因为“本地接口不需要session了”
        
        return f(*args, **kwargs)
        
    return decorated_function
