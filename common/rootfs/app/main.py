import logging
import sys
import threading
import os
import time
from flask import Flask

from config import (
    SERVICE_DIR, DATA_DIR, TEMPLATES_DIR, 
    SECRET_KEY, PERMANENT_SESSION_LIFETIME, 
    SESSION_COOKIE_HTTPONLY, SESSION_COOKIE_SAMESITE
)
from frpc_service import start_frpc
from cloud_service import heartbeat_loop, CLOUD_AUTH_INFO
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
    import config

    # 核心路径初始化
    try:
        config.SERVICE_DIR.mkdir(parents=True, exist_ok=True)
        config.DATA_DIR.mkdir(parents=True, exist_ok=True)
        logger.info(f"运行目录初始化成功: SERVICE_DIR={config.SERVICE_DIR}, DATA_DIR={config.DATA_DIR}")
    except Exception as e:
        logger.error(f"无法初始化运行目录: {e}")

    SERVICE_DIR = config.SERVICE_DIR
    DATA_DIR = config.DATA_DIR

    def wait_for_auth(timeout=120):
        """等待认证信息就绪，最多等待 timeout 秒"""
        logger.info("等待云端认证信息...")
        start = time.time()
        while time.time() - start < timeout:
            if CLOUD_AUTH_INFO.get('user_id') and CLOUD_AUTH_INFO.get('company_id'):
                logger.info(f"认证信息就绪: UserID={CLOUD_AUTH_INFO['user_id']}")
                return True
            time.sleep(3)
        logger.error(f"等待认证超时（{timeout}秒），跳过自动注册")
        return False

    def startup_frpc():
        """在后台线程中启动 frpc 服务"""
        # 如果 frpc.toml 已存在，直接启动，无需等待认证
        config_file = SERVICE_DIR / "frpc.toml"
        if config_file.exists():
            logger.info("frpc.toml 已存在，直接启动 frpc 服务...")
            if start_frpc(retry_count=3, retry_delay=2):
                logger.info("frpc 服务启动成功")
            else:
                logger.error("frpc 服务启动失败，请检查配置和日志")
            return

        # frpc.toml 不存在，需要先等待认证信息，再自动注册
        logger.info("frpc.toml 不存在，等待认证信息后自动注册...")
        if not wait_for_auth(timeout=120):
            logger.error("认证信息未就绪，无法自动注册，请通过 Web 界面手动配置")
            return

        from frpc_service import register_frpc_proxy
        logger.info("开始自动注册代理...")
        if register_frpc_proxy():
            logger.info("代理自动注册成功，启动 frpc 服务...")
            if start_frpc(retry_count=3, retry_delay=2):
                logger.info("frpc 服务启动成功")
            else:
                logger.error("frpc 服务启动失败，请检查配置和日志")
        else:
            logger.error("代理自动注册失败，请通过 Web 界面手动配置")

    # 先启动心跳线程（它负责获取认证信息）
    heartbeat_thread = threading.Thread(target=heartbeat_loop, daemon=True)
    heartbeat_thread.start()
    logger.info("心跳线程已启动")

    # 再启动 frpc 后台启动线程
    frpc_startup_thread = threading.Thread(target=startup_frpc, daemon=True)
    frpc_startup_thread.start()
    logger.info("frpc 自启动线程已启动")

    # 启动 Flask 应用（使用 waitress 生产级 WSGI 服务器）
    logger.info("启动 Web 服务端口 8888...")

    from waitress import serve
    serve(app, host='0.0.0.0', port=8888)

