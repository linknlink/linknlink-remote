import syslog
import threading
import os
from flask import Flask

from config import (
    SERVICE_DIR, TEMPLATES_DIR, 
    SECRET_KEY, PERMANENT_SESSION_LIFETIME, 
    SESSION_COOKIE_HTTPONLY, SESSION_COOKIE_SAMESITE
)
from frpc_service import start_frpc
from cloud_service import heartbeat_loop
from web_routes import web_bp

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
    # 确保配置目录存在
    SERVICE_DIR.mkdir(parents=True, exist_ok=True)
    
    # 启动时检查并启动 frpc
    # 这里可以添加逻辑：如果存在配置文件则启动 frpc，否则等待配置
    if (SERVICE_DIR / "frpc.toml").exists():
        start_frpc()
    else:
        syslog.syslog(syslog.LOG_INFO, "等待配置以启动 frpc...")

    # 启动心跳线程
    heartbeat_thread = threading.Thread(target=heartbeat_loop, daemon=True)
    heartbeat_thread.start()

    # 启动 Flask 应用
    # host='0.0.0.0' 允许外部访问
    # 端口保持为 8888 (用户要求的)
    app.run(host='0.0.0.0', port=8888, debug=False)
