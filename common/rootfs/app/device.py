import subprocess
import uuid
import logging
import requests
from pathlib import Path
from config import DEVICE_ID_FILE, HADDONS_API_BASE_URL

logger = logging.getLogger(__name__)

def get_primary_interface_mac():
    """
    获取主网卡的MAC地址
    优先使用 haddons 接口获取，如果失败则尝试本地检测
    返回: MAC地址字符串，失败返回空字符串
    """
    # 优先尝试从 haddons API 获取
    try:
        url = f"{HADDONS_API_BASE_URL.rstrip('/')}/addons/system/mac"
        logger.info(f"Outbound Request: GET {url}")
        response = requests.get(url, timeout=5)
        logger.info(f"Outbound Response: GET {url}, Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            mac = data.get("mac", "")
            if mac and len(mac) == 17:
                logger.info(f"Successfully retrieved MAC from haddons API: {mac}")
                return mac
    except Exception as e:
        logger.warning(f"Failed to get MAC from haddons API: {e}")

    # 回退到原有逻辑
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
        logger.error(f"获取主网卡MAC地址失败: {str(e)}")
        return ""

def get_device_id():
    """
    获取设备ID（MAC地址或UUID）
    优先使用持久化存储的设备ID，否则使用MAC地址，最后使用UUID
    """
    # 1. 优先使用持久化存储的设备ID
    if DEVICE_ID_FILE.exists():
        try:
            saved_id = DEVICE_ID_FILE.read_text().strip().lower()
            if saved_id:
                logger.info(f"Using stored device ID: {saved_id}")
                return saved_id
        except Exception as e:
            logger.warning(f"Read stored device ID failed: {e}")

    # 2. 尝试获取MAC地址
    mac = get_primary_interface_mac().replace(':', '').upper()
    device_id = ""
    
    if mac:
        # 补齐到32位
        padding = 32 - len(mac)
        if padding > 0:
            device_id = "0" * padding + mac
        else:
            device_id = mac
        logger.info(f"Using MAC address as device ID: {device_id}")
    else:
        # 3. 使用UUID
        device_id = uuid.uuid4().hex.upper()
        logger.info(f"Using UUID as device ID: {device_id}")
    
    device_id = device_id.lower()
    
    # 持久化保存
    try:
        # 确保目录存在
        DEVICE_ID_FILE.parent.mkdir(parents=True, exist_ok=True)
        DEVICE_ID_FILE.write_text(device_id)
        logger.info(f"Persisted generated device ID: {device_id}")
    except Exception as e:
        logger.error(f"Save device ID failed: {e}")
        
    return device_id
