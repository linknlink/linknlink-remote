import requests
import json
import syslog
import hashlib
import base64
import time
from flask import session, request, jsonify, redirect, url_for
from functools import wraps
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend

from config import HADDONS_API_BASE_URL

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
        syslog.syslog(syslog.LOG_ERR, f"AES Decrypt error: {str(e)}")
        return None

# ============= 认证相关函数 =============

def check_ieg_user_info(token):
    """
    调用 HAddons 认证服务检查用户信息
    API: POST /addons/account/getuserinfo
    Security: AES Encrypted Body, Timestamp Header
    """
    try:
        url = f"{HADDONS_API_BASE_URL}/addons/account/getuserinfo"
        
        # 1. Prepare Request Data
        current_timestamp = str(int(time.time()))
        
        # Key = MD5(timestamp + SALT_AES_KEY)
        key_raw = md5_str(current_timestamp + SALT_AES_KEY)
        # AES-128 key must be 16 bytes. MD5 is 32 hex chars (16 bytes raw? No, hex string is 32 bytes).
        # Check Go implementation: `key := utils.MD5(timestamp + utils.SALT_AES_KEY)` -> returns hex string.
        # But `block, err := aes.NewCipher([]byte(key))` in Go: if key is 32 bytes, it selects AES-256. 
        # Wait, account_handler.go:
        # key := utils.MD5(timestamp + utils.SALT_AES_KEY) -> returns string (hex32 chars)
        # aes.NewCipher([]byte(key)) -> len is 32 -> AES-256.
        # My python `algorithms.AES(key)` needs key to be bytes. 
        # If I use hex string as bytes, length is 32 -> AES-256.
        # So I should use the hex string directly as bytes.
        
        key = key_raw.encode('utf-8') 
        
        req_data = {
            "loginsession": token,
            # "userid": "" # Optional? API handler only checks LoginSession for VerifySession
        }
        
        # 2. Encrypt Body
        plaintext = json.dumps(req_data)
        ciphertext = aes_encrypt(plaintext, key, IV)
        
        headers = {
            'Timestamp': current_timestamp,
            'Content-Type': 'application/json' # Although body is raw string, usually ... Flask side reads request.data or request.get_data(). 
            # Go side: `ioutil.ReadAll(c.Request.Body)` treats it as raw bytes.
        }
        
        # 3. Send Request
        # In Go `Login`: bodyBytes -> string -> decrypt. The body IS the ciphertext string.
        response = requests.post(url, data=ciphertext, headers=headers, timeout=5)
        
        if response.status_code == 200:
            # 4. Decrypt Response?
            # Go `GetUserInfo` returns `c.JSON(http.StatusOK, resp)`. 
            # It seems the response is NOT encrypted based on code: `c.JSON(http.StatusOK, resp)` sends plain JSON.
            # Only Request is encrypted?
            # Let's re-read account_handler.go.
            # `c.JSON` writes JSON to response writer. It is NOT encrypted automatically.
            # So response is plain JSON.
            
            data = response.json()
            if data.get('status') == 0:
                # Map response fields to user_info
                # Go response: userid, email, nickname, lid, companyid, country
                return {
                    'userid': data.get('userid'),
                    'email': data.get('email'),
                    'nickname': data.get('nickname'),
                    'lid': data.get('lid'),
                    'companyid': data.get('companyid'),
                    'countrycode': data.get('country')
                }
            else:
                syslog.syslog(syslog.LOG_WARNING, f"GetUserInfo failed: {data.get('msg')}")
    except Exception as e:
        syslog.syslog(syslog.LOG_ERR, f"Check user info error: {str(e)}")
    
    return None

def require_login(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 1. 检查Session中是否有用户信息
        if 'user_info' in session:
            return f(*args, **kwargs)
        
        # 2. 检查Cookie中的token（HAddons通常设置名为 'ingress_session' 或其它，这里假设复用 'token' 或 'loginsession'）
        # HAddons 前端 (Vue) 使用 'loginsession' header 或 cookie?
        # Check `account_handler.go`: `c.GetHeader("X-Login-Session")` or `c.Cookie("loginsession")`.
        # So we should look for 'loginsession' cookie.
        token = request.cookies.get('loginsession')
        if not token:
            # Fallback to 'token' just in case
            token = request.cookies.get('token')
            
        if token:
            user_info = check_ieg_user_info(token)
            if user_info:
                session['user_info'] = user_info
                # Update session token
                session['token'] = token 
                return f(*args, **kwargs)
        
        # 3. 验证失败，返回 401
        return jsonify({'success': False, 'message': '未登录或登录失效', 'code': 401}), 401
        
    return decorated_function
