import logging
import requests
from pathlib import Path
from config import DEVICE_ID_FILE, HADDONS_API_BASE_URL

logger = logging.getLogger(__name__)

def get_primary_interface_mac():
    """
    获取主网卡的MAC地址
    仅通过 haddons 接口获取，如果失败则直接返回空
    返回: MAC地址字符串，失败返回空字符串
    """
    try:
        url = f"{HADDONS_API_BASE_URL.rstrip('/')}/addons/system/mac"
        logger.info(f"Outbound Request: GET {url}")
        response = requests.get(url, timeout=5)
        logger.info(f"Outbound Response: GET {url}, Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            mac = data.get("mac", "")
            if mac and len(mac) == 17:
                return mac
        else:
            logger.error(f"Failed to get MAC from haddons API: HTTP {response.status_code}")
    except Exception as e:
        logger.error(f"Failed to get MAC from haddons API: {e}")

    return ""

def get_device_id():
    """
    获取设备ID
    强制使用 MAC 地址作为唯一来源，如果获取失败则程序无法运行
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

    # 2. 从 API 获取 MAC 地址
    mac = get_primary_interface_mac().replace(':', '').lower()
    
    if not mac:
        logger.critical("CRITICAL: Failed to retrieve MAC address. System cannot function without device identity.")
        # 抛出异常以阻止后续逻辑，因为心跳和注册都需要此 ID
        raise RuntimeError("Device ID generation failed: MAC retrieval from API failed and no fallback allowed.")

    # 3. 补齐到32位并格式化
    padding = 32 - len(mac)
    if padding > 0:
        device_id = "0" * padding + mac
    else:
        device_id = mac
    
    # 持久化保存
    try:
        DEVICE_ID_FILE.parent.mkdir(parents=True, exist_ok=True)
        DEVICE_ID_FILE.write_text(device_id)
        logger.info(f"Generated and persisted device ID: {device_id}")
    except Exception as e:
        logger.error(f"Save device ID failed: {e}")
        
    return device_id
