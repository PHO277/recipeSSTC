#!/usr/bin/env python3
"""
快速启动脚本 - 一键运行完整应用
"""

import os
import subprocess
import sys
import time

def check_python_version():
    """检查Python版本"""
    if sys.version_info < (3, 8):
        print("❌ 需要Python 3.8或更高版本")
        sys.exit(1)
    print(f"✅ Python版本: {sys.version}")

def install_dependencies():
    """安装依赖"""
    print("📦 安装依赖包...")
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        print("✅ 依赖安装完成")
    except subprocess.CalledProcessError as e:
        print(f"❌ 依赖安装失败: {e}")
        return False
    return True

def copy_modules():
    """复制原有模块"""
    print("📁 复制原有模块...")
    try:
        import copy_modules
        copy_modules.copy_modules()
        return True
    except Exception as e:
        print(f"⚠️  模块复制失败: {e}")
        print("请手动复制原有模块文件")
        return False

def setup_environment():
    """设置环境变量"""
    env_file = '.env'
    if not os.path.exists(env_file):
        print("📝 创建环境变量文件...")
        with open(env_file, 'w') as f:
            f.write("""# 数据库配置
MONGODB_URI=mongodb://localhost:27017/recipe_app

# AI API配置 (请替换为真实的API密钥)
DEEPSEEK_API_KEY=demo_key
SILICONFLOW_API_KEY=demo_key

# Flask配置
SECRET_KEY=recipe_app_secret_2025
FLASK_ENV=development
""")
        print("✅ 环境变量文件已创建，请编辑.env文件添加真实的API密钥")
    
    # 加载环境变量
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ 环境变量已加载")
    except ImportError:
        print("⚠️  python-dotenv未安装，将使用默认配置")

def start_application():
    """启动应用"""
    print("\n🚀 启动Recipe App完整版...")
    print("📱 浏览器将自动打开 http://localhost:5000")
    print("🛑 按Ctrl+C停止服务器")
    print("="*50)
    
    try:
        # 延迟打开浏览器
        import threading
        import webbrowser
        
        def open_browser():
            time.sleep(3)
            webbrowser.open('http://localhost:5000')
        
        browser_thread = threading.Thread(target=open_browser)
        browser_thread.daemon = True
        browser_thread.start()
        
        # 启动Flask应用
        import integrated_app
        
    except KeyboardInterrupt:
        print("\n🛑 应用已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")

def main():
    """主函数"""
    print("""
    ╔══════════════════════════════════════════════════╗
    ║          🍳 Recipe App 快速启动工具              ║ 
    ║                                                  ║
    ║        完整集成版本 - 包含所有原有功能            ║
    ╚══════════════════════════════════════════════════╝
    """)
    
    # 检查Python版本
    check_python_version()
    
    # 安装依赖
    if not install_dependencies():
        return
    
    # 复制模块
    copy_modules()
    
    # 设置环境
    setup_environment()
    
    print("\n🎯 准备工作完成！")
    input("按回车键启动应用...")
    
    # 启动应用
    start_application()

if __name__ == "__main__":
    main()
