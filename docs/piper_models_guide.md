# Piper TTS 模型下载指南

## 概述

Piper TTS 是一个高质量的本地语音合成引擎，支持多种语言和语音模型。本指南将详细介绍如何下载、配置和使用 Piper 模型。

## 支持的语音模型

### 中文语音模型

| 模型名称 | 语言 | 性别 | 质量 | 文件大小 | 推荐用途 |
|---------|------|------|------|----------|----------|
| `zh_CN-huayan-medium` | 中文 | 女 | 中等 | ~50MB | 日常使用 |
| `zh_CN-huayan-high` | 中文 | 女 | 高 | ~100MB | 高质量需求 |
| `zh_CN-huayan-low` | 中文 | 女 | 低 | ~25MB | 快速测试 |

### 英文语音模型

| 模型名称 | 语言 | 性别 | 质量 | 文件大小 | 推荐用途 |
|---------|------|------|------|----------|----------|
| `en_GB-alan-medium` | 英式英语 | 男 | 中等 | ~50MB | 英式发音 |
| `en_GB-cori-medium` | 英式英语 | 女 | 中等 | ~50MB | 英式发音 |
| `en_US-lessac-medium` | 美式英语 | 男 | 中等 | ~50MB | 美式发音 |
| `en_US-lessac-high` | 美式英语 | 男 | 高 | ~100MB | 高质量美式发音 |

### 其他语言模型

| 语言 | 模型数量 | 主要模型 |
|------|----------|----------|
| 日语 | 3个 | `ja_JP-kokoro-medium` |
| 韩语 | 2个 | `ko_KR-kss-medium` |
| 法语 | 2个 | `fr_FR-siwis-medium` |
| 德语 | 2个 | `de_DE-thorsten-medium` |
| 西班牙语 | 2个 | `es_ES-sharvard-medium` |

## 下载方法

### 方法一：自动下载（推荐）

应用程序会自动检测缺失的模型并提供下载选项：

1. 启动应用程序
2. 选择 Piper TTS 引擎
3. 如果模型不存在，系统会提示下载
4. 点击"下载模型"按钮
5. 等待下载完成

### 方法二：手动下载

#### 1. 访问官方模型库

- **官方仓库**: https://huggingface.co/rhasspy/piper-voices
- **模型列表**: https://huggingface.co/rhasspy/piper-voices/tree/main

#### 2. 下载步骤

1. 访问模型页面
2. 选择所需的语音模型
3. 下载以下文件：
   - `MODEL_NAME.onnx` - 模型文件
   - `MODEL_NAME.onnx.json` - 配置文件
4. 将文件放置到 `models/piper/MODEL_NAME/` 目录

#### 3. 目录结构

```
models/
└── piper/
    ├── zh_CN-huayan-medium/
    │   ├── zh_CN-huayan-medium.onnx
    │   └── zh_CN-huayan-medium.onnx.json
    ├── en_GB-alan-medium/
    │   ├── en_GB-alan-medium.onnx
    │   └── en_GB-alan-medium.onnx.json
    └── ...
```

## 配置说明

### 模型配置文件

每个模型都包含一个 JSON 配置文件，示例：

```json
{
  "audio": {
    "sample_rate": 22050
  },
  "espeak": {
    "voice": "zh"
  },
  "inference": {
    "noise_scale": 0.667,
    "length_scale": 1.0,
    "noise_w": 0.8
  },
  "language": {
    "code": "zh"
  },
  "num_speakers": 1,
  "speaker_id": 0,
  "speaker_name_map": {
    "default": 0
  }
}
```

### 应用程序配置

在 `config.json` 中配置 Piper TTS：

```json
{
  "tts": {
    "default_engine": "piper_tts",
    "default_voice": "zh_CN-huayan-medium"
  },
  "piper": {
    "models_dir": "models/piper",
    "enable_caching": true,
    "max_cache_size": 10
  }
}
```

## 性能优化

### 1. 模型缓存

- **启用缓存**: 在配置中设置 `enable_caching: true`
- **缓存大小**: 设置 `max_cache_size` 限制内存使用
- **缓存位置**: 系统临时目录

### 2. 硬件加速

- **CPU优化**: 使用多线程处理
- **内存管理**: 限制并发模型加载数量
- **磁盘空间**: 确保有足够空间存储模型文件

### 3. 质量设置

| 参数 | 说明 | 推荐值 |
|------|------|--------|
| `noise_scale` | 音频变化程度 | 0.667 |
| `length_scale` | 语音长度缩放 | 1.0 |
| `noise_w` | 说话方式变化 | 0.8 |

## 故障排除

### 常见问题

#### 1. 模型下载失败

**症状**: 下载进度卡住或失败
**解决方案**:
- 检查网络连接
- 尝试使用 VPN
- 手动下载模型文件

#### 2. 模型加载失败

**症状**: 应用程序提示模型不可用
**解决方案**:
- 检查文件完整性
- 重新下载模型
- 检查文件权限

#### 3. 语音质量差

**症状**: 生成的语音质量不佳
**解决方案**:
- 使用高质量模型
- 调整音频参数
- 检查输入文本质量

### 日志调试

启用调试日志查看详细信息：

```json
{
  "advanced": {
    "log_level": "DEBUG"
  }
}
```

查看日志文件：
- `logs/app.log` - 应用程序日志
- `logs/error.log` - 错误日志

## 最佳实践

### 1. 模型选择

- **日常使用**: 选择 medium 质量模型
- **高质量需求**: 选择 high 质量模型
- **快速测试**: 选择 low 质量模型

### 2. 存储管理

- **定期清理**: 删除不使用的模型
- **备份重要模型**: 避免重复下载
- **监控磁盘空间**: 确保有足够存储空间

### 3. 性能调优

- **限制并发**: 避免同时加载过多模型
- **使用缓存**: 启用模型缓存提高性能
- **定期更新**: 检查模型更新

## 技术支持

如果遇到问题，请：

1. 查看日志文件获取详细错误信息
2. 检查网络连接和防火墙设置
3. 确认模型文件完整性
4. 联系技术支持团队

## 更新日志

- **v1.0.0**: 初始版本，支持基础模型下载
- **v1.1.0**: 添加自动下载功能
- **v1.2.0**: 支持多语言模型
- **v1.3.0**: 优化下载速度和错误处理

---

*最后更新: 2024年10月*
