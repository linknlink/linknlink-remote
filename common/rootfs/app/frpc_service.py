import subprocess
import syslog
import os
import json
import time
from pathlib import Path

from config import SERVICE_DIR, SCRIPT_DIR, COMMON_SH, VISITOR_CODE_FILE, DATA_DIR
from utils import prepare_env, compare_json_content, generate_bind_port, get_link_value, enc_password

# 全局 FRPC 进程句柄
FRPC_PROCESS = None

def check_frpc_running():
    """检查frpc主进程是否运行"""
    global FRPC_PROCESS
    if FRPC_PROCESS and FRPC_PROCESS.poll() is None:
        return True
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
            # 尝试备选路径
            frpc_binary = shutil.which("frpc") or "/usr/bin/frpc"
            if not frpc_binary or not os.path.exists(frpc_binary):
                syslog.syslog(syslog.LOG_ERR, "frpc 二进制文件不存在")
                return False
            
        # 启动 frpc 进程
        log_file_path = SERVICE_DIR / "frpc.log"
        log_file = open(log_file_path, 'a')
        FRPC_PROCESS = subprocess.Popen(
            [frpc_binary, '-c', str(config_file)],
            stdout=log_file,
            stderr=subprocess.STDOUT,
            start_new_session=True
        )
        syslog.syslog(syslog.LOG_INFO, f"frpc 启动成功，PID: {FRPC_PROCESS.pid}")
        return True
    except Exception as e:
        syslog.syslog(syslog.LOG_ERR, f"启动 frpc 异常: {str(e)}")
        return False

def stop_frpc():
    """停止frpc主进程"""
    global FRPC_PROCESS
    if FRPC_PROCESS and FRPC_PROCESS.poll() is None:
        try:
            FRPC_PROCESS.terminate()
            FRPC_PROCESS.wait(timeout=5)
            syslog.syslog(syslog.LOG_INFO, "frpc 停止成功")
        except:
            FRPC_PROCESS.kill()
            syslog.syslog(syslog.LOG_WARNING, "frpc 强制停止")
        FRPC_PROCESS = None
        return True
    return True

def restart_frpc():
    """重启frpc服务"""
    try:
        stop_frpc()
        time.sleep(1)
        start_frpc()
        return True
    except Exception as e:
        syslog.syslog(syslog.LOG_ERR, f"重启frpc服务异常: {str(e)}")
        return False

# 注册代理函数
def convert_to_cloud_format(input_file, output_file):
    """
    将前端友好的配置格式转换为 Cloud API 需要的格式
    Front: [{"serviceName": "SSH", "localPort": 22, "bindPort": 30022, "link": false}, ...]
    Cloud: [{"localIp": "127.0.0.1", "localPort": "22", "remotePort": "30022", "type": "tcp"}, ...]
    """
    try:
        if not input_file.exists():
            return False
            
        with open(input_file, 'r') as f:
            data = json.load(f)
            
        cloud_data = []
        for item in data:
            try:
                # 确保必需字段存在
                local_port = str(item.get('localPort', ''))
                remote_port = str(item.get('bindPort', ''))
                
                if local_port and remote_port:
                    cloud_data.append({
                        "localIp": "127.0.0.1",
                        "localPort": local_port,
                        "remotePort": remote_port,
                        "type": "tcp"
                        # serviceName is ignored by cloud API for now, or maybe used if we add it? 
                        # Cloud API spec usually just needs ip/port/type.
                    })
            except:
                continue
                
        with open(output_file, 'w') as f:
            json.dump(cloud_data, f, indent=4)
            
        return True
    except Exception as e:
        syslog.syslog(syslog.LOG_ERR, f"Config conversion failed: {str(e)}")
        return False

def register_frpc_proxy():
    """调用register_frpc_proxy函数重新注册代理（设置REGISTER_FORCE环境变量）"""
    try:
        if not COMMON_SH.exists():
            syslog.syslog(syslog.LOG_ERR, f"common.sh不存在: {COMMON_SH}")
            return False
        
        # 1. 转换配置格式
        input_file = SERVICE_DIR / "register_proxy.json"
        cloud_file = SERVICE_DIR / "register_proxy_cloud.json"
        
        # 如果不存在，尝试从模板复制 (web_routes 里也做了类似事情，这里双重保险)
        if not input_file.exists():
             template_file = SCRIPT_DIR / "conf" / "register_proxy.json"
             if template_file.exists():
                 import shutil
                 shutil.copy(template_file, input_file)
        
        if not convert_to_cloud_format(input_file, cloud_file):
             syslog.syslog(syslog.LOG_ERR, "Failed to convert register_proxy.json to cloud format")
             return False

        # 2. 设置环境变量并调用register_frpc_proxy函数
        env = os.environ.copy()
        env['REGISTER_FORCE'] = 'true'
        env['PROXY_JSON_FILE'] = str(cloud_file) # 传递转换后的文件
        
        # 执行bash命令调用register_frpc_proxy函数
        cmd = f"""
        cd {SCRIPT_DIR} && \
        source {COMMON_SH} && \
        register_frpc_proxy
        """
        
        result = subprocess.run(
            ['bash', '-c', cmd],
            env=env,
            cwd=str(SCRIPT_DIR),
            check=True,
            capture_output=True,
            text=True
        )
        
        # 验证配置文件是否成功更新
        target_config = SERVICE_DIR / "frpc.toml"
        if target_config.exists():
            import time as time_module
            file_mtime = target_config.stat().st_mtime
            current_time = time_module.time()
            if current_time - file_mtime < 10:
                syslog.syslog(syslog.LOG_INFO, f"代理注册成功，配置文件已更新: {result.stdout}")
                return True
        syslog.syslog(syslog.LOG_INFO, f"代理注册完成: {result.stdout}")
        return True
    except Exception as e:
        syslog.syslog(syslog.LOG_ERR, f"代理注册异常: {str(e)}")
        return False

# 临时 FRPC 管理逻辑 (保持原样移植)
def check_tmp_frpc_running():
    try:
        pid_file = SERVICE_DIR / "frpc_tmp.pid"
        if not pid_file.exists(): return False
        with open(pid_file, 'r') as f: pid = int(f.read().strip())
        subprocess.run(['kill', '-0', str(pid)], check=True, capture_output=True)
        return True
    except: return False

def start_tmp_frpc():
    try:
        config_file = SERVICE_DIR / "frpc_tmp.toml"
        if not config_file.exists(): return False
        frpc_binary = SERVICE_DIR / "bin" / "frpc"
        if not frpc_binary.exists(): 
            # 尝试系统路径
            import shutil
            frpc_binary = shutil.which("frpc") or "/usr/bin/frpc"
            if not frpc_binary or not os.path.exists(frpc_binary):
                 return False

        log_file = open(SERVICE_DIR / "frpc_tmp.log", 'a')
        process = subprocess.Popen([str(frpc_binary), '-c', str(config_file)], stdout=log_file, stderr=subprocess.STDOUT, start_new_session=True)
        pid_file = SERVICE_DIR / "frpc_tmp.pid"
        with open(pid_file, 'w') as f: f.write(str(process.pid))
        return True
    except Exception as e: return False

def stop_tmp_frpc():
    try:
        pid_file = SERVICE_DIR / "frpc_tmp.pid"
        if pid_file.exists():
            with open(pid_file, 'r') as f: pid = int(f.read().strip())
            try: subprocess.run(['kill', str(pid)], check=True, timeout=2)
            except: subprocess.run(['kill', '-9', str(pid)], check=False)
            pid_file.unlink()
        try: subprocess.run(['pkill', '-f', 'frpc -c.*frpc_tmp.toml'], check=False)
        except: pass
        return True
    except: return False

def cleanup_tmp_frpc_files():
    try:
        stop_tmp_frpc()
        config_file = SERVICE_DIR / "frpc_tmp.toml"
        if config_file.exists(): config_file.unlink()
        pid_file = SERVICE_DIR / "frpc_tmp.pid"
        if pid_file.exists(): pid_file.unlink()
        if VISITOR_CODE_FILE.exists(): VISITOR_CODE_FILE.unlink()
        return True
    except: return False

def register_tmp_proxy():
    try:
        # 1. 转换配置格式
        input_file = SERVICE_DIR / "register_proxy_tmp.json"
        cloud_file = SERVICE_DIR / "register_proxy_tmp_cloud.json"
        
        # 如果不存在，尝试从模板复制
        if not input_file.exists():
             template_file = SCRIPT_DIR / "conf" / "register_proxy_tmp.json"
             if template_file.exists():
                 import shutil
                 shutil.copy(template_file, input_file)
        
        if not convert_to_cloud_format(input_file, cloud_file):
             return False, "Failed to convert tmp config format"

        # 2. 调用 common.sh
        env = os.environ.copy()
        env['PROXY_JSON_FILE'] = str(cloud_file)
        
        cmd = f'cd {SCRIPT_DIR} && source {COMMON_SH} && register_tmp_frpc_proxy'
        result = subprocess.run(['bash', '-c', cmd], capture_output=True, text=True, env=env)
        
        if result.returncode == 0:
            visitor_code = ""
            for line in result.stdout.split('\n'):
                if 'Visitor Code:' in line:
                    code = line.split('Visitor Code:')[1].strip()
                    if code: 
                        visitor_code = code
                        break
            if not visitor_code and VISITOR_CODE_FILE.exists():
                with open(VISITOR_CODE_FILE, 'r') as f: visitor_code = f.read().strip()
            if visitor_code:
                with open(VISITOR_CODE_FILE, 'w') as f: f.write(visitor_code)
                return True, visitor_code
            return True, ""
        return False, result.stderr or result.stdout
    except Exception as e: return False, str(e)
