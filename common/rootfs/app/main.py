import logging
import sys
import threading
import os
from flask import Flask

from config import (
    SERVICE_DIR, DATA_DIR, TEMPLATES_DIR, 
    SECRET_KEY, PERMANENT_SESSION_LIFETIME, 
    SESSION_COOKIE_HTTPONLY, SESSION_COOKIE_SAMESITE
)
from frpc_service import start_frpc
from cloud_service import heartbeat_loop
from web_routes import web_bp

# 初始化日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

# 初始化 Flask 应用
app = Flask(__name__, template_folder=str(TEMPLATES_DIR))

# 配置 Flask
app.secret_key = SECRET_KEY
app.config['PERMANENT_SESSION_LIFETIME'] = PERMANENT_SESSION_LIFETIME
app.config['SESSION_COOKIE_HTTPONLY'] = SESSION_COOKIE_HTTPONLY
app.config['SESSION_COOKIE_SAMESITE'] = SESSION_COOKIE_SAMESITE

# 注册蓝图
app.register_blueprint(web_bp)

if __name__ == '__main__':
    # 延迟导入，确保顶层导入不触发环境副作用
    import config
    
    # 核心路径初始化逻辑（最优优化：失败则降级到本地目录运行）
    try:
        config.SERVICE_DIR.mkdir(parents=True, exist_ok=True)
        config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        logger.warning("默认路径权限不足，降级到当前目录 runtime 文件夹下运行...")
        runtime_root = config.APP_DIR.parent / "runtime"
        config.SERVICE_DIR = runtime_root / "etc"
        config.DATA_DIR = runtime_root / "data"
        
        config.SERVICE_DIR.mkdir(parents=True, exist_ok=True)
        config.DATA_DIR.mkdir(parents=True, exist_ok=True)
        
        # 同步更新依赖路径
        config.REMOTE_ASSISTANCE_FILE = config.SERVICE_DIR / "remote_assistance"
        config.VISITOR_CODE_FILE = config.SERVICE_DIR / "visitor_code"
        config.DEVICE_ID_FILE = config.DATA_DIR / "device_id.txt"

    # 使用更新后的路径
    SERVICE_DIR = config.SERVICE_DIR
    DATA_DIR = config.DATA_DIR
    
    # 启动时检查并启动 frpc
    config_file = SERVICE_DIR / "frpc.toml"
    if not config_file.exists():
        logger.info("frpc.toml 不存在，尝试自动注册...")
        from frpc_service import register_frpc_proxy
        if register_frpc_proxy():
            logger.info("代理自动注册成功")
        else:
            logger.error("代理自动注册失败，等待手动配置")

    if config_file.exists():
        start_frpc()
    else:
        logger.info("等待配置以启动 frpc...")

    # 启动心跳线程
    heartbeat_thread = threading.Thread(target=heartbeat_loop, daemon=True)
    heartbeat_thread.start()

    # 启动 Flask 应用
    logger.info("启动 Web 服务端口 8888...")
    app.run(host='0.0.0.0', port=8888, debug=False)
