#!/usr/bin/env python3
"""
Recipe App Flask Version - Startup Script
Team Internal Build - Desktop App Ready
"""

import os
import sys
import threading
import time
import webbrowser
from flask_app import app

def print_banner():
    """打印启动横幅"""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                     🍳 RECIPE APP FLASK                     ║
    ║                                                              ║
    ║                   Team Internal Version                      ║
    ║                Desktop Application Ready                     ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def check_dependencies():
    """检查必要的依赖"""
    print("🔍 Checking dependencies...")
    
    required_modules = [
        'flask', 'requests', 'PIL', 'openai', 'pymongo'
    ]
    
    missing_modules = []
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"  ✅ {module}")
        except ImportError:
            missing_modules.append(module)
            print(f"  ❌ {module}")
    
    if missing_modules:
        print(f"\n⚠️  Missing modules: {', '.join(missing_modules)}")
        print("📦 Please run: pip install -r requirements.txt")
        return False
    
    print("✅ All dependencies satisfied!")
    return True

def open_browser():
    """延迟打开浏览器"""
    time.sleep(2)  # 等待服务器启动
    webbrowser.open('http://localhost:5000')

def print_startup_info():
    """打印启动信息"""
    print("\n🚀 Starting Recipe App Flask Server...")
    print("📋 Server Information:")
    print("   • URL: http://localhost:5000")
    print("   • Environment: Development")
    print("   • Auto-reload: Enabled")
    print("   • Debug mode: Enabled")
    print("\n🔧 Available Features:")
    print("   • 🤖 AI Recipe Generation")
    print("   • 👤 User Authentication")
    print("   • 📊 Recipe Statistics")
    print("   • 💾 Local Recipe Storage")
    print("   • 🌍 Multi-language Support")
    print("\n📱 Desktop App Ready:")
    print("   • Ready for Electron packaging")
    print("   • Responsive design included")
    print("   • Offline capabilities built-in")
    
def print_team_info():
    """打印团队信息"""
    print("\n👥 Team Internal Build")
    print("   • Version: 1.0.0-alpha")
    print("   • Build Date: 2025-06-15")
    print("   • Target: Desktop Application")
    print("   • Status: Ready for Testing")

def main():
    """主启动函数"""
    print_banner()
    
    # 检查依赖
    if not check_dependencies():
        sys.exit(1)
    
    # 打印启动信息
    print_startup_info()
    print_team_info()
    
    print("\n" + "="*60)
    print("🌐 Opening browser automatically...")
    print("🛑 Press Ctrl+C to stop the server")
    print("="*60 + "\n")
    
    # 在单独线程中打开浏览器
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    try:
        # 启动Flask应用
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=True,
            use_reloader=True,
            threaded=True
        )
    except KeyboardInterrupt:
        print("\n\n🛑 Server stopped by user")
        print("👋 Thank you for using Recipe App!")
    except Exception as e:
        print(f"\n❌ Server error: {e}")
        print("🔧 Please check the logs and try again")

if __name__ == "__main__":
    main()
