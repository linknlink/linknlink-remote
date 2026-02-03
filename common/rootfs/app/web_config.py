#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LinknLink Remote Web Configuration Service
提供Web界面用于配置register_proxy.json和register_proxy_tmp.json
"""

import os
import json
import subprocess
import shutil
import syslog
import time
import hashlib
import requests
from flask import Flask, render_template, request, jsonify, session
from pathlib import Path
from functools import wraps
from datetime import timedelta

# 配置路径（必须在Flask应用初始化之前定义）
# web_config.py 在 $BASE_DIR/frpc/script/web_config.py，所以上上级目录是 BASE_DIR
_script_file = Path(__file__).resolve()
BASE_DIR = _script_file.parent.parent.parent
SCRIPT_DIR = BASE_DIR / "frpc"
SERVICE_DIR = Path("/etc/frpc")
REMOTE_ASSISTANCE_FILE = SERVICE_DIR / "remote_assistance"
VISITOR_CODE_FILE = SERVICE_DIR / "visitor_code"

# Flask默认会在应用文件所在目录查找templates目录
# 使用相对于脚本文件的路径查找templates目录
# web_config.py 在 $SCRIPT_DIR/script/web_config.py，templates 在 $SCRIPT_DIR/script/templates
_templates_dir = _script_file.parent / 'templates'
app = Flask(__name__, template_folder=str(_templates_dir))

# 设置session密钥和配置
app.secret_key = os.urandom(24)
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)  # session有效期2小时
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# iEG认证服务地址
IEG_AUTH_BASE_URL = "http://127.0.0.1:22210"

# ============= 登录和认证相关函数 =============

def enc_password(password):
    """
    加密密码（与iegauth项目中的blaccount.EncPassword保持一致）
    加密方法：SHA1(password + "4969fj#k23#")
    """
    # 密码 + 固定盐值
    data = password + "4969fj#k23#"
    # SHA1哈希并转换为十六进制字符串
    sha1_hash = hashlib.sha1(data.encode('utf-8')).hexdigest()
    return sha1_hash

def check_ieg_user_info():
    """
    检查是否能获取到iEG用户信息
    调用common.sh中的get_ieg_config_info逻辑
    返回: (success, account, userid, companyid)
    """
    try:
        api_url = f"{IEG_AUTH_BASE_URL}/iegauth/rpc/remoteuser/info"
        response = requests.post(api_url, timeout=5)
        
        # 输出响应body日志
        try:
            response_body = response.text
            syslog.syslog(syslog.LOG_INFO, f"获取用户信息接口响应: HTTP {response.status_code}, Body: {response_body}")
        except Exception as log_err:
            syslog.syslog(syslog.LOG_WARNING, f"记录响应日志失败: {str(log_err)}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 0 and 'data' in data:
                user_data = data['data']
                account = user_data.get('account', '')
                userid = user_data.get('userId', '')
                companyid = user_data.get('companyId', '')
                
                if account and userid:
                    return True, account, userid, companyid
        
        return False, None, None, None
    except Exception as e:
        syslog.syslog(syslog.LOG_ERR, f"检查iEG用户信息失败: {str(e)}")
        return False, None, None, None

def login_to_ieg(account, password):
    """
    调用iEG登录接口
    返回: (success, message)
    """
    try:
        api_url = f"{IEG_AUTH_BASE_URL}/iegauth/api/remoteuser/login"
        
        # 加密密码（使用与blaccount.EncPassword相同的加密方法）
        encrypted_password = enc_password(password)
        
        payload = {
            'account': account,
            'password': encrypted_password
        }
        
        headers = {
            'xkey': 'linklink666'
        }
        
        response = requests.post(api_url, json=payload, headers=headers, timeout=10)
        
        # 输出响应body日志
        try:
            response_body = response.text
            syslog.syslog(syslog.LOG_INFO, f"登录接口响应: HTTP {response.status_code}, Body: {response_body}")
        except Exception as log_err:
            syslog.syslog(syslog.LOG_WARNING, f"记录响应日志失败: {str(log_err)}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 0:
                return True, "登录成功"
            else:
                return False, data.get('msg', '登录失败')
        else:
            return False, f"登录请求失败: HTTP {response.status_code}"
    except Exception as e:
        syslog.syslog(syslog.LOG_ERR, f"登录失败: {str(e)}")
        return False, f"登录异常: {str(e)}"

def logout_from_ieg():
    """
    调用iEG登出接口
    返回: (success, message)
    """
    try:
        api_url = f"{IEG_AUTH_BASE_URL}/iegauth/api/remoteuser/logout"
        
        headers = {
            'xkey': 'linklink666'
        }
        
        syslog.syslog(syslog.LOG_INFO, f"开始调用iEG登出接口: {api_url}")
        
        response = requests.post(api_url, headers=headers, timeout=10)
        
        # 输出响应body日志
        response_body = response.text
        syslog.syslog(syslog.LOG_INFO, f"登出接口响应: HTTP {response.status_code}, Body: {response_body}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                if data.get('status') == 0:
                    syslog.syslog(syslog.LOG_INFO, "iEG登出接口调用成功")
                    return True, "登出成功"
                else:
                    error_msg = data.get('msg', '登出失败')
                    syslog.syslog(syslog.LOG_WARNING, f"iEG登出接口返回失败: {error_msg}")
                    return False, error_msg
            except ValueError as json_err:
                # JSON解析失败
                syslog.syslog(syslog.LOG_ERR, f"登出接口响应JSON解析失败: {str(json_err)}, Body: {response_body}")
                return False, f"响应解析失败: {str(json_err)}"
        else:
            syslog.syslog(syslog.LOG_ERR, f"登出请求失败: HTTP {response.status_code}, Body: {response_body}")
            return False, f"登出请求失败: HTTP {response.status_code}"
    except requests.exceptions.RequestException as req_err:
        syslog.syslog(syslog.LOG_ERR, f"登出请求异常: {str(req_err)}")
        return False, f"登出请求异常: {str(req_err)}"
    except Exception as e:
        syslog.syslog(syslog.LOG_ERR, f"登出失败: {str(e)}")
        return False, f"登出异常: {str(e)}"

def require_login(f):
    """装饰器：要求登录才能访问"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 检查session中是否有登录标记
        if not session.get('logged_in'):
            return jsonify({'success': False, 'message': '未登录', 'needLogin': True}), 401
        
        # 检查iEG用户信息是否仍然有效
        success, account, userid, companyid = check_ieg_user_info()
        if not success:
            session.clear()
            return jsonify({'success': False, 'message': '登录已过期，请重新登录', 'needLogin': True}), 401
        
        # 更新session中的用户信息
        session['account'] = account
        session['userid'] = userid
        session['companyid'] = companyid
        
        return f(*args, **kwargs)
    return decorated_function

# ============= 原有的辅助函数 =============

def generate_bind_port(local_port, prefix):
    """
    根据localPort生成bindPort
    规则：
    1. localPort 范围 1000～9999：加前缀（文件1用3，文件2用4）
    2. localPort < 1000：加前缀且中间补0凑成5位（例如：802 -> 30802, 22 -> 30022）
    3. localPort >= 10000：返回空字符串，使用随机端口
    """
    local_port = int(local_port)
    
    # 如果 localPort >= 10000，使用随机端口
    if local_port >= 10000:
        return None
    
    # 如果 localPort < 1000，加前缀且中间补0凑成5位
    if local_port < 1000:
        port_str = str(local_port)
        port_len = len(port_str)
        zeros_needed = 4 - port_len
        padded_port = "0" * zeros_needed + port_str
        return int(f"{prefix}{padded_port}")
    
    # localPort 范围 1000～9999：加前缀
    if 1000 <= local_port <= 9999:
        return int(f"{prefix}{local_port}")
    
    # 其他情况返回None，使用随机端口
    return None

def get_link_value(local_port):
    """根据localPort判断link值，除22端口是false外，其它都为true"""
    return local_port != 22

def ensure_config_file(config_file, default_file):
    """确保配置文件存在，如果不存在则从默认文件拷贝"""
    if not config_file.exists():
        if default_file.exists():
            shutil.copy2(default_file, config_file)
            return True
        else:
            return False
    return True

def load_config(config_file, default_file):
    """加载配置文件，如果不存在则从默认文件拷贝"""
    if not ensure_config_file(config_file, default_file):
        return []
    
    if config_file.exists():
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    else:
        return []

def save_config(config_file, data):
    """保存配置文件"""
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def load_remote_assistance():
    """加载RemoteAssistance配置，默认false"""
    if REMOTE_ASSISTANCE_FILE.exists():
        with open(REMOTE_ASSISTANCE_FILE, 'r', encoding='utf-8') as f:
            value = f.read().strip().lower()
            return value == 'true'
    return False

def load_visitor_code():
    """加载访客码"""
    if VISITOR_CODE_FILE.exists():
        with open(VISITOR_CODE_FILE, 'r', encoding='utf-8') as f:
            return f.read().strip()
    return ""

def save_visitor_code(code):
    """保存访客码"""
    if code:
        with open(VISITOR_CODE_FILE, 'w', encoding='utf-8') as f:
            f.write(code)
    elif VISITOR_CODE_FILE.exists():
        VISITOR_CODE_FILE.unlink()

def save_remote_assistance(value):
    """保存RemoteAssistance配置"""
    with open(REMOTE_ASSISTANCE_FILE, 'w', encoding='utf-8') as f:
        f.write('true' if value else 'false')

def compare_json_content(json1, json2):
    """比较两个JSON内容是否相同（忽略格式差异）"""
    try:
        # 规范化JSON后比较
        normalized1 = json.dumps(json1, sort_keys=True)
        normalized2 = json.dumps(json2, sort_keys=True)
        return normalized1 == normalized2
    except:
        return False

def get_primary_interface_mac():
    """
    获取主网卡的MAC地址
    优先使用默认路由的网卡，如果失败则使用第一个非回环、非虚拟网卡
    返回: MAC地址字符串，失败返回空字符串
    """
    try:
        # 方法1: 尝试获取默认路由的网卡
        result = subprocess.run(
            ['ip', 'route', 'show', 'default'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0 and result.stdout:
            # 解析默认路由输出，格式如: default via 192.168.1.1 dev eth0
            lines = result.stdout.strip().split('\n')
            for line in lines:
                if 'dev' in line:
                    parts = line.split()
                    try:
                        dev_index = parts.index('dev')
                        if dev_index + 1 < len(parts):
                            interface = parts[dev_index + 1]
                            # 获取该网卡的MAC地址
                            mac_result = subprocess.run(
                                ['cat', f'/sys/class/net/{interface}/address'],
                                capture_output=True,
                                text=True,
                                timeout=5
                            )
                            if mac_result.returncode == 0:
                                mac = mac_result.stdout.strip()
                                if mac and len(mac) == 17:  # MAC地址格式: xx:xx:xx:xx:xx:xx
                                    return mac
                    except (ValueError, IndexError):
                        continue
        
        # 方法2: 遍历所有网卡，找到第一个非回环、非虚拟网卡
        result = subprocess.run(
            ['ls', '/sys/class/net/'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            interfaces = result.stdout.strip().split('\n')
            # 排除回环和虚拟网卡
            exclude_prefixes = ['lo', 'docker', 'br-', 'veth', 'virbr', 'vmnet']
            
            for interface in interfaces:
                interface = interface.strip()
                if not interface:
                    continue
                
                # 检查是否是排除的网卡
                should_exclude = False
                for prefix in exclude_prefixes:
                    if interface.startswith(prefix):
                        should_exclude = True
                        break
                
                if should_exclude:
                    continue
                
                # 检查网卡是否有MAC地址
                mac_file = Path(f'/sys/class/net/{interface}/address')
                if mac_file.exists():
                    try:
                        mac = mac_file.read_text().strip()
                        if mac and len(mac) == 17:
                            return mac
                    except:
                        continue
        
        return ""
    except Exception as e:
        syslog.syslog(syslog.LOG_ERR, f"获取主网卡MAC地址失败: {str(e)}")
        return ""

def check_frpc_running():
    """检查frpc主进程是否运行"""
    try:
        result = subprocess.run(
            ['systemctl', 'is-active', '--quiet', 'frpc'],
            capture_output=True
        )
        return result.returncode == 0
    except:
        return False

def prepare_env():
    """准备环境变量，确保PATH包含常用路径"""
    env = os.environ.copy()
    # 确保PATH包含常用命令路径
    default_paths = ['/usr/local/sbin', '/usr/local/bin', '/usr/sbin', '/usr/bin', '/sbin', '/bin']
    current_path = env.get('PATH', '')
    path_list = current_path.split(':') if current_path else []
    # 合并路径，去重
    all_paths = path_list + default_paths
    unique_paths = []
    seen = set()
    for p in all_paths:
        if p and p not in seen:
            seen.add(p)
            unique_paths.append(p)
    env['PATH'] = ':'.join(unique_paths)
    return env

def stop_frpc():
    """停止frpc服务（使用$SCRIPT_DIR中的stop.sh脚本）"""
    try:
        stop_script = SCRIPT_DIR / "stop.sh"
        if not stop_script.exists():
            syslog.syslog(syslog.LOG_ERR, f"停止脚本不存在: {stop_script}")
            return False
        
        env = prepare_env()
        result = subprocess.run(
            ['bash', str(stop_script)],
            check=True,
            capture_output=True,
            text=True,
            cwd=str(SCRIPT_DIR),
            env=env
        )
        syslog.syslog(syslog.LOG_INFO, f"停止frpc服务成功: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        error_output = e.stderr if e.stderr else e.stdout
        syslog.syslog(syslog.LOG_ERR, f"停止frpc服务失败: {error_output}")
        return False
    except Exception as e:
        syslog.syslog(syslog.LOG_ERR, f"停止frpc服务异常: {str(e)}")
        return False

def register_frpc_proxy():
    """调用register_frpc_proxy函数重新注册代理（设置REGISTER_FORCE环境变量）"""
    try:
        script_dir = SCRIPT_DIR
        common_sh = script_dir / "common.sh"
        
        if not common_sh.exists():
            syslog.syslog(syslog.LOG_ERR, f"common.sh不存在: {common_sh}")
            return False
        
        # 设置环境变量并调用register_frpc_proxy函数
        env = os.environ.copy()
        env['REGISTER_FORCE'] = 'true'
        
        # 执行bash命令调用register_frpc_proxy函数
        cmd = f"""
        cd {script_dir} && \
        source {common_sh} && \
        register_frpc_proxy
        """
        
        result = subprocess.run(
            ['bash', '-c', cmd],
            env=env,
            cwd=str(script_dir),
            check=True,
            capture_output=True,
            text=True
        )
        
        # 验证配置文件是否成功更新
        target_config = SERVICE_DIR / "frpc.toml"
        if target_config.exists():
            # 检查文件修改时间，确保是新文件
            import time as time_module
            file_mtime = target_config.stat().st_mtime
            current_time = time_module.time()
            # 文件应该在最近10秒内被修改
            if current_time - file_mtime < 10:
                syslog.syslog(syslog.LOG_INFO, f"代理注册成功，配置文件已更新: {result.stdout}")
                return True
            else:
                syslog.syslog(syslog.LOG_WARNING, f"配置文件存在但修改时间异常: {file_mtime}, 当前时间: {current_time}")
        else:
            syslog.syslog(syslog.LOG_ERR, f"配置文件不存在: {target_config}")
        
        syslog.syslog(syslog.LOG_INFO, f"代理注册完成: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        syslog.syslog(syslog.LOG_ERR, f"代理注册失败: {e.stderr if e.stderr else e.stdout}")
        return False
    except Exception as e:
        syslog.syslog(syslog.LOG_ERR, f"代理注册异常: {str(e)}")
        return False

def start_frpc():
    """启动frpc主进程"""
    global FRPC_PROCESS
    try:
        config_file = SERVICE_DIR / "frpc.toml"
        if not config_file.exists():
            syslog.syslog(syslog.LOG_INFO, "frpc.toml 不存在，跳过启动 frpc")
            return False
        
        frpc_binary = "/usr/local/bin/frpc"
        if not os.path.exists(frpc_binary):
            syslog.syslog(syslog.LOG_ERR, f"frpc 二进制文件不存在: {frpc_binary}")
            return False
            
        # 启动 frpc 进程
        log_file = open(SERVICE_DIR / "frpc.log", 'a')
        FRPC_PROCESS = subprocess.Popen(
            [frpc_binary, '-c', str(config_file)],
            stdout=log_file,
            stderr=subprocess.STDOUT
        )
        syslog.syslog(syslog.LOG_INFO, f"frpc 启动成功，PID: {FRPC_PROCESS.pid}")
        return True
    except Exception as e:
        syslog.syslog(syslog.LOG_ERR, f"启动 frpc 异常: {str(e)}")
        return False

def restart_frpc():
    """重启frpc服务（先停止再启动，使用$SCRIPT_DIR中的脚本）"""
    try:
        # 1. 停止服务
        syslog.syslog(syslog.LOG_INFO, "停止frpc服务...")
        if not stop_frpc():
            syslog.syslog(syslog.LOG_ERR, "停止frpc服务失败")
            return False
        
        # 等待服务完全停止
        time.sleep(1)
        
        # 2. 启动服务（start.sh脚本会处理注册和启动）
        syslog.syslog(syslog.LOG_INFO, "启动frpc服务...")
        if not start_frpc():
            syslog.syslog(syslog.LOG_ERR, "启动frpc服务失败")
            return False
        
        syslog.syslog(syslog.LOG_INFO, "frpc服务重启成功")
        return True
    except Exception as e:
        syslog.syslog(syslog.LOG_ERR, f"重启frpc服务异常: {str(e)}")
        return False

def check_tmp_frpc_running():
    """检查临时frpc进程是否运行"""
    try:
        pid_file = SERVICE_DIR / "frpc_tmp.pid"
        if not pid_file.exists():
            return False
        
        with open(pid_file, 'r') as f:
            pid = int(f.read().strip())
        
        # 检查进程是否存在
        subprocess.run(['kill', '-0', str(pid)], check=True, capture_output=True)
        return True
    except:
        return False

def start_tmp_frpc():
    """启动临时frpc进程"""
    try:
        config_file = SERVICE_DIR / "frpc_tmp.toml"
        if not config_file.exists():
            return False
        
        frpc_binary = SERVICE_DIR / "bin" / "frpc"
        if not frpc_binary.exists():
            return False
        
        # 启动临时frpc进程（后台运行）
        log_file = open(SERVICE_DIR / "frpc_tmp.log", 'a')
        process = subprocess.Popen(
            [str(frpc_binary), '-c', str(config_file)],
            stdout=log_file,
            stderr=subprocess.STDOUT,
            start_new_session=True
        )
        
        # 保存PID
        pid_file = SERVICE_DIR / "frpc_tmp.pid"
        with open(pid_file, 'w') as f:
            f.write(str(process.pid))
        
        return True
    except Exception as e:
        print(f"Error starting tmp frpc: {e}")
        return False

def stop_tmp_frpc():
    """停止临时frpc进程"""
    try:
        pid_file = SERVICE_DIR / "frpc_tmp.pid"
        if pid_file.exists():
            with open(pid_file, 'r') as f:
                pid = int(f.read().strip())
            
            # 尝试优雅停止
            try:
                subprocess.run(['kill', str(pid)], check=True, timeout=2)
            except:
                # 强制杀死
                subprocess.run(['kill', '-9', str(pid)], check=False)
            
            pid_file.unlink()
        
        # 检查是否有其他临时frpc进程
        try:
            subprocess.run(['pkill', '-f', 'frpc -c.*frpc_tmp.toml'], check=False)
        except:
            pass
        
        return True
    except:
        return False

def cleanup_tmp_frpc_files():
    """清理临时frpc相关文件"""
    try:
        # 停止临时frpc
        stop_tmp_frpc()
        
        # 删除配置文件
        config_file = SERVICE_DIR / "frpc_tmp.toml"
        if config_file.exists():
            config_file.unlink()
        
        # 删除PID文件
        pid_file = SERVICE_DIR / "frpc_tmp.pid"
        if pid_file.exists():
            pid_file.unlink()
        
        # 删除访客码文件
        if VISITOR_CODE_FILE.exists():
            VISITOR_CODE_FILE.unlink()
        
        # 删除日志文件（可选）
        log_file = SERVICE_DIR / "frpc_tmp.log"
        if log_file.exists():
            log_file.unlink()
        
        return True
    except Exception as e:
        print(f"Error cleaning up tmp frpc files: {e}")
        return False

def register_tmp_proxy():
    """调用临时代理注册接口"""
    try:
        # 调用common.sh中的register_tmp_frpc_proxy函数
        script_dir = SCRIPT_DIR
        # 使用bash -c执行，确保能正确source脚本
        cmd = f'cd {script_dir} && source {script_dir}/common.sh && register_tmp_frpc_proxy'
        result = subprocess.run(
            ['bash', '-c', cmd],
            capture_output=True,
            text=True,
            env=os.environ.copy()
        )
        
        if result.returncode == 0:
            # 从输出中提取访客码
            visitor_code = ""
            for line in result.stdout.split('\n'):
                if 'Visitor Code:' in line:
                    code = line.split('Visitor Code:')[1].strip()
                    if code:
                        visitor_code = code
                        break
            
            # 如果从输出中没找到，尝试从文件读取
            if not visitor_code:
                visitor_code = load_visitor_code()
            
            if visitor_code:
                save_visitor_code(visitor_code)
                return True, visitor_code
            else:
                return True, ""
        else:
            error_msg = result.stderr or result.stdout
            return False, error_msg
    except Exception as e:
        return False, str(e)

@app.route('/')
def index():
    """主页面 - 根据登录状态返回不同页面"""
    # 检查是否能获取到iEG用户信息
    success, account, userid, companyid = check_ieg_user_info()
    
    if success:
        # 用户已登录，设置session
        session['logged_in'] = True
        session['account'] = account
        session['userid'] = userid
        session['companyid'] = companyid
        session.permanent = True
        return render_template('index.html')
    else:
        # 需要登录，返回登录页面
        return render_template('login.html')

@app.route('/frpc/api/auth/check', methods=['GET'])
def check_auth():
    """检查登录状态"""
    success, account, userid, companyid = check_ieg_user_info()
    
    if success:
        session['logged_in'] = True
        session['account'] = account
        session['userid'] = userid
        session['companyid'] = companyid
        return jsonify({
            'success': True,
            'loggedIn': True,
            'account': account,
            'userid': userid,
            'companyid': companyid
        })
    else:
        session.clear()
        return jsonify({'success': True, 'loggedIn': False})

@app.route('/frpc/api/auth/login', methods=['POST'])
def login():
    """登录接口"""
    data = request.json
    account = data.get('account', '')
    password = data.get('password', '')
    
    if not account or not password:
        return jsonify({'success': False, 'message': '账号和密码不能为空'}), 400
    
    # 调用iEG登录接口
    success, message = login_to_ieg(account, password)
    
    if success:
        # 登录成功后，获取用户信息
        time.sleep(0.5)  # 等待一下确保登录状态同步
        check_success, acc, uid, cid = check_ieg_user_info()
        
        if check_success:
            session['logged_in'] = True
            session['account'] = acc
            session['userid'] = uid
            session['companyid'] = cid
            session.permanent = True
            
            syslog.syslog(syslog.LOG_INFO, f"用户 {acc} 登录成功")
            return jsonify({'success': True, 'message': '登录成功'})
        else:
            return jsonify({'success': False, 'message': '登录成功但获取用户信息失败'}), 500
    else:
        return jsonify({'success': False, 'message': message}), 401

@app.route('/frpc/api/auth/logout', methods=['POST'])
def logout():
    """登出接口"""
    try:
        # 获取当前登录用户账号（用于日志）
        account = session.get('account', '')
        syslog.syslog(syslog.LOG_INFO, f"收到登出请求，用户: {account if account else '未知'}")
        
        # 调用iEG登出接口
        success, message = logout_from_ieg()
        
        if success:
            # 清除session
            session.clear()
            if account:
                syslog.syslog(syslog.LOG_INFO, f"用户 {account} 登出成功，已清除本地session")
            else:
                syslog.syslog(syslog.LOG_INFO, "登出成功，已清除本地session")
            return jsonify({'success': True, 'message': '已登出'})
        else:
            # 即使iEG登出失败，也清除本地session
            session.clear()
            syslog.syslog(syslog.LOG_WARNING, f"iEG登出失败，但已清除本地session: {message}")
            return jsonify({'success': True, 'message': '已登出（本地session已清除）'})
    except Exception as e:
        # 发生异常时也清除session
        session.clear()
        syslog.syslog(syslog.LOG_ERR, f"登出异常: {str(e)}，已清除本地session")
        return jsonify({'success': True, 'message': '已登出（本地session已清除）'})

@app.route('/frpc/api/system/mac', methods=['GET'])
@require_login
def get_system_mac():
    """获取主机主网卡MAC地址"""
    try:
        mac_address = get_primary_interface_mac()
        return jsonify({
            'success': True,
            'data': mac_address
        })
    except Exception as e:
        syslog.syslog(syslog.LOG_ERR, f"获取MAC地址异常: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/frpc/api/service/status', methods=['GET'])
@require_login
def get_service_status():
    """获取frpc服务状态"""
    try:
        # 检查主服务状态
        main_running = check_frpc_running()
        
        # 检查临时服务状态
        tmp_running = check_tmp_frpc_running()
        
        return jsonify({
            'success': True,
            'data': {
                'mainService': main_running,
                'tmpService': tmp_running
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/frpc/api/service/start', methods=['POST'])
@require_login
def start_service():
    """启动frpc主服务"""
    try:
        if check_frpc_running():
            return jsonify({'success': False, 'message': 'frpc服务已在运行中'}), 400
        
        syslog.syslog(syslog.LOG_INFO, f"用户 {session.get('account')} 请求启动frpc服务")
        
        if start_frpc():
            return jsonify({'success': True, 'message': 'frpc服务启动成功'})
        else:
            return jsonify({'success': False, 'message': 'frpc服务启动失败'}), 500
    except Exception as e:
        syslog.syslog(syslog.LOG_ERR, f"启动frpc服务异常: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/frpc/api/service/stop', methods=['POST'])
@require_login
def stop_service():
    """停止frpc主服务"""
    try:
        if not check_frpc_running():
            return jsonify({'success': False, 'message': 'frpc服务未运行'}), 400
        
        syslog.syslog(syslog.LOG_INFO, f"用户 {session.get('account')} 请求停止frpc服务")
        
        if stop_frpc():
            return jsonify({'success': True, 'message': 'frpc服务停止成功'})
        else:
            return jsonify({'success': False, 'message': 'frpc服务停止失败'}), 500
    except Exception as e:
        syslog.syslog(syslog.LOG_ERR, f"停止frpc服务异常: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/frpc/api/service/restart', methods=['POST'])
@require_login
def restart_service():
    """重启frpc主服务"""
    try:
        syslog.syslog(syslog.LOG_INFO, f"用户 {session.get('account')} 请求重启frpc服务")
        
        if restart_frpc():
            return jsonify({'success': True, 'message': 'frpc服务重启成功'})
        else:
            return jsonify({'success': False, 'message': 'frpc服务重启失败'}), 500
    except Exception as e:
        syslog.syslog(syslog.LOG_ERR, f"重启frpc服务异常: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/frpc/api/config/main', methods=['GET'])
@require_login
def get_main_config():
    """获取主配置（register_proxy.json）"""
    config_file = SERVICE_DIR / "register_proxy.json"
    default_file = SCRIPT_DIR / "conf" / "register_proxy.json"
    
    config = load_config(config_file, default_file)
    return jsonify({'success': True, 'data': config})

@app.route('/frpc/api/config/tmp', methods=['GET'])
@require_login
def get_tmp_config():
    """获取临时配置（register_proxy_tmp.json）"""
    config_file = SERVICE_DIR / "register_proxy_tmp.json"
    default_file = SCRIPT_DIR / "conf" / "register_proxy_tmp.json"
    
    config = load_config(config_file, default_file)
    return jsonify({'success': True, 'data': config})

@app.route('/frpc/api/config/remote-assistance', methods=['GET'])
@require_login
def get_remote_assistance():
    """获取RemoteAssistance配置"""
    value = load_remote_assistance()
    return jsonify({'success': True, 'data': value})

@app.route('/frpc/api/config/visitor-code', methods=['GET'])
@require_login
def get_visitor_code():
    """获取访客码"""
    code = load_visitor_code()
    return jsonify({'success': True, 'data': code})

@app.route('/frpc/api/config/reset/main', methods=['POST'])
@require_login
def reset_main_config():
    """恢复主配置为默认值"""
    try:
        main_config_file = SERVICE_DIR / "register_proxy.json"
        default_file = SCRIPT_DIR / "conf" / "register_proxy.json"
        
        if not default_file.exists():
            return jsonify({'success': False, 'message': '默认配置文件不存在'}), 404
        
        # 从默认文件拷贝
        shutil.copy2(default_file, main_config_file)
        return jsonify({'success': True, 'message': '主配置已恢复为默认值'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/frpc/api/config/reset/tmp', methods=['POST'])
@require_login
def reset_tmp_config():
    """恢复临时配置为默认值"""
    try:
        tmp_config_file = SERVICE_DIR / "register_proxy_tmp.json"
        default_file = SCRIPT_DIR / "conf" / "register_proxy_tmp.json"
        
        if not default_file.exists():
            return jsonify({'success': False, 'message': '默认配置文件不存在'}), 404
        
        # 从默认文件拷贝
        shutil.copy2(default_file, tmp_config_file)
        return jsonify({'success': True, 'message': '临时配置已恢复为默认值'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/frpc/api/config/save', methods=['POST'])
@require_login
def save_configs():
    """保存配置"""
    # 保存前再次验证iEG用户信息
    success, account, userid, companyid = check_ieg_user_info()
    if not success:
        session.clear()
        return jsonify({'success': False, 'message': '登录已过期，请重新登录', 'needLogin': True}), 401
    
    data = request.json
    
    main_config = data.get('mainConfig', [])
    tmp_config = data.get('tmpConfig', [])  # 如果RemoteAssistance为false，可能为空
    remote_assistance = data.get('remoteAssistance', False)
    
    # 验证：主配置至少有一个
    if len(main_config) == 0:
        return jsonify({'success': False, 'message': '主配置至少需要有一个服务'}), 400
    
    # 验证：远程协助启用时，临时配置至少有一个
    if remote_assistance and len(tmp_config) == 0:
        return jsonify({'success': False, 'message': '启用远程协助时，临时配置至少需要有一个服务'}), 400
    
    # 检查配置数量限制（最多10个）
    if len(main_config) > 10:
        return jsonify({'success': False, 'message': '主配置最多只能添加10个服务'}), 400
    
    if remote_assistance and len(tmp_config) > 10:
        return jsonify({'success': False, 'message': '临时配置最多只能添加10个服务'}), 400
    
    # 加载旧配置用于比较
    main_config_file = SERVICE_DIR / "register_proxy.json"
    tmp_config_file = SERVICE_DIR / "register_proxy_tmp.json"
    
    old_main_config = load_config(main_config_file, SCRIPT_DIR / "conf" / "register_proxy.json")
    old_tmp_config = load_config(tmp_config_file, SCRIPT_DIR / "conf" / "register_proxy_tmp.json")
    old_remote_assistance = load_remote_assistance()
    
    # 处理主配置：生成bindPort和link
    processed_main_config = []
    for item in main_config:
        service_name = item.get('serviceName', '')
        local_port = int(item.get('localPort', 0))
        bind_port = generate_bind_port(local_port, 3)  # 主配置使用前缀3
        link = get_link_value(local_port)
        
        processed_main_config.append({
            'serviceName': service_name,
            'localPort': local_port,
            'bindPort': bind_port if bind_port else item.get('bindPort', 0),
            'link': link
        })
    
    # 处理临时配置：生成bindPort和link
    processed_tmp_config = []
    for item in tmp_config:
        service_name = item.get('serviceName', '')
        local_port = int(item.get('localPort', 0))
        bind_port = generate_bind_port(local_port, 4)  # 临时配置使用前缀4
        link = get_link_value(local_port)
        
        processed_tmp_config.append({
            'serviceName': service_name,
            'localPort': local_port,
            'bindPort': bind_port if bind_port else item.get('bindPort', 0),
            'link': link
        })
    
    # 保存配置
    save_config(main_config_file, processed_main_config)
    save_config(tmp_config_file, processed_tmp_config)
    save_remote_assistance(remote_assistance)
    
    # 检查是否需要重启frpc主进程
    # 注意：需要规范化旧配置，因为旧配置可能缺少bindPort和link字段
    normalized_old_main_config = []
    for item in old_main_config:
        local_port = item.get('localPort', 0)
        bind_port = item.get('bindPort')
        if not bind_port:
            bind_port = generate_bind_port(local_port, 3)
        link = item.get('link')
        if link is None:
            link = get_link_value(local_port)
        normalized_old_main_config.append({
            'serviceName': item.get('serviceName', ''),
            'localPort': local_port,
            'bindPort': bind_port if bind_port else 0,
            'link': link
        })
    
    main_config_changed = not compare_json_content(normalized_old_main_config, processed_main_config)
    frpc_running = check_frpc_running()
    
    # 记录详细日志到系统日志
    syslog.openlog('frpc-manager', syslog.LOG_PID, syslog.LOG_USER)
    syslog.syslog(syslog.LOG_INFO, f"用户 {account}({userid}) 保存配置: 主配置改变={main_config_changed}, frpc运行={frpc_running}")
    if main_config_changed:
        syslog.syslog(syslog.LOG_INFO, f"旧配置: {json.dumps(normalized_old_main_config, ensure_ascii=False)}")
        syslog.syslog(syslog.LOG_INFO, f"新配置: {json.dumps(processed_main_config, ensure_ascii=False)}")
    
    restart_message = ""
    if main_config_changed:
        if frpc_running:
            # 重启frpc主进程（设置REGISTER_FORCE环境变量）
            syslog.syslog(syslog.LOG_INFO, "开始重启frpc服务...")
            if restart_frpc():
                restart_message = "，frpc主服务已重启"
                syslog.syslog(syslog.LOG_INFO, "frpc服务重启成功")
            else:
                restart_message = "，但frpc主服务重启失败"
                syslog.syslog(syslog.LOG_ERR, "frpc服务重启失败")
        else:
            # 主配置改变了但frpc没有运行，启动它
            syslog.syslog(syslog.LOG_INFO, "开始启动frpc服务...")
            if start_frpc():
                restart_message = "，frpc主服务已启动"
                syslog.syslog(syslog.LOG_INFO, "frpc服务启动成功")
            else:
                restart_message = "，但frpc主服务启动失败"
                syslog.syslog(syslog.LOG_ERR, "frpc服务启动失败")
    else:
        syslog.syslog(syslog.LOG_INFO, "主配置未改变，无需重启")
    
    # 处理RemoteAssistance变化
    if remote_assistance != old_remote_assistance:
        if remote_assistance:
            # 从false变为true，调用临时代理注册接口获取frpc_tmp.toml，然后启动临时frpc
            success, result = register_tmp_proxy()
            if success:
                # 启动临时frpc
                if start_tmp_frpc():
                    return jsonify({'success': True, 'message': f'配置保存成功{restart_message}，临时frpc已启动', 'visitorCode': result})
                else:
                    return jsonify({'success': False, 'message': f'配置保存成功{restart_message}，但启动临时frpc失败'})
            else:
                return jsonify({'success': False, 'message': f'配置保存成功{restart_message}，但临时代理注册失败: {result}'})
        else:
            # 从true变为false，停止临时frpc并清理文件
            cleanup_tmp_frpc_files()
            return jsonify({'success': True, 'message': f'配置保存成功{restart_message}，临时frpc已停止并清理'})
    elif remote_assistance and remote_assistance == old_remote_assistance:
        # RemoteAssistance保持true，检查临时配置是否变化
        tmp_config_changed = not compare_json_content(old_tmp_config, processed_tmp_config)
        if tmp_config_changed:
            # 重新调用临时代理注册接口，然后重启临时frpc
            success, result = register_tmp_proxy()
            if success:
                # 停止旧的临时frpc
                stop_tmp_frpc()
                # 启动新的临时frpc
                if start_tmp_frpc():
                    return jsonify({'success': True, 'message': f'配置保存成功{restart_message}，临时frpc已重启', 'visitorCode': result})
                else:
                    return jsonify({'success': False, 'message': f'配置保存成功{restart_message}，但重启临时frpc失败'})
            else:
                return jsonify({'success': False, 'message': f'配置保存成功{restart_message}，但临时代理注册失败: {result}'})
    
    return jsonify({'success': True, 'message': f'配置保存成功{restart_message}'})

if __name__ == '__main__':
    # 确保目录存在
    SERVICE_DIR.mkdir(parents=True, exist_ok=True)
    app.run(host='0.0.0.0', port=8888, debug=False)


FRPC_PROCESS = None

if __name__ == '__main__':
    # 确保配置目录存在
    SERVICE_DIR.mkdir(parents=True, exist_ok=True)
    
    # 启动时检查并启动 frpc
    # 这里可以添加逻辑：如果存在配置文件则启动 frpc，否则等待配置
    if (SERVICE_DIR / "frpc.toml").exists():
        start_frpc()
    else:
        syslog.syslog(syslog.LOG_INFO, "等待配置以启动 frpc...")

    # 启动 Flask 应用
    # host='0.0.0.0' 允许外部访问
    app.run(host='0.0.0.0', port=8099)
