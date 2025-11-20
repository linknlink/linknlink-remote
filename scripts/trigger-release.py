#!/usr/bin/env python3
"""
触发 Release Workflow 的 Python 脚本
使用方法: python3 scripts/trigger-release.py [版本号]
例如: python3 scripts/trigger-release.py 1.0.1
"""

import os
import sys
import json
import requests
import re

# 配置
REPO = "linknlink/linknlink-remote"
TOKEN_ENV = "GITHUB_TOKEN"


def main():
    # 获取版本号
    if len(sys.argv) < 2:
        print("错误: 请提供版本号")
        print(f"使用方法: {sys.argv[0]} <版本号>")
        print("例如: python3 scripts/trigger-release.py 1.0.1")
        sys.exit(1)
    
    version = sys.argv[1]
    
    # 获取 token
    token = os.environ.get(TOKEN_ENV)
    if not token:
        print(f"错误: {TOKEN_ENV} 环境变量未设置")
        print("")
        print("请设置 GITHUB_TOKEN 环境变量:")
        print(f'  export {TOKEN_ENV}="your_token_here"')
        print("")
        print("或者在使用时直接指定:")
        print(f'  {TOKEN_ENV}="your_token" python3 {sys.argv[0]} {version}')
        sys.exit(1)
    
    # 验证版本格式
    if not re.match(r'^\d+\.\d+\.\d+', version):
        print(f"警告: 版本号格式可能不正确 (建议使用: x.y.z, 例如: 1.0.1)")
        confirm = input("是否继续? (y/N): ")
        if confirm.lower() != 'y':
            sys.exit(1)
    
    # 准备请求
    url = f"https://api.github.com/repos/{REPO}/dispatches"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"token {token}",
        "Content-Type": "application/json"
    }
    data = {
        "event_type": "release",
        "client_payload": {
            "version": version
        }
    }
    
    # 发送请求
    print("正在触发 Release Workflow...")
    print(f"仓库: {REPO}")
    print(f"版本: {version}")
    print("")
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        
        if response.status_code == 204:
            print("✓ Workflow 触发成功!")
            print("")
            print("请访问以下链接查看 workflow 运行状态:")
            print(f"  https://github.com/{REPO}/actions")
            sys.exit(0)
        else:
            print(f"✗ 触发失败 (HTTP {response.status_code})")
            if response.text:
                try:
                    error_data = response.json()
                    print(f"错误信息: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
                except:
                    print(f"错误信息: {response.text}")
            sys.exit(1)
    
    except requests.exceptions.RequestException as e:
        print(f"✗ 请求失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

