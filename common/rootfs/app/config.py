import os
from pathlib import Path
from datetime import timedelta

# ================= 配置路径 =================
_script_file = Path(__file__).resolve()
APP_DIR = _script_file.parent         # app/

# 基础运行目录（固定路径，不再支持环境变量覆盖）
BASE_DIR = APP_DIR.parent / "runtime"

# 服务与数据子目录（基于 BASE_DIR 自动生成）
SERVICE_DIR = BASE_DIR / "etc"
DATA_DIR = BASE_DIR / "data"

REMOTE_ASSISTANCE_FILE = SERVICE_DIR / "remote_assistance"
VISITOR_CODE_FILE = SERVICE_DIR / "visitor_code"
DEVICE_ID_FILE = DATA_DIR / "device_id.txt"

# 脚本路径
SCRIPT_DIR = APP_DIR 


# Haddons API 地址
HADDONS_API_BASE_URL = os.getenv('HADDONS_API_BASE_URL', "http://127.0.0.1:8099")
# ================= 集群配置 =================
# 集群地区映射（china: 国内, oversea: 海外）
CLUSTER_DOMAINS = {
    'china': {
        'home': 'https://home.linklinkiot.com',
        'admin': 'https://admin.linklinkiot.com',
    },
    'oversea': {
        'home': 'https://euhome.linklinkiot.com',
        'admin': 'https://euadmin.linklinkiot.com',
    },
}

# 当前集群（默认海外）
CURRENT_CLUSTER = 'oversea'

def update_cloud_urls(cluster='oversea'):
    """根据集群地区更新云端服务地址"""
    global CURRENT_CLUSTER, CLOUD_API_BASE_URL, HEARTBEAT_API_URL, PROXY_API_URL, TMP_PROXY_API_URL
    if cluster not in CLUSTER_DOMAINS:
        cluster = 'oversea'
    CURRENT_CLUSTER = cluster
    domains = CLUSTER_DOMAINS[cluster]
    CLOUD_API_BASE_URL = f"{domains['home']}/sfsaas/api"
    HEARTBEAT_API_URL = f"{domains['admin']}/frpserver/api/heartbeat"
    PROXY_API_URL = f"{domains['admin']}/frpserver/api/proxy"
    TMP_PROXY_API_URL = f"{domains['admin']}/frpserver/api/tmp-proxy"

# 云端服务地址（初始化为默认集群）
CLOUD_API_BASE_URL = ""
HEARTBEAT_API_URL = ""
PROXY_API_URL = ""
TMP_PROXY_API_URL = ""
update_cloud_urls(CURRENT_CLUSTER)

# 代理目标IP (默认为 127.0.0.1，Docker Bridge 模式下应通过环境变量覆盖为 host.docker.internal)
TARGET_IP = os.getenv('TARGET_IP', "127.0.0.1")



# ================= Web配置 =================
SECRET_KEY = os.urandom(24)
PERMANENT_SESSION_LIFETIME = timedelta(hours=2)
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
TEMPLATES_DIR = APP_DIR / 'templates'
