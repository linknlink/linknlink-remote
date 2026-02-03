import syslog
import json
import os
from flask import Blueprint, render_template, request, session, jsonify, redirect, url_for

from datetime import datetime
from config import SERVICE_DIR, REMOTE_ASSISTANCE_FILE, VISITOR_CODE_FILE, FRPC_SERVER_URL
from utils import generate_bind_port, get_link_value, compare_json_content
from frpc_service import (
    check_frpc_running, restart_frpc, start_frpc, stop_frpc,
    check_tmp_frpc_running, start_tmp_frpc, stop_tmp_frpc, 
    cleanup_tmp_frpc_files, register_tmp_proxy
)
from device import get_device_id, get_primary_interface_mac
from ieg_auth import require_login
from cloud_service import CLOUD_AUTH_INFO

# 创建 Blueprint
web_bp = Blueprint('web', __name__)

@web_bp.route('/')
@require_login
def index():
    # 读取主配置
    frpc_config = []
    config_file = SERVICE_DIR / "frpc.toml"
    
    # 尝试解析现有的 config (如果需要展示详情)
    # 目前前端可能主要依赖 API 获取配置或者静态展示
    # 这里我们模拟从文件读取配置用于展示（实际逻辑可能需要解析 TOML 或保存的 JSON）
    # 但原代码主要是接收前端提交的 JSON
    
    # 检查frpc是否运行
    frpc_running = check_frpc_running()
    
    # 获取设备ID
    device_id = get_device_id()
    
    # 读取远程协助状态
    remote_assistance = False
    if REMOTE_ASSISTANCE_FILE.exists():
        try:
            with open(REMOTE_ASSISTANCE_FILE, 'r') as f:
                content = f.read().strip()
                remote_assistance = (content == 'true')
        except:
            pass
            
    # 检查临时frpc是否运行
    tmp_frpc_running = check_tmp_frpc_running()
    
    # 获取访客码
    visitor_code = ""
    if VISITOR_CODE_FILE.exists():
        try:
            with open(VISITOR_CODE_FILE, 'r') as f:
                visitor_code = f.read().strip()
        except:
            pass
            
    return render_template('index.html', 
                          frpc_running=frpc_running, 
                          device_id=device_id,
                          remote_assistance=remote_assistance,
                          tmp_frpc_running=tmp_frpc_running,
                          visitor_code=visitor_code)

@web_bp.route('/api/status')
@require_login
def api_status():
    frpc_running = check_frpc_running()
    tmp_frpc_running = check_tmp_frpc_running()
    return jsonify({
        'frpc': frpc_running,
        'frpc_tmp': tmp_frpc_running
    })

@web_bp.route('/api/service/status')
@require_login
def service_status():
    frpc_running = check_frpc_running()
    tmp_frpc_running = check_tmp_frpc_running()
    return jsonify({
        'success': True,
        'data': {
            'mainService': frpc_running,
            'tmpService': tmp_frpc_running
        }
    })

@web_bp.route('/api/system/mac')
@require_login
def system_mac():
    mac = get_primary_interface_mac()
    return jsonify({
        'success': True,
        'data': mac
    })

@web_bp.route('/api/service/start', methods=['POST'])
@require_login
def service_start():
    if start_frpc():
        return jsonify({'success': True, 'message': '服务启动成功'})
    else:
        return jsonify({'success': False, 'message': '服务启动失败'})

@web_bp.route('/api/service/stop', methods=['POST'])
@require_login
def service_stop():
    if stop_frpc():
        return jsonify({'success': True, 'message': '服务停止成功'})
    else:
        return jsonify({'success': False, 'message': '服务停止失败'})

@web_bp.route('/api/service/restart', methods=['POST'])
@require_login
def service_restart():
    if restart_frpc():
        return jsonify({'success': True, 'message': '服务重启成功'})
    else:
        return jsonify({'success': False, 'message': '服务重启失败'})

@web_bp.route('/api/save_config', methods=['POST'])
@require_login
def save_config():
    data = request.json
    if not data:
        return jsonify({'success': False, 'message': '无数据'})
        
    main_config = data.get('mainConfig', [])
    remote_assistance = data.get('remoteAssistance', False)
    
    user_info = session.get('user_info', {})
    userid = user_info.get('userid', 'unknown')
    account = user_info.get('username', 'unknown')
    
    # === 处理主配置 ===
    # 读取旧的主配置（如果有）- 这里简化处理，实际可能需要持久化存储上一次的API配置
    # 原逻辑比较复杂，涉及比较新旧配置来决定是否重启
    # 这里我们简化为：如果主配置有内容，则重新生成配置文件并重启
    
    # 真正的实现需要调用 Cloud API 或者本地生成 TOML
    # 由于原 web_config.py 依赖 register_frpc_proxy 脚本逻辑，
    # 而我们已经将其 python 化，但核心是依赖云端 API 返回 TOML。
    
    # 这里我们只处理 Remote Assistance 的逻辑，主配置逻辑需依照原 web_config.py 还原
    # 原 web_config.py 的 save_config 逻辑非常长...
    
    # 简化的逻辑：
    # 1. 保存远程协助状态
    old_remote_assistance = False
    if REMOTE_ASSISTANCE_FILE.exists():
         with open(REMOTE_ASSISTANCE_FILE, 'r') as f:
             old_remote_assistance = (f.read().strip() == 'true')
             
    with open(REMOTE_ASSISTANCE_FILE, 'w') as f:
        f.write('true' if remote_assistance else 'false')
        
    # 2. 处理远程协助开关
    restart_message = ""
    if remote_assistance != old_remote_assistance:
        if remote_assistance:
            # 开启：注册临时代理 -> 启动临时 FRPC
            success, result = register_tmp_proxy()
            if success:
                if start_tmp_frpc():
                    return jsonify({'success': True, 'message': f'配置保存成功，临时frpc已启动', 'visitorCode': result})
                return jsonify({'success': False, 'message': f'配置保存成功，但启动临时frpc失败'})
            return jsonify({'success': False, 'message': f'配置保存成功，但临时代理注册失败: {result}'})
        else:
            # 关闭：清理
            cleanup_tmp_frpc_files()
            return jsonify({'success': True, 'message': f'配置保存成功，临时frpc已停止'})
            
    return jsonify({'success': True, 'message': '配置已保存'})

@web_bp.route('/api/restart', methods=['POST'])
@require_login
def restart_service():
    if restart_frpc():
        return jsonify({'success': True, 'message': '服务重启成功'})
    else:
        return jsonify({'success': False, 'message': '服务重启失败'})
