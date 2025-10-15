#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动应用程序
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 首先预加载 Piper TTS，避免 PyQt6 的兼容性问题
try:
    from utils.piper_preloader import PIPER_AVAILABLE, get_piper_status
    print("✓ Piper TTS 预加载成功")
except Exception as e:
    print(f"⚠️ Piper TTS 预加载失败: {e}")
    print("Piper TTS 功能将不可用，但其他 TTS 引擎仍可正常使用")

def check_dependencies():
    """检查依赖"""
    missing_deps = []
    
    try:
        import PyQt6
    except ImportError:
        missing_deps.append("PyQt6")
    
    try:
        import edge_tts
    except ImportError:
        missing_deps.append("edge-tts")
    
    try:
        import pyttsx3
    except ImportError:
        missing_deps.append("pyttsx3")
    
    try:
        import pydub
    except ImportError:
        missing_deps.append("pydub")
    
    if missing_deps:
        print("缺少以下依赖包:")
        for dep in missing_deps:
            print(f"  - {dep}")
        print("\n请运行: pip install -r requirements.txt")
        return False
    
    return True

def main():
    """主函数"""
    print("电子书生成音频工具 v1.0.0")
    print("=" * 40)
    
    # 检查依赖
    if not check_dependencies():
        sys.exit(1)
    
    print("依赖检查通过")
    print("正在启动应用程序...")
    
    try:
        from main import main as app_main
        app_main()
    except Exception as e:
        print(f"应用程序启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
