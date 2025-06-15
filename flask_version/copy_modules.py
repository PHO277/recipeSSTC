#!/usr/bin/env python3
"""
自动复制原有模块到Flask目录
"""

import os
import shutil
import sys

def copy_modules():
    """复制原有模块"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    
    # 要复制的文件
    files_to_copy = [
        'mongodb_manager.py',
        'llm_interface.py', 
        'nutrition_analyzer.py'
    ]
    
    # 要复制的目录
    dirs_to_copy = [
        'components',
        'config', 
        'utils'
    ]
    
    print("📁 开始复制原有模块...")
    
    # 复制文件
    for filename in files_to_copy:
        src = os.path.join(parent_dir, filename)
        dst = os.path.join(current_dir, filename)
        
        if os.path.exists(src):
            shutil.copy2(src, dst)
            print(f"✅ 复制文件: {filename}")
        else:
            print(f"⚠️  文件不存在: {filename}")
    
    # 复制目录
    for dirname in dirs_to_copy:
        src = os.path.join(parent_dir, dirname)
        dst = os.path.join(current_dir, dirname)
        
        if os.path.exists(src):
            if os.path.exists(dst):
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
            print(f"✅ 复制目录: {dirname}")
        else:
            print(f"⚠️  目录不存在: {dirname}")
    
    print("🎉 模块复制完成!")
    print("\n📋 下一步:")
    print("1. 设置环境变量")
    print("2. 安装依赖: pip install -r requirements.txt")
    print("3. 运行应用: python integrated_app.py")

if __name__ == "__main__":
    copy_modules()
