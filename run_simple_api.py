#!/usr/bin/env python3
import subprocess
import sys
import os

def main():
    print("🚀 启动简化版视频解析API...")
    print("📍 服务地址: http://localhost:10010")
    print("🔧 按 Ctrl+C 停止服务器")
    print()
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    api_file = os.path.join(script_dir, "api_simple.py")
    
    try:
        subprocess.run([sys.executable, api_file], check=True)
    except KeyboardInterrupt:
        print("\n👋 服务器已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")

if __name__ == "__main__":
    main()