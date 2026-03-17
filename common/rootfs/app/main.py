import logging
import sys
import threading
import os
from flask import Flask
from werkzeug.serving import WSGIRequestHandler

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
    
    # 核心路径初始化逻辑：确保配置和数据目录存在
    try:
        config.SERVICE_DIR.mkdir(parents=True, exist_ok=True)
        config.DATA_DIR.mkdir(parents=True, exist_ok=True)
        logger.info(f"运行目录初始化成功: SERVICE_DIR={config.SERVICE_DIR}, DATA_DIR={config.DATA_DIR}")
    except Exception as e:
        logger.error(f"无法初始化运行目录: {e}")

    # 使用更新后的路径
    SERVICE_DIR = config.SERVICE_DIR
    DATA_DIR = config.DATA_DIR

    def startup_frpc():
        """在后台线程中启动 frpc 服务，等待 Flask 完全启动后执行"""
        import time
        time.sleep(2)  # 等待 Flask 应用启动

        config_file = SERVICE_DIR / "frpc.toml"
        if not config_file.exists():
            logger.info("frpc.toml 不存在，尝试自动注册...")
            from frpc_service import register_frpc_proxy
            if register_frpc_proxy():
                logger.info("代理自动注册成功")
            else:
                logger.error("代理自动注册失败，等待手动配置")

        if config_file.exists():
            logger.info("开始启动 frpc 服务...")
            if start_frpc(retry_count=3, retry_delay=2):
                logger.info("frpc 服务启动成功")
            else:
                logger.error("frpc 服务启动失败，请检查配置和日志")
        else:
            logger.info("frpc.toml 不存在，等待手动配置后启动 frpc...")

    # 启动 frpc 后台启动线程
    frpc_startup_thread = threading.Thread(target=startup_frpc, daemon=True)
    frpc_startup_thread.start()

    # 启动心跳线程
    heartbeat_thread = threading.Thread(target=heartbeat_loop, daemon=True)
    heartbeat_thread.start()

    # 启动 Flask 应用
    logger.info("启动 Web 服务端口 8888...")

    class CustomRequestHandler(WSGIRequestHandler):
        def log(self, type, message, *args):
            try:
                msg = f"{self.address_string()} - - {message % args}\n"
            except:
                msg = f"{self.address_string()} - - {message}\n"
            sys.stderr.write(msg)
            sys.stderr.flush()

    app.run(host='0.0.0.0', port=8888, debug=False, request_handler=CustomRequestHandler)
