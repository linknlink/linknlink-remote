import os
from pathlib import Path
from datetime import timedelta

# ================= 配置路径 =================
_script_file = Path(__file__).resolve()
APP_DIR = _script_file.parent         # app/
ROOTFS_DIR = APP_DIR.parent           # rootfs/

# 服务配置目录（支持环境变量覆盖）
SERVICE_DIR = Path(os.getenv('SERVICE_DIR', '/etc/frpc'))
DATA_DIR = Path(os.getenv('DATA_DIR', '/data'))

# 确保目录存在
SERVICE_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

REMOTE_ASSISTANCE_FILE = SERVICE_DIR / "remote_assistance"
VISITOR_CODE_FILE = SERVICE_DIR / "visitor_code"
DEVICE_ID_FILE = DATA_DIR / "device_id.txt"

# 脚本路径
SCRIPT_DIR = APP_DIR # 兼容旧逻辑，脚本都在 app/ 下
COMMON_SH = APP_DIR / "common.sh" # 现在 common.sh 在 app/ 下

# ================= 认证配置 =================
# iEG认证服务地址
IEG_AUTH_BASE_URL = os.getenv('IEG_AUTH_BASE_URL', "http://127.0.0.1:22210")

# 云端服务地址
CLOUD_API_BASE_URL = "https://euhome.linklinkiot.com/sfsaas/api"
HEARTBEAT_API_URL = "https://euadmin.linklinkiot.com/frpserver/api/heartbeat"
FRPC_SERVER_URL = "https://euadmin.linklinkiot.com/frpserver/api/proxy"

# 本地认证凭证 (从环境变量)
AUTH_EMAIL = os.getenv('AUTH_EMAIL', '')
AUTH_PASSWORD = os.getenv('AUTH_PASSWORD', '')

# ================= Web配置 =================
SECRET_KEY = os.urandom(24)
PERMANENT_SESSION_LIFETIME = timedelta(hours=2)
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
TEMPLATES_DIR = APP_DIR / 'templates'
