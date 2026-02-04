import os
from pathlib import Path
from datetime import timedelta

# ================= 配置路径 =================
_script_file = Path(__file__).resolve()
APP_DIR = _script_file.parent         # app/

# 运行时目录
RUNTIME_DIR = APP_DIR.parent / "runtime"

# 服务配置目录（支持环境变量覆盖）
SERVICE_DIR = Path(os.getenv('SERVICE_DIR', RUNTIME_DIR / "etc"))
DATA_DIR = Path(os.getenv('DATA_DIR', RUNTIME_DIR / "data"))

REMOTE_ASSISTANCE_FILE = SERVICE_DIR / "remote_assistance"
VISITOR_CODE_FILE = SERVICE_DIR / "visitor_code"
DEVICE_ID_FILE = DATA_DIR / "device_id.txt"

# 脚本路径
SCRIPT_DIR = APP_DIR 


# Haddons API 地址
HADDONS_API_BASE_URL = os.getenv('HADDONS_API_BASE_URL', "http://127.0.0.1:8099")
# 云端服务地址
CLOUD_API_BASE_URL = "https://euhome.linklinkiot.com/sfsaas/api"
HEARTBEAT_API_URL = "https://euadmin.linklinkiot.com/frpserver/api/heartbeat"
PROXY_API_URL = "https://euadmin.linklinkiot.com/frpserver/api/proxy"
TMP_PROXY_API_URL = "https://euadmin.linklinkiot.com/frpserver/api/tmp-proxy"


# ================= Web配置 =================
SECRET_KEY = os.urandom(24)
PERMANENT_SESSION_LIFETIME = timedelta(hours=2)
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
TEMPLATES_DIR = APP_DIR / 'templates'
