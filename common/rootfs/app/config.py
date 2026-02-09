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
HADDONS_API_BASE_URL = os.getenv('HADDONS_API_BASE_URL', "http://localhost:8099")
# 云端服务地址
CLOUD_API_BASE_URL = "https://euhome.linklinkiot.com/sfsaas/api"
HEARTBEAT_API_URL = "https://euadmin.linklinkiot.com/frpserver/api/heartbeat"
PROXY_API_URL = "https://euadmin.linklinkiot.com/frpserver/api/proxy"
TMP_PROXY_API_URL = "https://euadmin.linklinkiot.com/frpserver/api/tmp-proxy"

# 代理目标IP (默认为 localhost，Docker Bridge 模式下应通过环境变量覆盖为 host.docker.internal)
TARGET_IP = os.getenv('TARGET_IP', "localhost")



# ================= Web配置 =================
SECRET_KEY = os.urandom(24)
PERMANENT_SESSION_LIFETIME = timedelta(hours=2)
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
TEMPLATES_DIR = APP_DIR / 'templates'
