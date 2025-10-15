"""
Piper TTS 预加载模块
用于在导入 PyQt6 之前预加载 Piper TTS，避免 DLL 兼容性问题
"""

import sys
import os
import warnings
from pathlib import Path

# 抑制 onnxruntime 警告
warnings.filterwarnings("ignore", category=UserWarning, module="onnxruntime")

# 设置 DLL 搜索路径
piper_models_dir = os.path.join(os.getcwd(), "models", "piper")
if os.path.exists(piper_models_dir):
    if piper_models_dir not in sys.path:
        sys.path.insert(0, piper_models_dir)
    os.environ['PATH'] = piper_models_dir + os.pathsep + os.environ.get('PATH', '')

# 在 PyInstaller 环境中设置 DLL 路径
if getattr(sys, 'frozen', False):
    # 打包后的环境
    base_path = Path(sys._MEIPASS)
    onnxruntime_dll_path = base_path / "onnxruntime" / "capi"
    if onnxruntime_dll_path.exists():
        os.environ['PATH'] = str(onnxruntime_dll_path) + os.pathsep + os.environ.get('PATH', '')
        print(f"[INFO] 设置 onnxruntime DLL 路径: {onnxruntime_dll_path}")

# 预加载 Piper TTS
PIPER_AVAILABLE = False
PiperVoice = None
SynthesisConfig = None

# 在 PyInstaller 打包环境中跳过 Piper TTS 导入
if getattr(sys, 'frozen', False):
    print("[INFO] 检测到 PyInstaller 打包环境，跳过 Piper TTS 导入以避免 DLL 冲突")
    print("Piper TTS 功能将不可用，但其他 TTS 引擎仍可正常使用")
else:
    try:
        # 先尝试导入 onnxruntime
        import onnxruntime
        print(f"[INFO] onnxruntime 版本: {onnxruntime.__version__}")
        
        # 然后导入 piper
        from piper import PiperVoice, SynthesisConfig
        PIPER_AVAILABLE = True
        print("[OK] Piper TTS 全局预加载成功")
    except ImportError as e:
        print(f"[WARN] Piper TTS 导入失败: {e}")
        print("Piper TTS 功能将不可用，但其他 TTS 引擎仍可正常使用")
    except Exception as e:
        print(f"[WARN] Piper TTS 全局预加载失败: {e}")
        print("Piper TTS 功能将不可用，但其他 TTS 引擎仍可正常使用")

def get_piper_status():
    """获取 Piper TTS 状态"""
    return {
        'available': PIPER_AVAILABLE,
        'voice_class': PiperVoice,
        'config_class': SynthesisConfig
    }
