import hashlib
import json
import shutil
import syslog
import os

def enc_password(password):
    """
    加密密码（与iegauth项目中的blaccount.EncPassword保持一致）
    加密方法：SHA1(password + "4969fj#k23#")
    """
    data = password + "4969fj#k23#"
    sha1_hash = hashlib.sha1(data.encode('utf-8')).hexdigest()
    return sha1_hash

def compare_json_content(json1, json2):
    """比较两个JSON内容是否相同（忽略格式差异）"""
    try:
        normalized1 = json.dumps(json1, sort_keys=True)
        normalized2 = json.dumps(json2, sort_keys=True)
        return normalized1 == normalized2
    except:
        return False

def generate_bind_port(local_port, prefix):
    """
    根据localPort生成bindPort
    规则：
    1. localPort 范围 1000～9999：加前缀（文件1用3，文件2用4）
    2. localPort < 1000：加前缀且中间补0凑成5位（例如：802 -> 30802, 22 -> 30022）
    3. localPort >= 10000：返回空字符串，使用随机端口
    """
    try:
        local_port = int(local_port)
    except ValueError:
        return None
        
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
    try:
        return int(local_port) != 22
    except ValueError:
        return True

def prepare_env():
    """准备环境变量，确保PATH包含常用路径"""
    env = os.environ.copy()
    default_paths = ['/usr/local/sbin', '/usr/local/bin', '/usr/sbin', '/usr/bin', '/sbin', '/bin']
    current_path = env.get('PATH', '')
    path_list = current_path.split(':') if current_path else []
    all_paths = path_list + default_paths
    unique_paths = []
    seen = set()
    for p in all_paths:
        if p and p not in seen:
            seen.add(p)
            unique_paths.append(p)
    env['PATH'] = ':'.join(unique_paths)
    return env
