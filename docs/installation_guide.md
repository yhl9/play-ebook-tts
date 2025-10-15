# TTS 应用程序安装指南

## 系统要求

### 最低要求
- **操作系统**: Windows 10/11, macOS 10.12+, Ubuntu 18.04+
- **Python版本**: Python 3.8 或更高版本
- **内存**: 4GB RAM (推荐 8GB+)
- **存储空间**: 2GB 可用空间
- **网络**: 用于下载语音模型和在线 TTS 服务

### 推荐配置
- **操作系统**: Windows 11, macOS 12+, Ubuntu 20.04+
- **Python版本**: Python 3.10 或更高版本
- **内存**: 8GB RAM 或更多
- **存储空间**: 5GB 可用空间
- **网络**: 稳定的网络连接

## 安装步骤

### 1. 环境准备

#### Windows 系统
```bash
# 检查 Python 版本
python --version

# 如果没有 Python，请从 https://python.org 下载安装
# 确保勾选 "Add Python to PATH"
```

#### macOS 系统
```bash
# 使用 Homebrew 安装 Python
brew install python

# 或从 https://python.org 下载安装包
```

#### Linux 系统
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip

# CentOS/RHEL
sudo yum install python3 python3-pip

# Arch Linux
sudo pacman -S python python-pip
```

### 2. 依赖安装

#### 安装 Python 依赖
```bash
# 进入项目目录
cd /path/to/tts-application

# 安装依赖包
pip install -r requirements.txt
```

#### 系统依赖

##### Windows 系统
- **SAPI 语音引擎**: 系统内置，无需额外安装
- **Visual C++ 运行库**: 用于编译某些 Python 包

##### macOS 系统
```bash
# 安装语音合成依赖
brew install espeak

# 安装音频处理依赖
brew install ffmpeg
```

##### Linux 系统
```bash
# Ubuntu/Debian
sudo apt install espeak espeak-data
sudo apt install ffmpeg

# CentOS/RHEL
sudo yum install espeak
sudo yum install ffmpeg

# Arch Linux
sudo pacman -S espeak
sudo pacman -S ffmpeg
```

### 3. 语音包配置

#### Edge TTS (在线引擎)
- **无需额外配置**: 自动使用微软在线服务
- **网络要求**: 需要稳定的网络连接
- **语言支持**: 100+ 种语言

#### Piper TTS (本地引擎)
```bash
# 创建模型目录
mkdir -p models/piper

# 下载中文语音模型 (示例)
# 应用程序会自动提示下载，或手动下载到 models/piper/ 目录
```

#### pyttsx3 (系统引擎)
- **Windows**: 使用系统内置 SAPI 语音
- **macOS**: 使用系统内置语音合成器
- **Linux**: 使用 espeak 语音引擎

### 4. 配置文件设置

#### 主配置文件 (config.json)
```json
{
  "general": {
    "theme": "purple",
    "language": 0
  },
  "tts": {
    "default_engine": "edge_tts",
    "default_voice": "zh-CN-XiaoxiaoNeural"
  },
  "advanced": {
    "log_level": "INFO",
    "debug_mode": false
  }
}
```

#### 引擎配置
- **引擎注册**: `configs/engines/registry.json`
- **引擎参数**: `configs/engine_parameters.json`
- **语音配置**: `configs/dicts/` 目录

### 5. 启动应用程序

#### 命令行启动
```bash
# 直接启动
python main.py

# 或使用启动脚本
python start_app.py
```

#### Windows 批处理
```batch
# 使用批处理文件
run_tts.bat

# 或启动无警告版本
start_without_warnings.bat
```

#### Linux/macOS 脚本
```bash
# 使用 shell 脚本
./start_app.sh

# 或直接运行
python main.py
```

## 验证安装

### 1. 功能测试
```bash
# 运行测试脚本
python -c "
from utils.log_manager import LogManager
from services.tts_service import TTSServiceFactory

# 测试日志系统
log_manager = LogManager()
logger = log_manager.get_logger('Test')
logger.info('日志系统正常')

# 测试 TTS 服务
factory = TTSServiceFactory()
print('TTS 服务初始化成功')
"
```

### 2. 语音测试
1. 启动应用程序
2. 选择 TTS 引擎
3. 点击"测试语音"按钮
4. 验证语音输出

### 3. 配置验证
```bash
# 检查配置文件
python -c "
import json
with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)
    print('配置文件格式正确')
    print(f'默认引擎: {config[\"tts\"][\"default_engine\"]}')
"
```

## 常见问题解决

### 1. Python 环境问题

#### 问题: Python 命令不存在
```bash
# Windows: 重新安装 Python 并勾选 "Add to PATH"
# macOS: 使用 Homebrew 安装
brew install python

# Linux: 安装 python3
sudo apt install python3
```

#### 问题: pip 命令不存在
```bash
# 安装 pip
python -m ensurepip --upgrade

# 或使用系统包管理器
# Ubuntu: sudo apt install python3-pip
# CentOS: sudo yum install python3-pip
```

### 2. 依赖安装问题

#### 问题: 某些包安装失败
```bash
# 升级 pip
pip install --upgrade pip

# 使用国内镜像源
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/

# 或使用 conda
conda install --file requirements.txt
```

#### 问题: 编译错误
```bash
# Windows: 安装 Visual Studio Build Tools
# macOS: 安装 Xcode Command Line Tools
xcode-select --install

# Linux: 安装开发工具
sudo apt install build-essential
```

### 3. 语音引擎问题

#### 问题: Edge TTS 连接失败
- 检查网络连接
- 验证防火墙设置
- 尝试使用 VPN

#### 问题: Piper TTS 模型加载失败
- 检查模型文件完整性
- 验证文件权限
- 重新下载模型

#### 问题: pyttsx3 语音不可用
- 检查系统语音设置
- 安装语音包
- 重启应用程序

### 4. 配置文件问题

#### 问题: 配置文件格式错误
```bash
# 验证 JSON 格式
python -c "
import json
try:
    with open('config.json', 'r', encoding='utf-8') as f:
        json.load(f)
    print('配置文件格式正确')
except json.JSONDecodeError as e:
    print(f'配置文件格式错误: {e}')
"
```

#### 问题: 配置项缺失
- 检查配置文件完整性
- 使用默认配置重新生成
- 参考文档修复配置

## 性能优化

### 1. 系统优化
- **内存管理**: 设置合适的内存限制
- **并发控制**: 限制同时处理的任务数量
- **缓存设置**: 启用适当的缓存机制

### 2. 网络优化
- **连接池**: 使用连接池减少连接开销
- **超时设置**: 设置合适的网络超时
- **重试机制**: 实现网络请求重试

### 3. 存储优化
- **模型缓存**: 启用模型缓存减少加载时间
- **临时文件**: 定期清理临时文件
- **日志管理**: 设置日志文件大小限制

## 卸载说明

### 1. 应用程序卸载
```bash
# 删除应用程序文件
rm -rf /path/to/tts-application

# 删除配置文件 (可选)
rm -rf ~/.config/tts-application
```

### 2. 依赖清理
```bash
# 卸载 Python 依赖
pip uninstall -r requirements.txt

# 清理缓存
pip cache purge
```

### 3. 系统清理
- **Windows**: 删除注册表项和系统文件
- **macOS**: 清理应用程序支持文件
- **Linux**: 删除用户配置和缓存文件

## 技术支持

### 获取帮助
1. **查看文档**: 阅读相关技术文档
2. **检查日志**: 查看应用程序日志文件
3. **社区支持**: 访问项目 GitHub 页面
4. **技术支持**: 联系开发团队

### 报告问题
1. **问题描述**: 详细描述遇到的问题
2. **环境信息**: 提供系统和环境信息
3. **日志文件**: 附上相关的日志文件
4. **复现步骤**: 提供问题复现步骤

---

*安装指南最后更新: 2024年10月*
