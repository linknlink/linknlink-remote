import json
import os
import re
import logging
import sys
from flask import Blueprint, render_template, request, session, jsonify, redirect, url_for

from datetime import datetime
from config import REMOTE_ASSISTANCE_FILE, VISITOR_CODE_FILE, SCRIPT_DIR
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

# 配置日志输出到终端
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

# 创建 Blueprint
web_bp = Blueprint('web', __name__)

@web_bp.before_request
def before_request_logging():
    """在请求处理前记录日志"""
    # 仅对 API 接口进行日志记录 (以 /api/ 开头的路径)
    if request.path.startswith('/api/'):
        log_msg = f"API Request: {request.method} {request.path}"
        if request.args:
            log_msg += f", Args: {json.dumps(request.args.to_dict())}"
        if request.is_json:
            # 避免记录过大的 payload 或敏感数据，这里做个简单截断
            body = request.get_json(silent=True)
            if body:
                body_str = json.dumps(body)
                if len(body_str) > 500:
                    body_str = body_str[:500] + "..."
                log_msg += f", Body: {body_str}"
        logger.info(log_msg)

@web_bp.after_request
def after_request_logging(response):
    """在请求处理后记录日志"""
    if request.path.startswith('/api/'):
        status_code = response.status_code
        log_msg = f"API Response: {request.method} {request.path}, Status: {status_code}"
        
        # 如果是 JSON 响应，记录数据概览
        if response.is_json:
            try:
                data = response.get_json()
                if isinstance(data, dict):
                    # 摘取关键字段
                    summary = {k: v for k, v in data.items() if k in ['success', 'message', 'data']}
                    # 对 data 字段进一步缩减
                    if 'data' in summary and isinstance(summary['data'], (list, dict)) and len(json.dumps(summary['data'])) > 200:
                        summary['data'] = "..."
                    log_msg += f", Result: {json.dumps(summary, ensure_ascii=False)}"
            except:
                pass
                
        logger.info(log_msg)
    return response


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

def _ensure_config_consistency():
    """
    检查配置一致性，并在必要时触发自动注册
    返回: True (配置正常或修复成功), False (修复失败)
    """
    need_register = False
    config_file = config.SERVICE_DIR / "frpc.toml"
    
    # 1. 检查文件是否存在
    if not config_file.exists():
        syslog.syslog(syslog.LOG_INFO, "frpc.toml not found, triggering registration...")
        need_register = True
    else:
        # 2. 检查配置一致性 (对比 JSON 中的 bindPort 和 TOML 中的 remotePort)
        try:
            # 读取 JSON 配置
            json_config_file = config.SERVICE_DIR / "register_proxy.json"
            if not json_config_file.exists():
                # JSON 都不存在，可能还是初始状态，尝试注册看看能否恢复模板
                need_register = True
            else:
                with open(json_config_file, 'r') as f:
                    proxy_list = json.load(f)
                    
                # 提取 JSON 中所有的 bindPort (预期值)
                expected_ports = set()
                for item in proxy_list:
                    if str(item.get('bindPort')):
                        expected_ports.add(str(item.get('bindPort')))
                        
                if expected_ports:
                    # 读取 TOML 配置
                    with open(config_file, 'r') as f:
                        toml_content = f.read()
                        
                    # 提取 TOML 中所有的 remotePort (实际值)
                    # 匹配 pattern: remotePort = 12345
                    actual_ports = set(re.findall(r'remotePort\s*=\s*(\d+)', toml_content))
                    
                    # 检查预期端口是否都在实际配置中
                    # 注意：只检查是否存在，不一定一一对应，因为TOML可能包含其他默认配置，但JSON中的一定要有
                    if not expected_ports.issubset(actual_ports):
                        syslog.syslog(syslog.LOG_WARNING, f"Config mismatch detected. Expected: {expected_ports}, Actual: {actual_ports}. Triggering registration...")
                        need_register = True
        except Exception as e:
            syslog.syslog(syslog.LOG_ERR, f"Config consistency check failed: {str(e)}")
            # 出错保守起见不强制注册，以免陷入死循环，或者可以根据策略决定
            pass

    # 3. 如果需要，执行注册
    if need_register:
        syslog.syslog(syslog.LOG_INFO, "Executing auto-registration due to missing or inconsistent config...")
        if not register_frpc_proxy():
            return False
            
    return True

@web_bp.route('/api/service/start', methods=['POST'])
@require_login
def service_start():
    if not _ensure_config_consistency():
        return jsonify({'success': False, 'message': '服务启动失败：配置自动修正失败，请检查日志'})
        
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
    if not _ensure_config_consistency():
        return jsonify({'success': False, 'message': '服务重启失败：配置自动修正失败，请检查日志'})
        
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

@web_bp.route('/api/config/reset/main', methods=['POST'])
@require_login
def reset_config_main():
    """重置主配置为默认"""
    try:
        template_file = SCRIPT_DIR / "conf" / "register_proxy.json"
        target_file = config.SERVICE_DIR / "register_proxy.json"
        
        if template_file.exists():
            # 读取模板
            with open(template_file, 'r') as f:
                content = json.load(f)
            
            # 写入目标
            with open(target_file, 'w') as f:
                json.dump(content, f, indent=4)
                
            # 重启服务使得配置生效
            if register_frpc_proxy():
                restart_frpc()
                return jsonify({'success': True, 'message': '主配置已重置并生效'})
            else:
                return jsonify({'success': False, 'message': '主配置重置成功但同步失败'})
        else:
            # 如果没有模板，创建一个空的列表
            with open(target_file, 'w') as f:
                json.dump([], f, indent=4)
            restart_frpc()
            return jsonify({'success': True, 'message': '主配置已清空'})

    except Exception as e:
        syslog.syslog(syslog.LOG_ERR, f"Reset main config failed: {str(e)}")
        return jsonify({'success': False, 'message': f'重置主配置失败: {str(e)}'})

@web_bp.route('/api/config/reset/tmp', methods=['POST'])
@require_login
def reset_config_tmp():
    """重置临时配置为默认"""
    try:
        template_file = SCRIPT_DIR / "conf" / "register_proxy_tmp.json"
        target_file = config.SERVICE_DIR / "register_proxy_tmp.json"
        
        if template_file.exists():
            with open(template_file, 'r') as f:
                content = json.load(f)
            with open(target_file, 'w') as f:
                json.dump(content, f, indent=4)
        else:
            with open(target_file, 'w') as f:
                json.dump([], f, indent=4)
                
        return jsonify({'success': True, 'message': '临时配置已重置'})

    except Exception as e:
        syslog.syslog(syslog.LOG_ERR, f"Reset tmp config failed: {str(e)}")
        return jsonify({'success': False, 'message': f'重置临时配置失败: {str(e)}'})
