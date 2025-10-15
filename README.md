# E-book Audio Generation Tool
Generate audio from e-books to make it a pleasure to listen to novels. Convert e-book text to high-quality audio files.
A desktop application developed with Python + PyQt6 for converting e-book text to high-quality audio files.

**Language**: [English](README.md) | [中文](README_cn.md)

## Features

### Core Features
- **Multi-format Support**: Supports TXT, PDF, EPUB, DOCX and other e-book formats
- **Intelligent Text Processing**: Automatic text cleaning, chapter recognition, and intelligent segmentation
- **Multiple TTS Engines**: Supports Edge TTS and pyttsx3 speech synthesis engines
- **Voice Parameter Adjustment**: Supports speech rate, pitch, volume and other parameter adjustments
- **Batch Processing**: Supports multi-file batch conversion with queue management
- **Audio Formats**: Supports mainstream audio formats like MP3, WAV

### Interface Features
- **Modern UI**: Modern interface design based on PyQt6
- **Responsive Layout**: Supports window resizing
- **Theme Support**: Supports light/dark theme switching
- **Multi-language Support**: Interface language localization

## Technical Architecture

### Architecture Pattern
Adopts MVC (Model-View-Controller) architecture pattern combined with layered architecture design:

- **Presentation Layer (UI Layer)**: PyQt6 interface components
- **Controller Layer**: Business logic controllers
- **Service Layer**: Core business services
- **Data Layer (Model Layer)**: Data model definitions

### Technology Stack
- **Frontend Framework**: PyQt6
- **Programming Language**: Python 3.12
- **Text Processing**: PyPDF2, python-docx, ebooklib
- **Audio Processing**: pydub, ffmpeg-python
- **TTS Engines**: edge-tts, pyttsx3
- **Configuration Management**: configparser
- **Logging System**: logging

## Installation Instructions

### System Requirements
- Python 3.12+
- Windows 10/11 or Linux
- Memory: Minimum 4GB, recommended 8GB or more
- Storage: At least 1GB available space

### Installation Steps

1. **Clone the project**
```bash
git clone <repository-url>
cd play-ebook-tts-main
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Run the program**
```bash
python main.py
```

## Usage Instructions

### Basic Usage Workflow

1. **Import Files**
   - Click "Import Files" button or drag and drop files directly to the interface
   - Supported file formats: TXT, PDF, EPUB, DOCX

2. **Text Processing**
   - Preview and edit text in the "Text Processing" tab
   - Choose segmentation method: by length, by chapter, by paragraph
   - Adjust segmentation parameters

3. **Voice Settings**
   - Select TTS engine in the "Voice Settings" tab
   - Choose voice type and language
   - Adjust speech rate, pitch, volume parameters
   - Use "Test Voice" function to preview effects

4. **Generate Audio**
   - Click "Start Processing" button to begin audio generation
   - Manage processing queue in the "Batch Processing" tab
   - View processing progress and status

5. **Export Results**
   - Audio files will be saved to the specified output directory
   - Supports multiple audio format outputs

### Advanced Features

#### Batch Processing
- Add multiple files to processing queue
- Set different voice parameters
- Monitor processing progress and status
- Support pause, resume, stop operations

#### Configuration Management
- Save user preference settings
- Import/export configuration files
- Theme and language switching
- Performance parameter adjustment

## Project Structure

```
src/
├── main.py                 # Application entry point
├── requirements.txt        # Dependency package list
├── config.json            # Configuration file
├── README.md              # Project description
├── docs/                  # Technical documentation
│   ├── README.md          # Documentation index
│   ├── installation_guide.md      # Installation guide
│   ├── piper_models_guide.md      # Piper model download guide
│   ├── pyttsx3_voices_guide.md   # pyttsx3 voice package guide
│   └── tts_engines_comparison.md  # TTS engine comparison guide
├── ui/                    # Interface layer
│   ├── main_window.py     # Main window
│   ├── file_manager.py    # File management
│   ├── text_processor.py  # Text processing
│   ├── voice_settings.py  # Voice settings
│   ├── batch_processor.py # Batch processing
│   └── settings.py        # System settings
├── controllers/           # Controller layer
│   ├── file_controller.py
│   ├── text_controller.py
│   ├── audio_controller.py
│   ├── batch_controller.py
│   └── settings_controller.py
├── services/              # Service layer
│   ├── file_service.py
│   ├── text_service.py
│   ├── audio_service.py
│   ├── tts_service.py
│   └── config_service.py
├── models/                # Data layer
│   ├── file_model.py
│   ├── text_model.py
│   ├── audio_model.py
│   └── config_model.py
├── processors/            # File processors
│   ├── pdf_processor.py
│   ├── epub_processor.py
│   └── docx_processor.py
├── utils/                 # Utility classes
│   ├── log_manager.py
│   ├── file_utils.py
│   ├── audio_utils.py
│   └── text_utils.py
├── resources/             # Resource files
│   └── icons/            # Icon files
└── docs/                 # Technical documentation
    ├── README.md         # Documentation index
    ├── installation_guide.md      # Installation guide
    ├── piper_models_guide.md      # Piper model download guide
    ├── pyttsx3_voices_guide.md   # pyttsx3 voice package guide
    └── tts_engines_comparison.md  # TTS engine comparison guide
```

## Technical Documentation

### 📚 Detailed Documentation
The project includes complete technical documentation located in the `docs/` directory:

- **[Installation Guide](docs/installation_guide.md)** - Detailed installation and configuration instructions
- **[Piper Model Download Guide](docs/piper_models_guide.md)** - Piper TTS model download and configuration
- **[pyttsx3 Voice Package Guide](docs/pyttsx3_voices_guide.md)** - pyttsx3 voice package configuration
- **[TTS Engine Comparison Guide](docs/tts_engines_comparison.md)** - Engine comparison and selection recommendations

### 🔧 Configuration Description
- **Main Configuration File**: `config.json` - Application main configuration
- **Log Level**: Configure logging level through `advanced.log_level`
- **Engine Configuration**: `configs/engines/` - TTS engine configuration
- **Voice Parameters**: `configs/engine_parameters.json` - Engine parameter configuration

## Development Instructions

### Code Standards
- Follow PEP 8 Python coding standards
- Use type hints to enhance code readability
- Complete docstrings and comments
- Modular design with separation of concerns

### Logging
- Log files are saved in the `logs/` directory
- Supports different levels of logging
- Log level can be adjusted through configuration file

## Troubleshooting

### Common Issues

1. **TTS Engine Unavailable**
   - Check network connection (Edge TTS requires network)
   - Ensure pyttsx3 is properly installed
   - Check log files for detailed error information

2. **Unsupported File Format**
   - Ensure corresponding dependency libraries are installed
   - Check if the file is corrupted
   - Try other file formats

3. **Audio Generation Failed**
   - Check output directory permissions
   - Ensure sufficient disk space
   - Check error logs

4. **Application Startup Failed**
   - Check Python version (requires 3.12+)
   - Ensure all dependencies are properly installed
   - Check configuration file format

### Performance Optimization

1. **Memory Usage**
   - Adjust maximum concurrent task count
   - Set appropriate memory limits
   - Clean up temporary files promptly

2. **Processing Speed**
   - Enable hardware acceleration (if supported)
   - Adjust text segmentation length
   - Choose appropriate TTS engine

## Contributing Guidelines

1. Fork the project
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Changelog

### v1.01 (2024-01-01)
- Initial version release
- Support for multiple e-book formats
- Integration of Edge TTS and pyttsx3 engines
- Implementation of batch processing functionality
- Provision of modern user interface

## Contact

For questions or suggestions, please contact through:

- Submit an Issue
- Send an email
- Project discussion area

---

**Note**: This project is for learning and research purposes only. Please comply with relevant laws, regulations, and copyright requirements.
