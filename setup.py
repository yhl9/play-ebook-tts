#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安装脚本
"""

from setuptools import setup, find_packages
from pathlib import Path

# 读取README文件
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

# 读取requirements.txt
requirements = []
with open('requirements.txt', 'r', encoding='utf-8') as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name="playebook",
    version="1.0.0",
    author="AI开发团队",
    author_email="ai-dev@example.com",
    description="电子书生成音频工具",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ai-dev/playebook",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.12",
        "Topic :: Multimedia :: Sound/Audio :: Speech",
        "Topic :: Text Processing :: Markup",
    ],
    python_requires=">=3.12",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "playebook=main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["resources/icons/*.svg", "resources/themes/*.qss"],
    },
    keywords="ebook audio tts text-to-speech pyqt6",
    project_urls={
        "Bug Reports": "https://github.com/ai-dev/playebook/issues",
        "Source": "https://github.com/ai-dev/playebook",
        "Documentation": "https://github.com/ai-dev/playebook/wiki",
    },
)
