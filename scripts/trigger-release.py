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
import glob
from pathlib import Path

# 配置
REPO = "linknlink/linknlink-remote"
TOKEN_ENV = "GITHUB_TOKEN"


def get_github_token():
    """
    获取 GitHub Token
    先从环境变量获取，如果本地有 *.token 文件，则读取文件中 token 进行覆盖
    """
    # 先从环境变量获取
    token = os.environ.get(TOKEN_ENV)
    
    # 获取脚本所在目录，然后找到项目根目录
    script_dir = Path(__file__).parent.absolute()
    project_root = script_dir.parent
    
    # 查找项目根目录下的 *.token 文件
    token_files = list(project_root.glob("*.token"))
    
    # 如果找到 token 文件，读取文件中的 token 覆盖环境变量
    if token_files:
        token_file = token_files[0]  # 使用第一个找到的文件
        try:
            with open(token_file, 'r') as f:
                file_token = f.read().strip()
            if file_token:
                token = file_token
                print(f"从文件读取 token: {token_file.name}", file=sys.stderr)
        except Exception as e:
            print(f"警告: 无法读取 token 文件 {token_file}: {e}", file=sys.stderr)
    
    return token


def main():
    # 获取版本号
    if len(sys.argv) < 2:
        print("错误: 请提供版本号")
        print(f"使用方法: {sys.argv[0]} <版本号>")
        print("例如: python3 scripts/trigger-release.py 1.0.1")
        sys.exit(1)
    
    version = sys.argv[1]
    
    # 获取 token
    token = get_github_token()
    if not token:
        print(f"错误: {TOKEN_ENV} 未设置")
        print("")
        print("请通过以下方式之一设置:")
        print(f"  1. 环境变量: export {TOKEN_ENV}=\"your_token_here\"")
        print("  2. 创建 *.token 文件: 在项目根目录创建 *.token 文件，内容为 token")
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

