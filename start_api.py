#!/usr/bin/env python3
"""
启动视频解析API服务器的便捷脚本
"""

import subprocess
import sys
import os

def start_server():
    """启动API服务器"""
    print("🚀 正在启动视频解析API服务器...")
    print("📍 服务地址: http://localhost:10010")
    print("📖 API文档: http://localhost:10010/docs")
    print("🔧 按 Ctrl+C 停止服务器")
    print()
    
    # 切换到api.py所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    api_file = os.path.join(script_dir, "api.py")
    
    # 检查文件是否存在
    if not os.path.exists(api_file):
        print(f"❌ 错误: 找不到 {api_file}")
        return
    
    try:
        # 启动服务器
        subprocess.run([sys.executable, api_file], check=True)
    except KeyboardInterrupt:
        print("\n👋 服务器已停止")
    except subprocess.CalledProcessError as e:
        print(f"❌ 启动失败: {e}")
    except FileNotFoundError:
        print("❌ 错误: 找不到python解释器")

if __name__ == "__main__":
    start_server()