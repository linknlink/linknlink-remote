import subprocess
import logging
import os
import json
import time
from pathlib import Path

from config import SCRIPT_DIR, VISITOR_CODE_FILE, DATA_DIR
import config
from utils import prepare_env, compare_json_content, generate_bind_port, get_link_value, enc_password
import shutil
# 延迟导入，避免循环依赖 (如果 cloud_service 导入 frpc_service)
import cloud_service

logger = logging.getLogger(__name__)

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
        config_file = config.SERVICE_DIR / "frpc.toml"
        if not config_file.exists():
            logger.info("frpc.toml 不存在，跳过启动 frpc")
            return False
        
        # 二进制查找策略
        search_paths = [
            config.SERVICE_DIR / "bin" / "frpc",                        # 1. 配置目录下的 bin
            Path("/usr/local/bin/frpc"),                                # 2. 标准系统路径
            Path("/usr/bin/frpc"),                                      # 3. 备选系统路径
            Path(shutil.which("frpc") or "/usr/bin/frpc")               # 4. PATH 环境变量
        ]
        
        frpc_binary = None
        for path in search_paths:
            if path and os.path.exists(path):
                frpc_binary = path
                break
                
        if not frpc_binary:
            logger.error("frpc 二进制文件不存在，已尝试路径: " + ", ".join(str(p) for p in search_paths))
            return False
            
        logger.info(f"使用 frpc 二进制: {frpc_binary}")
            
        # 启动 frpc 进程
        log_file_path = config.SERVICE_DIR / "frpc.log"
        log_file = open(log_file_path, 'a')
        FRPC_PROCESS = subprocess.Popen(
            [frpc_binary, '-c', str(config_file)],
            stdout=log_file,
            stderr=subprocess.STDOUT,
            start_new_session=True
        )
        logger.info(f"frpc 启动成功，PID: {FRPC_PROCESS.pid}")
        return True
    except Exception as e:
        logger.error(f"启动 frpc 异常: {str(e)}")
        return False

def stop_frpc():
    """停止frpc主进程"""
    global FRPC_PROCESS
    if FRPC_PROCESS and FRPC_PROCESS.poll() is None:
        try:
            FRPC_PROCESS.terminate()
            FRPC_PROCESS.wait(timeout=5)
            logger.info("frpc 停止成功")
        except:
            FRPC_PROCESS.kill()
            logger.warning("frpc 强制停止")
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
        logger.error(f"重启frpc服务异常: {str(e)}")
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
        logger.error(f"Config conversion failed: {str(e)}")
        return False

def register_frpc_proxy():
    """向云端重新注册代理"""
    try:
        # 1. 转换配置格式
        input_file = config.SERVICE_DIR / "register_proxy.json"
        
        # 如果不存在，尝试从模板复制
        if not input_file.exists():
             template_file = SCRIPT_DIR / "conf" / "register_proxy.json"
             if template_file.exists():
                 import shutil
                 shutil.copy(template_file, input_file)
        
        if not input_file.exists():
            logger.error("register_proxy.json 不存在且无法通过模板创建")
            return False

        with open(input_file, 'r') as f:
            proxy_list = json.load(f)

        # 2. 调用 Python 注册逻辑
        from cloud_service import register_proxy_to_cloud
        config_content, _ = register_proxy_to_cloud(proxy_list, is_tmp=False, force=True)
        
        if config_content:
            # 3. 将生成的配置文件保存到 SERVICE_DIR
            target_config = config.SERVICE_DIR / "frpc.toml"
            with open(target_config, 'w') as f:
                f.write(config_content)
            
            logger.info(f"代理注册成功，配置文件已更新: {target_config}")
            return True
        else:
            logger.error("代理注册失败：未能从云端获取配置内容")
            return False

    except Exception as e:
        logger.error(f"代理注册异常: {str(e)}")
        return False


# 临时 FRPC 管理逻辑 (保持原样移植)
def check_tmp_frpc_running():
    try:
        pid_file = config.SERVICE_DIR / "frpc_tmp.pid"
        if not pid_file.exists(): return False
        with open(pid_file, 'r') as f: pid = int(f.read().strip())
        subprocess.run(['kill', '-0', str(pid)], check=True, capture_output=True)
        return True
    except: return False

def start_tmp_frpc():
    try:
        config_file = config.SERVICE_DIR / "frpc_tmp.toml"
        if not config_file.exists(): return False
        frpc_binary = config.SERVICE_DIR / "bin" / "frpc"
        if not frpc_binary.exists(): 
            # 尝试系统路径
            import shutil
            frpc_binary = shutil.which("frpc") or "/usr/bin/frpc"
            if not frpc_binary or not os.path.exists(frpc_binary):
                 return False

        log_file = open(config.SERVICE_DIR / "frpc_tmp.log", 'a')
        process = subprocess.Popen([str(frpc_binary), '-c', str(config_file)], stdout=log_file, stderr=subprocess.STDOUT, start_new_session=True)
        pid_file = config.SERVICE_DIR / "frpc_tmp.pid"
        with open(pid_file, 'w') as f: f.write(str(process.pid))
        return True
    except Exception as e: return False

def stop_tmp_frpc():
    try:
        pid_file = config.SERVICE_DIR / "frpc_tmp.pid"
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
        config_file = config.SERVICE_DIR / "frpc_tmp.toml"
        if config_file.exists(): config_file.unlink()
        pid_file = config.SERVICE_DIR / "frpc_tmp.pid"
        if pid_file.exists(): pid_file.unlink()
        if VISITOR_CODE_FILE.exists(): VISITOR_CODE_FILE.unlink()
        return True
    except: return False

def register_tmp_proxy():
    """临时代理注册"""
    try:
        # 1. 读取配置
        input_file = config.SERVICE_DIR / "register_proxy_tmp.json"
        
        # 如果不存在，尝试从模板复制
        if not input_file.exists():
             template_file = SCRIPT_DIR / "conf" / "register_proxy_tmp.json"
             if template_file.exists():
                 import shutil
                 shutil.copy(template_file, input_file)
        
        if not input_file.exists():
            return False, "register_proxy_tmp.json 不存在"

        with open(input_file, 'r') as f:
            proxy_list = json.load(f)

        # 2. 调用 Python 注册逻辑
        from cloud_service import register_proxy_to_cloud
        config_content, visitor_code = register_proxy_to_cloud(proxy_list, is_tmp=True)
        
        if config_content:
            # 3. 保存配置文件
            target_config = config.SERVICE_DIR / "frpc_tmp.toml"
            with open(target_config, 'w') as f:
                f.write(config_content)
            
            # 4. 保存访客码
            if visitor_code:
                with open(VISITOR_CODE_FILE, 'w') as f:
                    f.write(visitor_code)
                return True, visitor_code
            return True, ""
        else:
            return False, visitor_code or "获取临时配置失败"

    except Exception as e:
        return False, str(e)
