import syslog
import json
import os
from flask import Blueprint, render_template, request, session, jsonify, redirect, url_for

from datetime import datetime
from config import REMOTE_ASSISTANCE_FILE, VISITOR_CODE_FILE, FRPC_SERVER_URL, SCRIPT_DIR
import config
from utils import generate_bind_port, get_link_value, compare_json_content
from frpc_service import (
    check_frpc_running, restart_frpc, start_frpc, stop_frpc,
    check_tmp_frpc_running, start_tmp_frpc, stop_tmp_frpc, 
    cleanup_tmp_frpc_files, register_tmp_proxy, register_frpc_proxy
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
    config_file = config.SERVICE_DIR / "frpc.toml"
    
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

@web_bp.route('/api/config/main')
@require_login
def get_config_main():
    """获取主配置"""
    config_file = config.SERVICE_DIR / "register_proxy.json"
    
    # 如果文件不存在，尝试从 conf 目录（只读模板）加载，或者返回空
    if not config_file.exists():
        template_file = SCRIPT_DIR / "conf" / "register_proxy.json"
        if template_file.exists():
            try:
                with open(template_file, 'r') as f:
                    content = json.load(f)
            except:
                content = []
        else:
            content = []
    else:
        try:
            with open(config_file, 'r') as f:
                content = json.load(f)
        except:
             content = []
             
    # 直接返回内容，因为文件格式现在已经与前端一致
    return jsonify({'success': True, 'data': content})

@web_bp.route('/api/config/tmp')
@require_login
def get_config_tmp():
    """获取临时配置"""
    config_file = config.SERVICE_DIR / "register_proxy_tmp.json"
    
    if not config_file.exists():
        template_file = SCRIPT_DIR / "conf" / "register_proxy_tmp.json"
        if template_file.exists():
            try:
                with open(template_file, 'r') as f:
                    content = json.load(f)
            except:
                content = []
        else:
             content = []
    else:
        try:
            with open(config_file, 'r') as f:
                content = json.load(f)
        except:
            content = []
            
    # 直接返回内容
    return jsonify({'success': True, 'data': content})

@web_bp.route('/api/config/remote-assistance')
@require_login
def get_remote_assistance():
    """获取远程协助状态"""
    enabled = False
    if REMOTE_ASSISTANCE_FILE.exists():
        try:
            with open(REMOTE_ASSISTANCE_FILE, 'r') as f:
                enabled = (f.read().strip() == 'true')
        except:
            pass
    return jsonify({'success': True, 'data': enabled})

@web_bp.route('/api/config/visitor-code')
@require_login
def get_visitor_code():
    """获取访客码"""
    code = ""
    if VISITOR_CODE_FILE.exists():
        try:
            with open(VISITOR_CODE_FILE, 'r') as f:
                code = f.read().strip()
        except:
            pass
    return jsonify({'success': True, 'data': code})

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
    tmp_config_data = data.get('tmpConfig', [])
    remote_assistance = data.get('remoteAssistance', False)
    
    # 1. 保存主配置到 register_proxy.json (直接保存前端传来的格式)
    # 前端格式: [{"serviceName": "...", "localPort": 123, "bindPort": 456, "link": true}, ...]
    try:
        # 做一些基本的类型转换，确保端口是数字
        cleaned_main_config = []
        for item in main_config:
            try:
                local_port = int(item.get('localPort', 0))
                bind_port = int(item.get('bindPort', 0))
                item['localPort'] = local_port
                item['bindPort'] = bind_port
                cleaned_main_config.append(item)
            except:
                continue
                
        with open(config.SERVICE_DIR / "register_proxy.json", 'w') as f:
            json.dump(cleaned_main_config, f, indent=4)
        
        # 调用注册函数同步配置到云端并重启frpc
        # register_frpc_proxy 内部会处理格式转换
        from frpc_service import register_frpc_proxy
        if register_frpc_proxy():
            restart_frpc()
            msg_suffix = "主服务配置已更新。"
        else:
             msg_suffix = "主服务配置更新失败（云端同步失败）。"
             
    except Exception as e:
        syslog.syslog(syslog.LOG_ERR, f"Save main config failed: {str(e)}")
        return jsonify({'success': False, 'message': f'保存主配置失败: {str(e)}'})

    # 2. 保存临时配置到 register_proxy_tmp.json
    try:
        cleaned_tmp_config = []
        for item in tmp_config_data:
            try:
                local_port = int(item.get('localPort', 0))
                bind_port = int(item.get('bindPort', 0))
                item['localPort'] = local_port
                item['bindPort'] = bind_port
                cleaned_tmp_config.append(item)
            except:
                continue
                
        with open(config.SERVICE_DIR / "register_proxy_tmp.json", 'w') as f:
            json.dump(cleaned_tmp_config, f, indent=4)
    except Exception as e:
        syslog.syslog(syslog.LOG_ERR, f"Save tmp config failed: {str(e)}")

    # 3. 保存远程协助状态
    old_remote_assistance = False
    if REMOTE_ASSISTANCE_FILE.exists():
         with open(REMOTE_ASSISTANCE_FILE, 'r') as f:
             old_remote_assistance = (f.read().strip() == 'true')
             
    with open(REMOTE_ASSISTANCE_FILE, 'w') as f:
        f.write('true' if remote_assistance else 'false')
        
    visitor_code_msg = ""
    if remote_assistance != old_remote_assistance:
        if remote_assistance:
            # 开启
            success, result = register_tmp_proxy()
            if success:
                if start_tmp_frpc():
                    visitor_code_msg = f" 临时服务已启动，访客码: {result}"
                else:
                    visitor_code_msg = " 临时服务启动失败"
            else:
                visitor_code_msg = f" 临时服务注册失败: {result}"
        else:
            # 关闭
            cleanup_tmp_frpc_files()
            visitor_code_msg = " 临时服务已停止"
    elif remote_assistance and cleaned_tmp_config: 
        # 如果配置有变，尝试重新注册
        success, result = register_tmp_proxy()
        if success:
             stop_tmp_frpc()
             start_tmp_frpc()
             visitor_code_msg = " 临时服务配置已更新"
            
    return jsonify({'success': True, 'message': f'配置保存成功。{msg_suffix}{visitor_code_msg}'})

@web_bp.route('/api/restart', methods=['POST'])
@require_login
def restart_service():
    if restart_frpc():
        return jsonify({'success': True, 'message': '服务重启成功'})
    else:
        return jsonify({'success': False, 'message': '服务重启失败'})
