# 电子书生成音频工具
Generate audio from the e-book to make it a pleasure to listen to the novel.从电子书生成音频，实现听小说的自由
基于Python + PyQt6开发的桌面应用程序，用于将电子书文本转换为高质量音频文件。

**语言**: [English](README.md) | [中文](README_cn.md)

## 功能特性

### 核心功能
- **多格式支持**: 支持TXT、PDF、EPUB、DOCX等电子书格式
- **智能文本处理**: 自动清理文本、识别章节、智能分割
- **多种TTS引擎**: 支持Edge TTS和pyttsx3语音合成引擎
- **语音参数调节**: 支持语速、音调、音量等参数调节
- **批量处理**: 支持多文件批量转换，队列管理
- **音频格式**: 支持MP3、WAV等主流音频格式

### 界面特性
- **现代化UI**: 基于PyQt6的现代化界面设计
- **响应式布局**: 支持窗口大小调整
- **主题支持**: 支持明暗主题切换
- **多语言支持**: 界面语言本地化

## 技术架构

### 架构模式
采用MVC (Model-View-Controller) 架构模式，结合分层架构设计：

- **表示层 (UI Layer)**: PyQt6界面组件
- **控制层 (Controller Layer)**: 业务逻辑控制器
- **业务层 (Service Layer)**: 核心业务服务
- **数据层 (Model Layer)**: 数据模型定义

### 技术栈
- **前端框架**: PyQt6
- **编程语言**: Python 3.12
- **文本处理**: PyPDF2, python-docx, ebooklib
- **音频处理**: pydub, ffmpeg-python
- **TTS引擎**: edge-tts, pyttsx3
- **配置管理**: configparser
- **日志系统**: logging

## 安装说明

### 环境要求
- Python 3.12+
- Windows 10/11 或 Linux
- 内存: 最低4GB，推荐8GB以上
- 存储: 至少1GB可用空间

### 安装步骤

1. **克隆项目**
```bash
git clone <repository-url>
cd play-ebook-tts-main
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **运行程序**
```bash
python main.py
```

## 使用说明

### 基本使用流程

1. **导入文件**
   - 点击"导入文件"按钮或直接拖拽文件到界面
   - 支持的文件格式：TXT、PDF、EPUB、DOCX

2. **文本处理**
   - 在"文本处理"标签页中预览和编辑文本
   - 选择分割方式：按长度、按章节、按段落
   - 调整分割参数

3. **语音设置**
   - 在"语音设置"标签页中选择TTS引擎
   - 选择语音类型和语言
   - 调节语速、音调、音量参数
   - 使用"测试语音"功能预览效果

4. **生成音频**
   - 点击"开始处理"按钮开始生成音频
   - 在"批量处理"标签页中管理处理队列
   - 查看处理进度和状态

5. **导出结果**
   - 音频文件将保存到指定的输出目录
   - 支持多种音频格式输出

### 高级功能

#### 批量处理
- 添加多个文件到处理队列
- 设置不同的语音参数
- 监控处理进度和状态
- 支持暂停、恢复、停止操作

#### 配置管理
- 保存用户偏好设置
- 导入/导出配置文件
- 主题和语言切换
- 性能参数调节

## 项目结构

```
src/
├── main.py                 # 应用程序入口
├── requirements.txt        # 依赖包列表
├── config.json            # 配置文件
├── README.md              # 项目说明
├── docs/                  # 技术文档
│   ├── README.md          # 文档索引
│   ├── installation_guide.md      # 安装指南
│   ├── piper_models_guide.md      # Piper模型下载指南
│   ├── pyttsx3_voices_guide.md   # pyttsx3语音包指南
│   └── tts_engines_comparison.md  # TTS引擎对比指南
├── ui/                    # 界面层
│   ├── main_window.py     # 主窗口
│   ├── file_manager.py    # 文件管理
│   ├── text_processor.py  # 文本处理
│   ├── voice_settings.py  # 语音设置
│   ├── batch_processor.py # 批量处理
│   └── settings.py        # 系统设置
├── controllers/           # 控制层
│   ├── file_controller.py
│   ├── text_controller.py
│   ├── audio_controller.py
│   ├── batch_controller.py
│   └── settings_controller.py
├── services/              # 业务层
│   ├── file_service.py
│   ├── text_service.py
│   ├── audio_service.py
│   ├── tts_service.py
│   └── config_service.py
├── models/                # 数据层
│   ├── file_model.py
│   ├── text_model.py
│   ├── audio_model.py
│   └── config_model.py
├── processors/            # 文件处理器
│   ├── pdf_processor.py
│   ├── epub_processor.py
│   └── docx_processor.py
├── utils/                 # 工具类
│   ├── log_manager.py
│   ├── file_utils.py
│   ├── audio_utils.py
│   └── text_utils.py
├── resources/             # 资源文件
│   └── icons/            # 图标文件
└── docs/                 # 技术文档
    ├── README.md         # 文档索引
    ├── installation_guide.md      # 安装指南
    ├── piper_models_guide.md      # Piper模型下载指南
    ├── pyttsx3_voices_guide.md   # pyttsx3语音包指南
    └── tts_engines_comparison.md  # TTS引擎对比指南
```

## 技术文档

### 📚 详细文档
项目包含完整的技术文档，位于 `docs/` 目录：

- **[安装指南](docs/installation_guide.md)** - 详细的安装和配置说明
- **[Piper模型下载指南](docs/piper_models_guide.md)** - Piper TTS模型下载和配置
- **[pyttsx3语音包指南](docs/pyttsx3_voices_guide.md)** - pyttsx3语音包配置
- **[TTS引擎对比指南](docs/tts_engines_comparison.md)** - 各引擎对比和选择建议

### 🔧 配置说明
- **主配置文件**: `config.json` - 应用程序主配置
- **日志级别**: 通过 `advanced.log_level` 配置日志记录级别
- **引擎配置**: `configs/engines/` - TTS引擎配置
- **语音参数**: `configs/engine_parameters.json` - 引擎参数配置

## 开发说明

### 代码规范
- 遵循PEP 8 Python编码规范
- 使用类型提示增强代码可读性
- 完善的文档字符串和注释
- 模块化设计，职责分离


### 日志
- 日志文件保存在 `logs/` 目录
- 支持不同级别的日志记录
- 可通过配置文件调整日志级别

## 故障排除

### 常见问题

1. **TTS引擎不可用**
   - 检查网络连接（Edge TTS需要网络）
   - 确保pyttsx3正确安装
   - 查看日志文件获取详细错误信息

2. **文件格式不支持**
   - 确保安装了相应的依赖库
   - 检查文件是否损坏
   - 尝试其他文件格式

3. **音频生成失败**
   - 检查输出目录权限
   - 确保有足够的磁盘空间
   - 查看错误日志

4. **程序启动失败**
   - 检查Python版本（需要3.12+）
   - 确保所有依赖已正确安装
   - 检查配置文件格式

### 性能优化

1. **内存使用**
   - 调整最大并发任务数
   - 设置合适的内存限制
   - 及时清理临时文件

2. **处理速度**
   - 启用硬件加速（如果支持）
   - 调整文本分割长度
   - 选择合适的TTS引擎

## 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 更新日志

### v1.01 (2024-01-01)
- 初始版本发布
- 支持多种电子书格式
- 集成Edge TTS和pyttsx3引擎
- 实现批量处理功能
- 提供现代化用户界面

## 联系方式

如有问题或建议，请通过以下方式联系：

- 提交 Issue
- 发送邮件
- 项目讨论区

---

**注意**: 本项目仅供学习和研究使用，请遵守相关法律法规和版权规定。
